# ================================
# Script completo de setup (FIXED)
# ================================

# Permitir ejecución de scripts temporalmente
Set-ExecutionPolicy Bypass -Scope Process -Force

# ------------------------------
# Instalar Chocolatey si no existe
# ------------------------------
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Chocolatey..."
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
}

# ------------------------------
# Instalar Python
# ------------------------------
$python_version = "3.11.4"
Write-Host "Installing Python $python_version..."
choco install python --version=$python_version -y

# Asegurar que Python y pip estén en PATH
$pythonPath = "${env:ProgramFiles}\Python$($python_version.Replace('.', ''))"
$env:PATH += ";$pythonPath;$pythonPath\Scripts"

# Instalar paquetes de Python
Write-Host "Installing Python packages: tzdata, requests..."
python -m pip install --upgrade pip
pip install tzdata requests

# ------------------------------
# Instalar Visual Studio Code
# ------------------------------
Write-Host "Installing Visual Studio Code..."
choco install vscode -y

# ------------------------------
# Detectar code.cmd REAL (CLAVE)
# ------------------------------
$possibleCodePaths = @(
    "$env:LOCALAPPDATA\Programs\Microsoft VS Code\bin\code.cmd",
    "$env:ProgramFiles\Microsoft VS Code\bin\code.cmd"
)

$VSCodePath = $possibleCodePaths | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $VSCodePath) {
    Write-Error "VS Code executable (code.cmd) not found. Installation failed."
    exit 1
}

Write-Host "Using VS Code executable at: $VSCodePath"

# Inicializar VS Code (crea perfil del usuario)
& $VSCodePath --version | Out-Null

# ------------------------------
# Instalar extensiones de VSCode
# ------------------------------
$extensions = @(
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.python-devtools"
)

$installed = & $VSCodePath --list-extensions

foreach ($ext in $extensions) {
    if ($installed -contains $ext) {
        Write-Host "$ext already installed." -ForegroundColor Gray
    } else {
        Write-Host "Installing $ext..." -ForegroundColor Cyan
        & $VSCodePath --install-extension $ext --force
    }
}

# ------------------------------
# Crear carpeta 'auto' en Documentos
# ------------------------------
$autoFolder = Join-Path $env:USERPROFILE "Documents\auto"

if (-not (Test-Path $autoFolder)) {
    New-Item -ItemType Directory -Path $autoFolder | Out-Null
    Write-Host "Created folder: $autoFolder"
}

# ------------------------------
# Descargar script.py desde GitHub
# ------------------------------
$scriptUrl = "https://raw.githubusercontent.com/mrmaruan/azure/main/1.py"
$scriptPath = Join-Path $autoFolder "1.py"

Write-Host "Downloading script from GitHub..."
Invoke-WebRequest -Uri $scriptUrl -OutFile $scriptPath
Write-Host "Script saved to $scriptPath"

# ------------------------------
Write-Host "Installation completed successfully."
