
@echo off

SET BULPER=%TOOLS_PATH%\bulper\bulper.py
SET BW_WORKSPACE=D:\Projects\STM32CubeIDE\workspace_1.15.0
SET BW_PROJECT_DIR=%BW_WORKSPACE%\BeachWolf
SET CDT_DIR="C:\ST\STM32CubeIDE_1.15.0\STM32CubeIDE\headless-build.bat"

@REM run pre-build
py.exe %BULPER% -d %BW_PROJECT_DIR%/ -v BeachWolf\include\versions.h -b 1

if %ERRORLEVEL% equ 0 (

) else (
    echo Command failed with exit code %ERRORLEVEL%.
)


