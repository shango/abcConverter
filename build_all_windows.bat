@echo off
REM ==============================================================================
REM MultiConverter v2.1.0 - Complete Windows Setup and Build
REM ==============================================================================
REM This script runs both setup and build in one go
REM ==============================================================================

echo ====================================
echo MultiConverter v2.1.0
echo Complete Setup and Build
echo ====================================
echo.
echo This script will:
echo   1. Set up Python environment
echo   2. Install all dependencies
echo   3. Build the executable
echo.
pause

REM Run setup
call setup_windows_v2.1.bat
if errorlevel 1 (
    echo.
    echo Setup failed! Please fix the errors above.
    pause
    exit /b 1
)

echo.
echo.
echo ====================================
echo Setup complete! Starting build...
echo ====================================
echo.
timeout /t 3 /nobreak

REM Run build
call build_windows_v2.1.bat
if errorlevel 1 (
    echo.
    echo Build failed! Please check the errors above.
    pause
    exit /b 1
)

echo.
echo ====================================
echo All Done!
echo ====================================
echo.
echo Your executable is ready at: dist\MultiConverter.exe
echo.
pause
