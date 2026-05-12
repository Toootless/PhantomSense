#!/usr/bin/env python3
"""
PhantomSense Desktop Application Launcher
Installs dependencies and launches the data visualization app
"""

import subprocess
import sys
import importlib.util


def check_and_install_package(package_name, import_name=None):
    """Check if package is installed, install if not"""
    if import_name is None:
        import_name = package_name.replace("-", "_")
    
    spec = importlib.util.find_spec(import_name)
    if spec is None:
        print(f"Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", package_name])
        print(f"✓ {package_name} installed")
    else:
        print(f"✓ {package_name} already installed")


def main():
    print("=" * 60)
    print("PhantomSense Desktop App Launcher")
    print("=" * 60)
    
    # Check required packages
    packages = [
        ("PyQt6", "PyQt6"),
        ("requests", "requests"),
    ]
    
    print("\nChecking dependencies...")
    for package, import_name in packages:
        check_and_install_package(package, import_name)
    
    print("\n" + "=" * 60)
    print("Launching PhantomSense Desktop Application...")
    print("=" * 60 + "\n")
    
    # Import and run the app
    from phantomsense_desktop import main as app_main
    app_main()


if __name__ == "__main__":
    main()
