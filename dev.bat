@echo off
echo [1/3] Setting up backend...
call uv sync --extra dev

echo [2/3] Setting up frontend dependencies...
cd frontend
call npm install

echo [3/3] Starting the application...
call npm run electron:dev
