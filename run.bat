@echo off

if not exist venv (
    echo �������⻷��...
    python -m venv venv
)

call venv\Scripts\activate.bat

@REM REM ��������Ƿ��Ѱ�װ
@REM set DEPS_INSTALLED=true
@REM pip freeze > temp_installed.txt

@REM REM �ֱ���ÿ������
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
    echo ��װ����, �������Ҫһ��ʱ��...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
@REM ) else (
@REM     echo ���������ɣ�ֱ�����нű�...
@REM )

python script.py

deactivate
pause