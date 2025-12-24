@echo off
echo ================================================
echo   Hyperparameter Oracle - DSA-Driven AutoML
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/4] Checking Python dependencies...
pip show flask >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    echo Dependencies already installed
)

echo.
echo [2/4] Checking C library...
if exist "build\oracle.dll" (
    echo C library found: build\oracle.dll
) else (
    echo [WARNING] C library not found
    echo Attempting to compile...
    gcc -shared -o build\oracle.dll -fPIC src\c\*.c -Iinclude
    if %errorlevel% neq 0 (
        echo [ERROR] Compilation failed. Please install MinGW/GCC
        pause
        exit /b 1
    )
)

echo.
echo [3/4] Starting Flask API Server...
cd src\python
start "Hyperparameter Oracle API" python api_server.py

echo.
echo [4/4] Waiting for server to start...
timeout /t 3 /nobreak >nul

echo.
echo ================================================
echo   Server Started Successfully!
echo ================================================
echo.
echo Dashboard URL: http://localhost:5000
echo.
echo Opening browser in 2 seconds...
timeout /t 2 /nobreak >nul

start http://localhost:5000

echo.
echo Press any key to stop the server...
pause >nul

echo.
echo Stopping server...
taskkill /FI "WindowTitle eq Hyperparameter Oracle API*" /T /F >nul 2>&1

echo Server stopped. Goodbye!
