const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const isDev = process.env.NODE_ENV === 'development';

let mainWindow;
let flaskProcess;

function startFlask() {
  // In development, we assume the python environment is active
  // In production, we would use the bundled python executable
  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
  
  // Navigate to project root from web/electron
  const projectRoot = path.join(__dirname, '..', '..');
  
  flaskProcess = spawn(pythonCmd, ['-m', 'video_compressor', '--api'], {
    cwd: projectRoot,
    env: { ...process.env, PYTHONUNBUFFERED: '1' }
  });

  flaskProcess.stdout.on('data', (data) => {
    console.log(`Flask: ${data}`);
  });

  flaskProcess.stderr.on('data', (data) => {
    console.error(`Flask Error: ${data}`);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1100,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
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

app.on('ready', () => {
  startFlask();
  createWindow();
});

app.on('window-all-closed', () => {
  if (flaskProcess) {
    flaskProcess.kill();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

process.on('exit', () => {
  if (flaskProcess) {
    flaskProcess.kill();
  }
});
