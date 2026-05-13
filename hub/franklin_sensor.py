#!/usr/bin/env python3
"""
PhantomSense – Franklin WiFi Sensor
=====================================
Captures WiFi signal metrics from Franklin's WiFi adapter and posts them
to the hub as Unit 3, running alongside the two ESP32 sensor units.

How it works:
  - Polls the connected AP's signal quality at 4 Hz via the Windows WLAN API
    (wlanapi.dll → WlanQueryInterface).  Falls back to 'netsh wlan show
    interfaces' parsing if the DLL approach fails.
  - Over each POST interval (default 5 s) it collects ~20 samples and computes:
      activity_score  – total variation of signal quality, normalised 0–100.
                        Higher variance = more motion / activity in the room.
      rssi            – estimated dBm from signal quality percentage.
      phase_velocity  – mean absolute rate-of-change of signal quality (quality%/s).
      amplitude_mean  – mean signal quality over the interval (0–100).
      noise_floor     – 10th-percentile quality value over the rolling window (dBm est).
  - POSTs the payload to the hub /update endpoint every POST_INTERVAL seconds.
    The hub treats Franklin as a normal PhantomSense unit and feeds its data
    into the LLM reasoning pipeline alongside the two ESP32 units.

Run:
    python franklin_sensor.py
    python franklin_sensor.py --hub http://192.168.1.10:5000 --interval 5 --unit-id 3

Requirements (already in hub venv): httpx
"""
from __future__ import annotations

import argparse
import asyncio
import ctypes
import ctypes.wintypes
import logging
import statistics
import subprocess
import time
from collections import deque
from typing import Optional

import httpx

# ─────────────────────────────── Configuration ────────────────────────────────
DEFAULT_HUB_URL       = "http://localhost:5000"
DEFAULT_POST_INTERVAL = 5.0    # seconds between hub POSTs
SAMPLE_INTERVAL_S     = 0.25   # poll WiFi at 4 Hz
ROLLING_WINDOW_S      = 30.0   # seconds of history kept for noise floor
UNIT_NAME             = "PhantomSense-Franklin-WiFi"
# ──────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - franklin_sensor - %(levelname)s - %(message)s",
)
log = logging.getLogger("franklin_sensor")


# ════════════════════════ Windows WLAN API (ctypes) ════════════════════════════

_WLAN_INTF_OPCODE_CURRENT_CONNECTION = 7   # wlan_intf_opcode_current_connection


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.wintypes.DWORD),
        ("Data2", ctypes.wintypes.WORD),
        ("Data3", ctypes.wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class _DOT11_SSID(ctypes.Structure):
    _fields_ = [
        ("uSSIDLength", ctypes.wintypes.ULONG),
        ("ucSSID",      ctypes.c_ubyte * 32),
    ]


class _WLAN_ASSOCIATION_ATTRIBUTES(ctypes.Structure):
    """Sub-structure inside WLAN_CONNECTION_ATTRIBUTES."""
    _fields_ = [
        ("dot11Ssid",         _DOT11_SSID),
        ("dot11BssType",      ctypes.c_int),           # DOT11_BSS_TYPE enum
        ("dot11Bssid",        ctypes.c_ubyte * 6),
        ("dot11PhyType",      ctypes.c_int),           # DOT11_PHY_TYPE enum
        ("uDot11PhyIndex",    ctypes.wintypes.ULONG),
        ("wlanSignalQuality", ctypes.wintypes.ULONG),  # 0–100 %
        ("ulRxRate",          ctypes.wintypes.ULONG),  # 500 Kbps units
        ("ulTxRate",          ctypes.wintypes.ULONG),  # 500 Kbps units
    ]


class _WLAN_SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("bSecurityEnabled",     ctypes.wintypes.BOOL),
        ("bOneXEnabled",         ctypes.wintypes.BOOL),
        ("dot11AuthAlgorithm",   ctypes.c_int),
        ("dot11CipherAlgorithm", ctypes.c_int),
    ]


