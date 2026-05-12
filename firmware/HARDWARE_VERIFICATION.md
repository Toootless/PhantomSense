# Hardware Verification - Waveshare ESP32-S3-LCD-1.47

**Date Verified:** May 11, 2026  
**Source:** Waveshare Technical Schematics  
**Status:** ✅ CONFIRMED - GPIO pins identified

## Problem Summary

Previous GPIO testing (pins 46–48 for RGB, GPIO 33 for backlight) failed because those pins are **not wired to the display/LED** on this specific board. They are tied to internal PSRAM or JTAG.

## Confirmed GPIO Pinout

### RGB LED (WS2812B)

```
Component: WS2812B Addressable RGB LED
Location: Tiny white square near USB-C port
Data Pin: GPIO 38
Protocol: RMT (Recommended) or Bitbang
Type: NOT a standard LED - requires data protocol, not just HIGH/LOW
```

⚠️ **CRITICAL:** The RGB LED is NOT a simple GPIO output. It's a **WS2812B addressable LED** that requires:
- RMT peripheral for timing-critical PWM signal
- Color data sent via serial protocol
- Cannot use simple `gpio_set_level()` commands

### LCD Display (ST7789 over SPI)

```
Screen: 1.47" ST7789 (172×320 pixels)
Driver: SPI

LCD_BACKLIGHT (BL):   GPIO 15  ← MUST be HIGH to see anything
LCD_RESET (RES):      GPIO 13
LCD_DC (Data/Command): GPIO 14
LCD_CS (Chip Select):  GPIO 12
SPI_MOSI:             GPIO 11
SPI_CLK:              GPIO 10
SPI_MISO:             Not used (write-only display)
```

**The Backlight Issue:**
- **If LCD is black:** GPIO 15 not set to HIGH
- **If LCD is white:** Backlight is ON but no image data sent
- **Initialize order:** Reset → DC setup → SPI init → Backlight ON

## Immediate "Wake Up" Test

This minimal code proves the hardware is alive:

```c
#include "driver/gpio.h"
#include "esp_log.h"
#include "esp_psram.h"

#define LCD_BACKLIGHT_PIN 15

void app_main(void) {
    // 1. Force Backlight ON
    gpio_reset_pin(LCD_BACKLIGHT_PIN);
    gpio_set_direction(LCD_BACKLIGHT_PIN, GPIO_MODE_OUTPUT);
    gpio_set_level(LCD_BACKLIGHT_PIN, 1); 
    
    ESP_LOGI("PHANTOM", "Backlight should be ON now.");

    // 2. Verify Octal PSRAM
    size_t psram = esp_psram_get_size();
    ESP_LOGI("PHANTOM", "PSRAM detected: %d bytes", psram);

    if (psram < 8000000) {
        ESP_LOGE("PHANTOM", "PSRAM mismatch! Check Octal Mode in menuconfig.");
    }

    // Keep running
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}
```

**Expected Output on Serial Monitor:**
```
I (123) PHANTOM: Backlight should be ON now.
I (123) PHANTOM: PSRAM detected: 8388608 bytes
```

**Physical Check:**
- ✅ LCD display should light up (white screen, no content)
- ✅ Backlight brightness visible
- ✅ PSRAM shows 8388608 (8MB)

## Why Previous Tests Failed

| Assumption | Reality | Result |
|-----------|---------|--------|
| GPIO 46 = Red LED | Tied to PSRAM | No effect |
| GPIO 47 = Green LED | Tied to PSRAM | No effect |
| GPIO 48 = Blue LED | Tied to PSRAM | No effect |
| GPIO 33 = Backlight | Not connected | No effect |
| Simple `gpio_set_level()` | WS2812B protocol required | LED won't work |

## Tomorrow's Implementation Plan

### Phase 1: Verify Hardware is Alive ✅
- [ ] Flash "Wake Up" test code
- [ ] Confirm LCD backlight turns on
- [ ] Confirm PSRAM detection (should show 8MB)
- [ ] Monitor serial output

