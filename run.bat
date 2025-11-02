@echo off

set DEPS_INSTALLED=false
title 网易云音乐下载器

python --version >nul 2>&1
if %errorlevel% neq 0 (
    python3 --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo 检测到未安装Python或未配置环境变量，请先安装Python 3.6及以上版本。
        echo 若 Microsoft Store未自动打开，请访问 https://www.python.org/downloads/ 下载并安装。
        start https://www.python.org/downloads/
        exit /b
    ) else (
        set PYTHON_CMD=python3
    )
    
) else (
    set PYTHON_CMD=python
)

if not exist venv (
    echo 创建虚拟环境...
    %PYTHON_CMD% -m venv venv
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
    %PYTHON_CMD% -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple/
    %PYTHON_CMD% -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
) else (
    echo 依赖检查完成...
)

cls

%PYTHON_CMD% script.py
if %errorlevel% neq 0 (
    echo 程序未正常退出，正在清理...
    rmdir /s /q venv
    exit /b
)

deactivate
pause