class _WLAN_CONNECTION_ATTRIBUTES(ctypes.Structure):
    """Returned by WlanQueryInterface(wlan_intf_opcode_current_connection)."""
    _fields_ = [
        ("isState",                   ctypes.c_int),         # WLAN_INTERFACE_STATE
        ("wlanConnectionMode",        ctypes.c_int),         # WLAN_CONNECTION_MODE
        ("strProfileName",            ctypes.c_wchar * 256),
        ("wlanAssociationAttributes", _WLAN_ASSOCIATION_ATTRIBUTES),
        ("wlanSecurityAttributes",    _WLAN_SECURITY_ATTRIBUTES),
    ]


class _WLAN_INTERFACE_INFO(ctypes.Structure):
    _fields_ = [
        ("InterfaceGuid",           _GUID),
        ("strInterfaceDescription", ctypes.c_wchar * 256),
        ("isState",                 ctypes.c_int),
    ]


class WifiMonitor:
    """
    Polls Windows WLAN API for signal quality of the connected AP.

    Primary path  : wlanapi.dll → WlanQueryInterface (sub-millisecond)
    Fallback path : subprocess 'netsh wlan show interfaces' (~100 ms per call)
    """

    def __init__(self) -> None:
        self._api    = None
        self._handle = None
        self._guid_bytes: Optional[bytes] = None
        self._use_dll = True

        try:
            self._init_dll()
            log.info("WLAN API initialised via wlanapi.dll")
        except Exception as exc:
            log.warning(f"wlanapi.dll init failed ({exc}) – falling back to netsh")
            self._use_dll = False

    # ─── DLL initialisation ──────────────────────────────────────────────────

    def _init_dll(self) -> None:
        api = ctypes.WinDLL("wlanapi")

        version = ctypes.wintypes.DWORD()
        handle  = ctypes.wintypes.HANDLE()
        rc = api.WlanOpenHandle(2, None, ctypes.byref(version), ctypes.byref(handle))
        if rc != 0:
            raise OSError(f"WlanOpenHandle returned {rc}")

        self._api    = api
        self._handle = handle

        # Enumerate interfaces to find the first wireless interface GUID
        iface_ptr = ctypes.c_void_p()
        rc = api.WlanEnumInterfaces(handle, None, ctypes.byref(iface_ptr))
        if rc != 0:
            raise OSError(f"WlanEnumInterfaces returned {rc}")

        try:
            addr = iface_ptr.value
            if addr is None:
                raise RuntimeError("WlanEnumInterfaces returned null pointer")

            # WLAN_INTERFACE_INFO_LIST layout: DWORD count + DWORD index + entries
            count = ctypes.cast(addr, ctypes.POINTER(ctypes.wintypes.DWORD)).contents.value
            if count == 0:
                raise RuntimeError("No wireless interfaces found")

            # First WLAN_INTERFACE_INFO starts at byte offset 8 (2 × DWORD)
            first_info = ctypes.cast(addr + 8, ctypes.POINTER(_WLAN_INTERFACE_INFO)).contents
            self._guid_bytes = bytes(
                ctypes.string_at(ctypes.addressof(first_info.InterfaceGuid), 16)
            )
            desc = first_info.strInterfaceDescription
            log.info(f"Using wireless interface: {desc}")
        finally:
            api.WlanFreeMemory(ctypes.c_void_p(addr))

    # ─── Polling helpers ─────────────────────────────────────────────────────

    def _poll_dll(self) -> tuple[int, int, int]:
        """Returns (signal_quality_pct 0–100, rx_mbps, tx_mbps)."""
        guid = _GUID()
        ctypes.memmove(ctypes.byref(guid), self._guid_bytes, 16)

        data_size  = ctypes.wintypes.DWORD()
        data_ptr   = ctypes.c_void_p()
        opcode_vt  = ctypes.c_int()

        rc = self._api.WlanQueryInterface(
            self._handle,
            ctypes.byref(guid),
            _WLAN_INTF_OPCODE_CURRENT_CONNECTION,
            None,
            ctypes.byref(data_size),
            ctypes.byref(data_ptr),
            ctypes.byref(opcode_vt),
        )
        if rc != 0:
            raise OSError(f"WlanQueryInterface returned {rc}")

        addr = data_ptr.value
        try:
            conn  = ctypes.cast(addr, ctypes.POINTER(_WLAN_CONNECTION_ATTRIBUTES)).contents
            assoc = conn.wlanAssociationAttributes
            quality = int(assoc.wlanSignalQuality)           # 0–100
            rx_mbps = int(assoc.ulRxRate) // 1000          # Kbps → Mbps
            tx_mbps = int(assoc.ulTxRate) // 1000
        finally:
            self._api.WlanFreeMemory(ctypes.c_void_p(addr))

        return quality, rx_mbps, tx_mbps

    @staticmethod
    def _poll_netsh() -> tuple[int, int, int]:
        """Parse 'netsh wlan show interfaces' for signal/rate fields."""
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True, text=True, timeout=5,
            )
        except subprocess.TimeoutExpired:
            return 0, 0, 0

        quality, rx, tx = 0, 0, 0
        for line in result.stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith("Signal"):
                try:
                    quality = int(stripped.split(":", 1)[1].strip().rstrip("%"))
                except (ValueError, IndexError):
                    pass
            elif stripped.startswith("Receive rate"):
                try:
                    rx = int(float(stripped.split(":", 1)[1].strip()))
                except (ValueError, IndexError):
                    pass
            elif stripped.startswith("Transmit rate"):
                try:
                    tx = int(float(stripped.split(":", 1)[1].strip()))
                except (ValueError, IndexError):
                    pass
        return quality, rx, tx

    # ─── Public API ──────────────────────────────────────────────────────────

    def poll(self) -> tuple[int, int, int]:
        """Return (signal_quality_pct 0–100, rx_mbps, tx_mbps)."""
        if self._use_dll:
            try:
                return self._poll_dll()
            except Exception as exc:
                log.debug(f"DLL poll failed ({exc}), using netsh this cycle")
        return self._poll_netsh()

    def close(self) -> None:
        if self._handle and self._use_dll and self._api:
            self._api.WlanCloseHandle(self._handle, None)
            self._handle = None