### Phase 2: Implement WS2812B Driver
- [ ] Add RMT peripheral setup (or Bitbang alternative)
- [ ] Configure GPIO 38 for data output
- [ ] Create color functions (red, green, blue, etc.)
- [ ] Test individual color output

### Phase 3: Update Display Driver
- [ ] Fix GPIO pin definitions in `display_driver.c`
- [ ] Replace LEDC PWM with RMT protocol
- [ ] Update LCD SPI pins (10, 11, 12, 14, 13, 15)
- [ ] Test full LED status sequence

### Phase 4: Integration Testing
- [ ] Device status indicator (CONNECTING=yellow, CONNECTED=green, etc.)
- [ ] LCD display on (white background ready for content)
- [ ] Hub communication verification

## Hardware Health Checks

**Power Draw Check:**
The ESP32-S3 with LCD + RGB can spike power during initialization.
- ✅ Use dedicated USB power supply (not hub)
- ✅ If LED doesn't glow: check USB power current (>500mA needed)

**Physical Component Location:**
- **WS2812B RGB LED:** Tiny white square near USB-C port
- **ST7789 IC:** Near the LCD connector (black rectangular component)
- **PSRAM:** Chip labeled "OPI PSRAM" or similar (8MB variant)

## Code Snippets for Tomorrow

### Basic RMT Setup for WS2812B

```c
// Configuration for RMT peripheral
#include "driver/rmt_tx.h"

#define WS2812B_GPIO 38
#define RMT_LED_RESOLUTION_HZ 10000000  // 10MHz

rmt_tx_channel_handle_t led_channel = NULL;

void init_ws2812b_led(void) {
    rmt_tx_channel_config_t channel_config = {
        .clk_src = RMT_CLK_SRC_DEFAULT,
        .resolution_hz = RMT_LED_RESOLUTION_HZ,
        .mem_block_symbols = 64,
        .trans_queue_depth = 10,
        .gpio_num = WS2812B_GPIO,
    };
    ESP_ERROR_CHECK(rmt_new_tx_channel(&channel_config, &led_channel));
    ESP_ERROR_CHECK(rmt_enable(led_channel));
}
```

### Basic LCD Backlight Control

```c
#include "driver/gpio.h"

#define LCD_BACKLIGHT 15
#define LCD_RESET 13

void init_lcd_display(void) {
    // Configure backlight
    gpio_reset_pin(LCD_BACKLIGHT);
    gpio_set_direction(LCD_BACKLIGHT, GPIO_MODE_OUTPUT);
    
    // Configure reset
    gpio_reset_pin(LCD_RESET);
    gpio_set_direction(LCD_RESET, GPIO_MODE_OUTPUT);
    
    // Power cycle sequence
    gpio_set_level(LCD_RESET, 0);
    vTaskDelay(pdMS_TO_TICKS(10));
    gpio_set_level(LCD_RESET, 1);
    vTaskDelay(pdMS_TO_TICKS(100));
    
    // Turn on backlight
    gpio_set_level(LCD_BACKLIGHT, 1);
}
```

## References

- **Waveshare Wiki:** https://www.waveshare.com/wiki/ESP32-S3-LCD-1.47
- **WS2812B Protocol:** https://cdn-shop.adafruit.com/datasheets/WS2812B.pdf
- **ESP-IDF RMT Documentation:** https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-reference/peripherals/rmt.html
- **ST7789 Datasheet:** Available from Waveshare support

## Files to Update

Once verified:
1. `components/display_driver/display_driver.c` - Update GPIO definitions
2. `components/display_driver/include/display_driver.h` - Update pin macros
3. `main/app_config.h` - Document correct pin layout
4. `README.md` - Update hardware specifications section

## Next Session Checklist

- [ ] Load this document
- [ ] Use "Wake Up" test code above
- [ ] Verify LCD backlight + PSRAM
- [ ] Begin WS2812B RMT implementation
- [ ] Update display_driver.c with correct pins
