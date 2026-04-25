import { app, BrowserWindow, dialog, ipcMain } from 'electron';
import * as path from 'path';
import { spawn, ChildProcess } from 'child_process';
import { fileURLToPath } from 'url';
import axios from 'axios';

// In ESM, __dirname is not available by default
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const isDev = process.env.NODE_ENV === 'development';
const API_PORT = 5000;
const API_URL = `http://127.0.0.1:${API_PORT}/api`;

let mainWindow: BrowserWindow | null = null;
let flaskProcess: ChildProcess | null = null;
let isQuitting = false;
let isRestarting = false;

async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await axios.get(`${API_URL}/health`, { timeout: 2000 });
    return response.status === 200;
  } catch (error) {
    return false;
  }
}

function startFlask() {
  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
  
  // In production, we might want to use a bundled executable
  // For now, we assume python is in the path and use the project root
  const projectRoot = isDev 
    ? path.join(__dirname, '..', '..')
    : path.join(process.resourcesPath, 'app');
  
  console.log(`Starting Flask with root: ${projectRoot}`);

  const config = isDev ? 'dev' : 'prod';
  
  flaskProcess = spawn(pythonCmd, ['-m', 'video_compressor', '--api', '--port', API_PORT.toString(), '--config', config], {
    cwd: projectRoot,
    env: { ...process.env, PYTHONUNBUFFERED: '1' }
  });

  flaskProcess.stdout?.on('data', (data) => {
    console.log(`Flask: ${data}`);
  });

  flaskProcess.stderr?.on('data', (data) => {
    console.error(`Flask Error: ${data}`);
  });

  flaskProcess.on('close', (code) => {
    console.log(`Flask process exited with code ${code}`);
    flaskProcess = null;
    
    if (!isQuitting && !isRestarting) {
      dialog.showMessageBox({
        type: 'error',
        title: 'Backend Process Error',
        message: 'The Flask backend process has exited unexpectedly.',
        buttons: ['Restart', 'Exit'],
      }).then((result) => {
        if (result.response === 0) {
          startFlask();
        } else {
          app.quit();
        }
      });
    }
  });

  flaskProcess.on('error', (err) => {
    console.error('Failed to start Flask process:', err);
    dialog.showErrorBox('Startup Error', `Failed to start the backend process: ${err.message}`);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1100,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    title: "AmeCompression"
  });

  const startUrl = isDev 
    ? 'http://localhost:5173' 
    : `file://${path.join(__dirname, '../dist/index.html')}`;

  mainWindow.loadURL(startUrl);

  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// IPC Handlers
ipcMain.handle('get-api-url', () => {
  return API_URL;
});

ipcMain.handle('get-backend-status', async () => {
  const isHealthy = await checkBackendHealth();
  return {
    running: !!flaskProcess,
    healthy: isHealthy,
    port: API_PORT
  };
});

ipcMain.handle('restart-backend', async () => {
  if (flaskProcess) {
    isRestarting = true;
    await new Promise<void>((resolve) => {
      flaskProcess!.once('close', () => {
        isRestarting = false;
        resolve();
      });
      flaskProcess!.kill();
    });
  }
  startFlask();
  return true;
});

app.on('ready', () => {
  startFlask();
  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

app.on('before-quit', () => {
  isQuitting = true;
  if (flaskProcess) {
    flaskProcess.kill();
    flaskProcess = null;
  }
});
