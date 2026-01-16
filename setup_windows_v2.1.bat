@echo off
REM ==============================================================================
REM MultiConverter v2.1.0 - Windows Setup Script
REM ==============================================================================
REM This script sets up everything needed to build the Windows executable
REM Includes USD library setup for multi-format export
REM ==============================================================================

echo ====================================
echo MultiConverter v2.1.0 - Windows Setup
echo ====================================
echo.

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo.
    echo Please install Python 3.11 or 3.12 from:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Checking Python version...
python --version

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%

REM Extract major.minor version (e.g., 3.11)
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PY_MAJOR=%%a
    set PY_MINOR=%%b
)

echo Python %PY_MAJOR%.%PY_MINOR% detected

REM Check if version is 3.11, 3.12, or newer
if "%PY_MINOR%"=="11" (
    set CP_TAG=cp311
    echo ✓ Python 3.11 - Compatible
    goto :version_ok
) else if "%PY_MINOR%"=="12" (
    set CP_TAG=cp312
    echo ✓ Python 3.12 - Compatible
    goto :version_ok
) else if "%PY_MINOR%"=="13" (
    set CP_TAG=cp312
    echo.
    echo ⚠ WARNING: Python 3.13 detected
    echo   Using Python 3.12 wheel - may work but not guaranteed
    echo   For best results, install Python 3.12
    echo.
    timeout /t 3 /nobreak >nul
    goto :version_ok
) else (
    echo.
    echo ERROR: Python 3.11 or 3.12 required for best compatibility
    echo You have Python %PY_MAJOR%.%PY_MINOR%
    echo.
    echo Please install Python 3.12 from:
    echo https://www.python.org/downloads/release/python-3120/
    echo.
    pause
    exit /b 1
)

:version_ok
REM Create virtual environment
if not exist "venv" (
    echo.
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install basic dependencies
echo.
echo Installing basic dependencies...
pip install numpy pyinstaller sv_ttk

REM Download and install PyAlembic wheel
echo.
echo ====================================
echo Installing PyAlembic
echo ====================================
echo.
echo PyAlembic wheel will be downloaded from:
echo https://github.com/cgohlke/pyalembic-wheels/releases
echo.

set PYALEMBIC_VERSION=1.8.10
set RELEASE_TAG=v2025.11.28

REM Detect architecture
if "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
    set PLATFORM=win_amd64
) else if "%PROCESSOR_ARCHITECTURE%"=="ARM64" (
    set PLATFORM=win_arm64
) else (
    set PLATFORM=win32
)

set WHEEL_NAME=pyalembic-%PYALEMBIC_VERSION%-%CP_TAG%-%CP_TAG%-%PLATFORM%.whl
set WHEEL_URL=https://github.com/cgohlke/pyalembic-wheels/releases/download/%RELEASE_TAG%/%WHEEL_NAME%

echo Downloading: %WHEEL_NAME%
echo.

REM Check if wheel already exists
if exist "%WHEEL_NAME%" (
    echo ✓ Wheel already downloaded
) else (
    echo Downloading PyAlembic wheel...
    powershell -Command "& {Invoke-WebRequest -Uri '%WHEEL_URL%' -OutFile '%WHEEL_NAME%'}"
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to download PyAlembic wheel
        echo.
        echo Please manually download from:
        echo %WHEEL_URL%
        echo.
        echo Save it to this directory: %CD%
        pause
        exit /b 1
    )
    echo ✓ Download complete
)

REM Install the wheel
echo.
echo Installing PyAlembic wheel...
pip install "%WHEEL_NAME%"
if errorlevel 1 (
    echo ERROR: Failed to install PyAlembic
    pause
    exit /b 1
)

echo ✓ PyAlembic installed successfully

REM Verify PyAlembic installation
echo.
echo Verifying PyAlembic installation...
python -c "import alembic; import alembic.Abc; print('✓ PyAlembic import successful')"
if errorlevel 1 (
    echo.
    echo WARNING: PyAlembic import failed
    echo This may be due to missing Visual C++ Redistributable
    echo.
    echo Please install:
    echo Microsoft Visual C++ Redistributable for Visual Studio 2015-2022
    echo https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo.
    pause
)

REM USD Library Installation (NEW in v2.1.0)
echo.
echo ====================================
echo Installing USD Library (Optional)
echo ====================================
echo.
echo USD library enables multi-format export (USD, Maya)
echo If USD is not available, AE export will still work
echo.
echo Would you like to install USD? (Y/N)
set /p INSTALL_USD="Install USD? (Y/N): "

if /i "%INSTALL_USD%"=="Y" (
    echo.
    echo USD installation options for Windows:
    echo.
    echo Option 1: NVIDIA Pre-built Binaries (RECOMMENDED)
    echo   Download from: https://developer.nvidia.com/usd
    echo   - Select "USD for Python %PY_MAJOR%.%PY_MINOR%"
    echo   - Extract to a folder
    echo   - Add to PYTHONPATH or copy to venv\Lib\site-packages
    echo.
    echo Option 2: Build from Source
    echo   Requires Visual Studio and CMake
    echo   https://github.com/PixarAnimationStudios/OpenUSD
    echo.
    echo Option 3: Try pip install (may not work on all systems)
    echo   pip install usd-core
    echo.
    set /p USD_METHOD="Choose option (1/2/3): "

    if "%USD_METHOD%"=="3" (
        echo.
        echo Attempting pip install...
        pip install usd-core
        if errorlevel 1 (
            echo.
            echo pip install failed. Please use Option 1 or 2.
            echo You can still build the executable - USD export just won't be available
            echo.
        ) else (
            echo ✓ USD installed via pip
        )
    ) else (
        echo.
        echo Please follow the instructions above to install USD manually
        echo After installation, verify with: python -c "from pxr import Usd"
        echo.
    )
) else (
    echo.
    echo Skipping USD installation
    echo Note: USD and Maya export will not be available
    echo You can install USD later if needed
    echo.
)

echo.
echo ====================================
echo Setup Complete!
echo ====================================
echo.
echo Next steps:
echo   1. Test the GUI: python a2j_gui.py
echo   2. Build executable: build_windows_v2.1.bat
echo.
echo Installed components:
echo   ✓ Python virtual environment
echo   ✓ PyAlembic %PYALEMBIC_VERSION%
echo   ✓ NumPy
echo   ✓ PyInstaller

if /i "%INSTALL_USD%"=="Y" (
    echo   ✓ USD library
)

echo.
echo The PyAlembic wheel has been downloaded to:
echo   %CD%\%WHEEL_NAME%
echo.
pause
