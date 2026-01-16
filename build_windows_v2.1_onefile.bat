@echo off
REM ==============================================================================
REM MultiConverter v2.5.0 - Windows Build Script (--onefile mode)
REM Creates a single standalone .exe file
REM NOTE: --onefile may have issues with USD DLLs - use --onedir if problems occur
REM ==============================================================================

echo ====================================
echo Building MultiConverter v2.5.0
echo (Single File Mode)
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
    echo WARNING: USD library not found
    echo   USD and Maya export will not be available in the executable
    echo   To add USD support, run setup_windows_v2.1.bat and install USD
    echo.
    set USD_AVAILABLE=NO
) else (
    echo USD library found - Multi-format export enabled
    echo.
    echo WARNING: --onefile mode may have issues with USD DLLs
    echo If the executable fails to run, try build_windows_v2.1_onedir.bat instead
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
if exist "MultiConverter.spec" (
    del MultiConverter.spec
)

echo.
echo ====================================
echo Running PyInstaller (--onefile mode)
echo ====================================
echo This creates a single executable file
echo (may take longer and be larger than --onedir)
echo ====================================
echo.

REM Build the executable with --onefile
%PYINSTALLER_CMD% ^
    --name=MultiConverter ^
    --onefile ^
    --windowed ^
    --clean ^
    --noconfirm ^
    --additional-hooks-dir=. ^
    --hidden-import=alembic_converter ^
    --hidden-import=readers ^
    --hidden-import=readers.base_reader ^
    --hidden-import=readers.alembic_reader ^
    --hidden-import=readers.usd_reader ^
    --hidden-import=core ^
    --hidden-import=core.scene_data ^
    --hidden-import=core.animation_detector ^
    --hidden-import=exporters ^
    --hidden-import=exporters.base_exporter ^
    --hidden-import=exporters.ae_exporter ^
    --hidden-import=exporters.usd_exporter ^
    --hidden-import=exporters.maya_ma_exporter ^
    --hidden-import=alembic ^
    --hidden-import=alembic.Abc ^
    --hidden-import=alembic.AbcGeom ^
    --hidden-import=alembic.AbcCoreAbstract ^
    --hidden-import=imath ^
    --hidden-import=imathnumpy ^
    --hidden-import=numpy ^
    --hidden-import=tkinter ^
    --hidden-import=sv_ttk ^
    --hidden-import=pxr ^
    --hidden-import=pxr.Usd ^
    --hidden-import=pxr.UsdGeom ^
    --hidden-import=pxr.Gf ^
    --hidden-import=pxr.Vt ^
    --hidden-import=pxr.Sdf ^
    --hidden-import=pxr.Tf ^
    --collect-all=alembic ^
    --collect-all=imath ^
    --collect-all=pxr ^
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
    echo If --onefile fails, try build_windows_v2.1_onedir.bat instead
    echo.
    pause
    exit /b 1
)

echo.
echo ====================================
echo Build Complete!
echo ====================================
echo.
echo Executable location: dist\MultiConverter.exe
echo.

REM Show file size
if exist "dist\MultiConverter.exe" (
    echo File size:
    dir dist\MultiConverter.exe | find "MultiConverter"
    echo.
)

echo Features included:
echo   - After Effects JSX + OBJ export
if "%USD_AVAILABLE%"=="YES" (
    echo   - USD .usdc export
    echo   - Maya USD export
    echo   - Maya MA export
) else (
    echo   x USD export (library not found)
    echo   x Maya export (library not found)
    echo   - Maya MA export
)

echo.
echo Distribution notes:
echo   - Distribute: dist\MultiConverter.exe (single file!)
echo   - Users need: Microsoft Visual C++ Redistributable 2015-2022
echo     Download: https://aka.ms/vs/17/release/vc_redist.x64.exe
echo.

if "%USD_AVAILABLE%"=="YES" (
    echo.
    echo NOTE: If the executable crashes or fails to start,
    echo USD DLLs may not be loading correctly in --onefile mode.
    echo Try build_windows_v2.1_onedir.bat for better compatibility.
    echo.
)

pause