# ═══════════════════════════ Signal Processing ═════════════════════════════════

def quality_to_rssi(quality: float) -> int:
    """
    Convert Windows signal-quality % to estimated RSSI dBm.
    Windows formula: quality = 2 * (rssi + 100), clamped 0–100.
    Inverse: rssi = quality/2 - 100.
    """
    return int(quality / 2.0 - 100)


def compute_metrics(samples: list[tuple[float, int, int, int]]) -> dict:
    """
    Build a hub-compatible payload from a list of polling samples.

    samples: [(timestamp_s, signal_quality_pct, rx_mbps, tx_mbps), ...]

    The hub's /update handler computes:
        snr            = csi_amplitude - csi_noise_floor
        activity_score = min(100, max(0, int(snr)))

    So we encode our own activity_score directly:
        csi_amplitude  = activity_score  (0–100)
        csi_noise_floor = 0.0
    This gives activity_score == snr as stored in the activity buffer.
    """
    if not samples:
        return {}

    qualities  = [s[1] for s in samples]
    rx_rates   = [s[2] for s in samples]
    n          = len(qualities)

    mean_q      = statistics.mean(qualities)
    rssi_now    = quality_to_rssi(qualities[-1])

    # ── Noise floor: 10th-percentile quality over the rolling window ──
    sorted_q    = sorted(qualities)
    p10_idx     = max(0, n // 10)
    noise_q     = sorted_q[p10_idx]
    noise_floor = float(quality_to_rssi(noise_q))   # negative dBm

    # ── Phase velocity: mean absolute rate-of-change (quality-units/sec) ──
    if n > 1:
        diffs = [abs(qualities[i] - qualities[i - 1]) for i in range(1, n)]
        phase_velocity = round(statistics.mean(diffs) / SAMPLE_INTERVAL_S, 4)
    else:
        phase_velocity = 0.0

    # ── Activity score: total variation of quality, normalised 0–100 ──
    # Total variation sums all consecutive differences; each 1%-point change
    # in signal quality counts toward the score.  Empirically:
    #   still environment : TV ≈  0–5  over 20 samples → score  0–20
    #   mild motion       : TV ≈  5–15                 → score 20–60
    #   active movement   : TV ≈ 15+                   → score 60–100
    if n > 1:
        total_variation = sum(abs(qualities[i] - qualities[i - 1]) for i in range(1, n))
        activity_score  = min(100, int(total_variation * 4))
    else:
        activity_score = 0

    log.info(
        f"WiFi stats | quality={mean_q:.1f}%  rssi={rssi_now} dBm  "
        f"TV={total_variation if n > 1 else 0:.1f}  "
        f"activity_score={activity_score}  rx={max(rx_rates) if rx_rates else 0} Mbps"
    )

    return {
        "unit_name":       UNIT_NAME,
        "rssi":            rssi_now,
        "ip_address":      "127.0.0.1",
        # csi_amplitude = mean signal quality % (0-100) — graphable/displayable.
        # csi_noise_floor = quality - activity_score so the hub formula
        # snr = amplitude - noise_floor yields snr == activity_score exactly,
        # feeding the correct motion score into the LLM pipeline.
        "csi_amplitude":   float(mean_q),
        "csi_noise_floor": float(mean_q - activity_score),
        "timestamp_ms":    int(time.time() * 1000),
    }


# ════════════════════════════ Async main loop ══════════════════════════════════

async def sensor_loop(hub_url: str, unit_id: int, post_interval: float) -> None:
    """
    Main loop: polls WiFi at 4 Hz, POSTs metrics to hub every post_interval seconds.
    """
    monitor = WifiMonitor()
    rolling_window = int(ROLLING_WINDOW_S / SAMPLE_INTERVAL_S)
    buffer: deque[tuple[float, int, int, int]] = deque(maxlen=rolling_window)

    update_url = f"{hub_url.rstrip('/')}/update"
    next_post  = time.monotonic() + post_interval

    log.info(f"Franklin WiFi sensor starting – unit_id={unit_id}, hub={hub_url}")

    async with httpx.AsyncClient(timeout=10.0) as client:
        while True:
            loop_start = time.monotonic()

            # ── Sample ──────────────────────────────────────────────────────
            try:
                quality, rx_mbps, tx_mbps = await asyncio.to_thread(monitor.poll)
                if quality > 0:
                    # Only buffer valid readings; quality=0 means the interface
                    # is not associated (WlanQueryInterface error 5023 / netsh
                    # returns nothing) — don't pollute the buffer with zeros.
                    buffer.append((time.time(), quality, rx_mbps, tx_mbps))
                else:
                    log.debug("Skipping zero-quality sample (interface not associated)")
            except Exception as exc:
                log.warning(f"WiFi poll error: {exc}")

            # ── POST to hub ─────────────────────────────────────────────────
            if time.monotonic() >= next_post:
                # Only post if we have at least one valid (non-zero) sample
                valid_samples = [s for s in buffer if s[1] > 0]
                if valid_samples:
                    payload = compute_metrics(valid_samples)
                    payload["unit_id"] = unit_id

                    try:
                        resp = await client.post(update_url, json=payload)
                        if resp.status_code == 200:
                            log.debug(f"POST /update → {resp.status_code}")
                        else:
                            log.warning(f"POST /update returned {resp.status_code}: {resp.text[:120]}")
                    except httpx.ConnectError:
                        log.warning(f"Cannot reach hub at {hub_url} – will retry")
                    except Exception as exc:
                        log.error(f"POST failed: {exc}")
                else:
                    log.warning("No valid WiFi samples this interval – skipping POST (interface not associated?)")

                next_post += post_interval

            # ── Sleep until next sample ──────────────────────────────────────
            elapsed = time.monotonic() - loop_start
            sleep_s = max(0.0, SAMPLE_INTERVAL_S - elapsed)
            await asyncio.sleep(sleep_s)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PhantomSense Franklin WiFi Sensor – posts WiFi signal metrics to the hub."
    )
    parser.add_argument(
        "--hub",
        default=DEFAULT_HUB_URL,
        help=f"Hub base URL (default: {DEFAULT_HUB_URL})",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_POST_INTERVAL,
        help=f"Seconds between POSTs (default: {DEFAULT_POST_INTERVAL})",
    )
    parser.add_argument(
        "--unit-id",
        type=int,
        default=3,
        help="Unit ID reported to the hub (default: 3)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable DEBUG logging",
    )
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        asyncio.run(sensor_loop(args.hub, args.unit_id, args.interval))
    except KeyboardInterrupt:
        log.info("Franklin WiFi sensor stopped.")


if __name__ == "__main__":
    main()
