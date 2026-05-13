# PhantomSense Installation Guide (Windows)

## Problem

The standard batch scripts (`start_all.bat`, `start_hub.bat`, `start_gui.bat`) were failing with:

```
ERROR: Unknown compiler(s): [['icl'], ['cl'], ['cc'], ['gcc'], ['clang'], ['clang-cl'], ['pgcc']]
```

**Cause:** NumPy was attempting to build from source, but no C/C++ compiler (MSVC) was found on the system.

## Solution

We've provided **installation scripts that work WITHOUT a C compiler**:

All three startup scripts now use pre-built wheels only:
- `quick_install.bat` - Initial setup (recommended for first-time install)
- `start_all.bat` - Start everything (hub + GUI)
- `start_hub.bat` - Hub server only
- `start_gui.bat` - GUI only

**All of these now use `--only-binary=:all:` to force pre-built packages - NO compiler needed!**

### Quick Start

```bash
# Option A: First time setup (install dependencies)
quick_install.bat

# Then start services:
start_all.bat

# OR Option B: Use start_all.bat directly (includes dependency install)
start_all.bat
```

### Alternative: Individual Services

```bash
# Terminal 1: Start Hub Server only
start_hub.bat

# Terminal 2: Start GUI only
start_gui.bat
```

---

### Option 1: ⭐ Quick Install or Start All (RECOMMENDED)

**No compiler required!** Both scripts automatically install pre-built wheels:

```bash
quick_install.bat  # OR just use start_all.bat
```

This script:
- ✅ Uses only pre-built Python wheels (no source compilation)
- ✅ Requires NO C/C++ compiler
- ✅ Takes 3-5 minutes
- ✅ Works on any Windows machine with Python 3.10+
- ✅ Forces numpy, matplotlib, PyQt6 from pre-built wheels with `--only-binary=:all:`

**Steps:**
1. Open Command Prompt or PowerShell
2. Navigate to: `c:\Users\johnj\OneDrive\Documents\VS_projects\PhantomSense`
3. Run: `quick_install.bat` OR `start_all.bat`
4. Wait for completion
5. Press any key to close

### Option 2: Install Microsoft Visual C++ Build Tools (Optional)

If you want full flexibility to build any package from source, install the C compiler:

**Windows 11/10:**
1. Download: https://visualstudio.microsoft.com/downloads/
2. Select "Visual Studio Build Tools"
3. Choose "Desktop development with C++"
4. Install (~4GB, 15-20 minutes)
5. Restart computer
6. All scripts will now work, including building packages from source

## Verifying Installation

After running `quick_install.bat`, verify the installation:

```bash
# Check virtual environment
.\hub\venv\Scripts\pip list

# Should show:
# PyQt6
# matplotlib
# fastapi
# numpy
# (and many others)
```

## Troubleshooting

### "Python not found"
- Ensure Python 3.10+ is installed
- Add Python to PATH: https://docs.python.org/3/using/windows.html
- Verify: `python --version`

### "Permission denied" / "Access is denied"
- Close all Python windows and terminals
- Run as Administrator if needed
- Delete `hub\venv` folder and run `quick_install.bat` again

### GUI won't start after installation
```bash
# Reinstall PyQt6
.\hub\venv\Scripts\pip install --only-binary=:all: PyQt6 --force-reinstall
```

### Hub port 5000 already in use
```bash
# Run these before starting hub
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

## Starting Services

After successful installation, use these commands:

```bash
# Terminal 1: Start Hub Server
.\start_hub.bat

# Terminal 2 (after Hub starts): Start GUI
.\start_gui.bat

# OR start everything at once
.\start_all.bat
```

## Accessing the System

| Component | URL | Purpose |
|-----------|-----|---------|
| Hub REST API | http://localhost:5000 | Device data, metrics |
| Device Status | http://localhost:5000/devices | List connected units |
| Metrics | http://localhost:5000/metrics | Aggregated CSI data |
| LLM Reasoning | http://localhost:5000/reasoning | Activity analysis |
| GUI App | Window on desktop | Real-time monitoring |

## File Structure After Installation

```
PhantomSense/
├── hub/
│   ├── venv/                    ← Virtual environment (created)
│   ├── requirements.txt
│   ├── phantomsense_hub/
│   ├── phantomsense_desktop.py
│   └── gui_config.json
├── start_all.bat                ← Start all services
├── start_hub.bat                ← Start hub only
├── start_gui.bat                ← Start GUI only
└── quick_install.bat            ← Install dependencies
```

## Support

**If `quick_install.bat` fails:**
1. Delete `hub\venv` folder
2. Run `quick_install.bat` again
3. Check internet connection
4. Try: `pip install --only-binary=:all: PyQt6`

**Most Common Issue:** Python not in PATH
- Solution: Reinstall Python and check "Add Python to PATH" during installation

---

**Last Updated:** May 13, 2026  
**Status:** Tested on Windows 10/11 with Python 3.10-3.14
