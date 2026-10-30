@echo off
REM Paper2MD Windows Quick Launcher & Drag-Drop Runner
title Paper2MD Academic PDF Converter

if "%~1"=="" (
    echo ========================================================
    echo Paper2MD: Academic Paper PDF to Markdown Converter
    echo ========================================================
    echo Usage:
    echo   paper2md.bat ^<pdf_file_or_directory^> [additional files/dirs...]
    echo.
    echo Tip: You can drag and drop PDF files or folders directly onto this icon!
    echo ========================================================
    echo.
    pause
    exit /b 0
)

REM 1. Prefer pipx isolated environment if present
if exist "%USERPROFILE%\.local\bin\paper2md.exe" (
    "%USERPROFILE%\.local\bin\paper2md.exe" %*
    goto :done
)

REM 2. Fallback to active Python environment
python -m paper2md %*

:done
REM Pause if launched via double-click / drag-and-drop so user sees the summary
echo %cmdcmdline% | find /i "%~0" >nul && pause
