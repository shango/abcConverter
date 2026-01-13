@echo off
REM ==============================================================================
REM abcConverter v2.1.0 - Windows Build Script (--onedir mode for USD)
REM Creates a directory with executable and dependencies
REM ==============================================================================

echo ====================================
echo Building abcConverter v2.1.0
echo ====================================
echo.

REM Check if venv exists
if not exist "venv" (
    echo ERROR: Virtual environment not found!
    echo Please run setup_windows_v2.1.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if PyInstaller is installed
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller
)

REM Try to run pyinstaller - if not found, use python -m PyInstaller
where pyinstaller >nul 2>&1
if errorlevel 1 (
    echo.
    echo Note: Using 'python -m PyInstaller' instead of 'pyinstaller' command
    set PYINSTALLER_CMD=python -m PyInstaller
) else (
    set PYINSTALLER_CMD=pyinstaller
)

REM Check for USD library
echo.
echo Checking for USD library...
python -c "from pxr import Usd" >nul 2>&1
if errorlevel 1 (
    echo ⚠ WARNING: USD library not found
    echo   USD and Maya export will not be available in the executable
    echo   To add USD support, run setup_windows_v2.1.bat and install USD
    echo.
    set USD_AVAILABLE=NO
) else (
    echo ✓ USD library found - Multi-format export enabled
    set USD_AVAILABLE=YES
)

timeout /t 2 /nobreak >nul

REM Clean previous builds
if exist "build" (
    echo Cleaning previous build...
    rmdir /s /q build
)
if exist "dist" (
    rmdir /s /q dist
)
if exist "abcConverter.spec" (
    del abcConverter.spec
)

echo.
echo ====================================
echo Running PyInstaller (--onedir mode)
echo ====================================
echo This creates a directory with the
echo executable and all dependencies
echo ====================================
echo.

REM Build the executable with v2.1.0 modular architecture
REM Using --onedir instead of --onefile for better USD DLL support
%PYINSTALLER_CMD% ^
    --name=abcConverter ^
    --onedir ^
    --windowed ^
    --clean ^
    --noconfirm ^
    --hidden-import=alembic_converter ^
    --hidden-import=core.alembic_reader ^
    --hidden-import=core.animation_detector ^
    --hidden-import=exporters.base_exporter ^
    --hidden-import=exporters.ae_exporter ^
    --hidden-import=exporters.usd_exporter ^
    --hidden-import=alembic ^
    --hidden-import=alembic.Abc ^
    --hidden-import=alembic.AbcGeom ^
    --hidden-import=alembic.AbcCoreAbstract ^
    --hidden-import=imath ^
    --hidden-import=imathnumpy ^
    --hidden-import=numpy ^
    --hidden-import=tkinter ^
    --hidden-import=pxr ^
    --hidden-import=pxr.Usd ^
    --hidden-import=pxr.UsdGeom ^
    --hidden-import=pxr.Gf ^
    --hidden-import=pxr.Vt ^
    --hidden-import=pxr.Sdf ^
    --hidden-import=pxr.Tf ^
    --collect-all=alembic ^
    --collect-all=imath ^
    --collect-binaries=pxr ^
    --collect-data=pxr ^
    --add-data="README.md;." ^
    a2j_gui.py

if errorlevel 1 (
    echo.
    echo ====================================
    echo Build Failed!
    echo ====================================
    echo.
    echo Common issues:
    echo   - Missing dependencies: Run setup_windows_v2.1.bat
    echo   - Import errors: Check that all modules are in place
    echo.
    pause
    exit /b 1
)

echo.
echo ====================================
echo Build Complete!
echo ====================================
echo.
echo Executable location: dist\abcConverter\abcConverter.exe
echo.

REM Show directory size
if exist "dist\abcConverter" (
    echo Distribution folder contents:
    dir dist\abcConverter
    echo.
)

echo Features included:
echo   ✓ After Effects JSX + OBJ export
if "%USD_AVAILABLE%"=="YES" (
    echo   ✓ USD .usdc export
    echo   ✓ Maya USD export
) else (
    echo   ✗ USD export (library not found)
    echo   ✗ Maya export (library not found)
)

echo.
echo Distribution notes:
echo   - Distribute: entire dist\abcConverter\ folder
echo   - Run: dist\abcConverter\abcConverter.exe
echo   - Users need: Microsoft Visual C++ Redistributable 2015-2022
echo     Download: https://aka.ms/vs/17/release/vc_redist.x64.exe
echo.

if "%USD_AVAILABLE%"=="NO" (
    echo.
    echo To enable USD/Maya export in future builds:
    echo   1. Install USD library (see setup_windows_v2.1.bat)
    echo   2. Rebuild with this script
    echo.
)

pause
