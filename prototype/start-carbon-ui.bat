@echo off
REM Carbon UI Startup Script for Windows
REM Double-click this file to start the entire Carbon UI environment

setlocal enabledelayedexpansion

echo ==========================================
echo   Carbon UI Environment Startup
echo ==========================================
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM Change to project root
cd /d "%PROJECT_ROOT%"

REM Function to detect Docker runtime
:detect_docker_runtime
where orbctl >nul 2>&1
if not errorlevel 1 (
    set DOCKER_RUNTIME=orbstack
    goto :eof
)

if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
    set DOCKER_RUNTIME=docker-desktop
    goto :eof
)

if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
    set DOCKER_RUNTIME=docker-desktop
    goto :eof
)

set DOCKER_RUNTIME=unknown
goto :eof

REM Function to start Docker runtime
:start_docker_runtime
if "%DOCKER_RUNTIME%"=="orbstack" (
    echo 🚀 Starting OrbStack...
    start "" "orbstack:"
    timeout /t 3 /nobreak >nul
    goto :eof
)

if "%DOCKER_RUNTIME%"=="docker-desktop" (
    echo 🚀 Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if errorlevel 1 start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
    timeout /t 5 /nobreak >nul
    goto :eof
)

echo ❌ Error: No Docker runtime found!
echo.
echo Please install one of the following:
echo   • Docker Desktop: https://www.docker.com/products/docker-desktop
echo   • OrbStack: https://orbstack.dev
echo.
pause
exit /b 1

REM Function to wait for Docker to be ready
:wait_for_docker
set MAX_WAIT=30
set WAIT_COUNT=0

echo ⏳ Waiting for Docker to be ready...

:wait_docker_loop
set /a WAIT_COUNT+=1
if %WAIT_COUNT% gtr %MAX_WAIT% (
    echo.
    echo ❌ Error: Docker failed to start after 30 seconds
    echo Please check your Docker installation and try again.
    echo.
    pause
    exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    echo|set /p="."
    timeout /t 1 /nobreak >nul
    goto wait_docker_loop
)

echo.
echo ✅ Docker is ready!
echo.
goto :eof

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Docker is not running

    REM Detect which Docker runtime is available
    call :detect_docker_runtime
    echo ℹ️  Detected runtime: %DOCKER_RUNTIME%
    echo.

    REM Try to start it
    call :start_docker_runtime

    REM Wait for Docker to be ready
    call :wait_for_docker
) else (
    echo ✅ Docker is already running
    echo.
)

REM Check if docker-compose exists
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: docker-compose is not installed!
    echo Please install Docker Desktop which includes docker-compose.
    echo.
    pause
    exit /b 1
)

echo ✅ docker-compose is available
echo.

REM Stop any existing containers
echo 🛑 Stopping any existing containers...
docker-compose down >nul 2>&1
echo.

REM Build and start containers
echo 🏗️  Building and starting containers...
echo This may take a few minutes on first run...
echo.
docker-compose up -d --build

REM Wait for services to be healthy
echo.
echo ⏳ Waiting for services to be ready...
echo.

REM Wait for API to be healthy
set MAX_ATTEMPTS=30
set ATTEMPT=0

:wait_api
set /a ATTEMPT+=1
if %ATTEMPT% gtr %MAX_ATTEMPTS% (
    echo ❌ API failed to start. Check logs with: docker-compose logs api
    pause
    exit /b 1
)

curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo    Waiting for API... (%ATTEMPT%/%MAX_ATTEMPTS%)
    timeout /t 2 /nobreak >nul
    goto wait_api
)

echo ✅ API is ready

REM Wait for Carbon UI to be ready
set ATTEMPT=0

:wait_ui
set /a ATTEMPT+=1
if %ATTEMPT% gtr %MAX_ATTEMPTS% (
    echo ❌ Carbon UI failed to start. Check logs with: docker-compose logs carbon-ui
    pause
    exit /b 1
)

curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo    Waiting for Carbon UI... (%ATTEMPT%/%MAX_ATTEMPTS%)
    timeout /t 2 /nobreak >nul
    goto wait_ui
)

echo ✅ Carbon UI is ready

REM Wait for Streamlit to be ready
set ATTEMPT=0

:wait_streamlit
set /a ATTEMPT+=1
if %ATTEMPT% gtr %MAX_ATTEMPTS% (
    echo ❌ Streamlit failed to start. Check logs with: docker-compose logs app
    pause
    exit /b 1
)

curl -s http://localhost:8501 >nul 2>&1
if errorlevel 1 (
    echo    Waiting for Streamlit... (%ATTEMPT%/%MAX_ATTEMPTS%)
    timeout /t 2 /nobreak >nul
    goto wait_streamlit
)

echo ✅ Streamlit is ready

echo.
echo ==========================================
echo   🎉 Carbon UI Environment is Ready!
echo ==========================================
echo.
echo Services running:
echo   • Carbon UI:  http://localhost:3000
echo   • API:        http://localhost:8000
echo   • Streamlit:  http://localhost:8501
echo   • Postgres:   localhost:5432
echo.
echo To view logs:
echo   docker-compose logs -f
echo.
echo To stop all services:
echo   docker-compose down
echo.
echo Opening Carbon UI in your browser...
timeout /t 2 /nobreak >nul

REM Open Carbon UI in default browser
start http://localhost:3000

echo.
echo Press Ctrl+C to stop viewing logs, or close to keep services running.
echo.

REM Keep terminal open and show logs
docker-compose logs -f

@REM Made with Bob
