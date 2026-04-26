@echo off
setlocal

echo [1/3] Setting up backend...
call uv sync --extra dev
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Backend setup failed.
    exit /b %ERRORLEVEL%
)

echo [2/3] Setting up frontend dependencies...
pushd frontend
call npm install
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Frontend dependency installation failed.
    popd
    exit /b %ERRORLEVEL%
)

echo [3/3] Starting the application...
call npm run electron:dev
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Application failed to start.
    popd
    exit /b %ERRORLEVEL%
)

popd
