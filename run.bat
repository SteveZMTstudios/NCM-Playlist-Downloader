@echo off

if not exist venv (
    echo 创建虚拟环境...
    python -m venv venv
)

call venv\Scripts\activate.bat

REM 检查依赖是否已安装
set DEPS_INSTALLED=false
pip freeze > temp_installed.txt
findstr /i "qrcode requests pillow pyncm" temp_installed.txt > nul 2>&1
if %errorlevel% equ 0 (
    echo 依赖已安装。
    set DEPS_INSTALLED=true
)
del temp_installed.txt

if "%DEPS_INSTALLED%"=="false" (
    echo 安装依赖, 这可能需要一段时间...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    echo 依赖检查完成，直接运行脚本...
)

python script.py

deactivate
pause