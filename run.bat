@echo off

set DEPS_INSTALLED=false

if not exist venv (
    echo 创建虚拟环境...
    python -m venv venv
    set DEPS_INSTALLED=false
) else (
    set DEPS_INSTALLED=true
)

call venv\Scripts\activate.bat

REM 检查pip是否已经安装
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo pip未安装，将进行安装...
    set DEPS_INSTALLED=false
)

if "%DEPS_INSTALLED%"=="false" (
    echo 安装依赖, 这可能需要一段时间...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    echo 依赖检查完成...
)

python script.py

deactivate
pause
