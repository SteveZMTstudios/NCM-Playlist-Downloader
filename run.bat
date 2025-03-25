@echo off

if not exist venv (
    echo 创建虚拟环境...
    python -m venv venv
)

call venv\Scripts\activate.bat

@REM REM 检查依赖是否已安装
@REM set DEPS_INSTALLED=true
@REM pip freeze > temp_installed.txt

@REM REM 分别检查每个依赖
@REM findstr /i "qrcode" temp_installed.txt > nul 2>&1
@REM if %errorlevel% neq 0 set DEPS_INSTALLED=false

@REM findstr /i "requests" temp_installed.txt > nul 2>&1
@REM if %errorlevel% neq 0 set DEPS_INSTALLED=false

@REM findstr /i "pillow" temp_installed.txt > nul 2>&1
@REM if %errorlevel% neq 0 set DEPS_INSTALLED=false

@REM findstr /i "pyncm" temp_installed.txt > nul 2>&1
@REM if %errorlevel% neq 0 set DEPS_INSTALLED=false

@REM del temp_installed.txt

@REM if "%DEPS_INSTALLED%"=="false" (
    echo 安装依赖, 这可能需要一段时间...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
@REM ) else (
@REM     echo 依赖检查完成，直接运行脚本...
@REM )

python script.py

deactivate
pause