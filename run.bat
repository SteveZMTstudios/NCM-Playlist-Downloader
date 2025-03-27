@echo off

set DEPS_INSTALLED=false

if not exist venv (
    echo �������⻷��...
    python -m venv venv
    set DEPS_INSTALLED=false
) else (
    set DEPS_INSTALLED=true
)

call venv\Scripts\activate.bat

REM ���pip�Ƿ��Ѿ���װ
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo pipδ��װ�������а�װ...
    set DEPS_INSTALLED=false
)

if "%DEPS_INSTALLED%"=="false" (
    echo ��װ����, �������Ҫһ��ʱ��...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    echo ����������...
)

python script.py

deactivate
pause
