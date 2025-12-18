# ================================
# Setup básico: Python + VSCode + carpeta auto
# ================================

Set-ExecutionPolicy Bypass -Scope Process -Force

Write-Host "Running as user: $env:USERNAME"
Write-Host "User profile: $env:USERPROFILE"

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
choco install python --version=$python_version -y --no-progress

# ------------------------------
# Instalar Visual Studio Code
# ------------------------------
Write-Host "Installing Visual Studio Code..."
choco install vscode -y --no-progress

# ------------------------------
# Crear carpeta auto en Documentos (FORMA CORRECTA)
# ------------------------------
$documentsPath = [Environment]::GetFolderPath("MyDocuments")
$autoFolder = Join-Path $documentsPath "auto"

if (-not (Test-Path $autoFolder)) {
    New-Item -ItemType Directory -Path $autoFolder -Force | Out-Null
    Write-Host "Created folder: $autoFolder"
} else {
    Write-Host "Folder already exists: $autoFolder"
}

# ------------------------------
# Descargar script desde GitHub
# ------------------------------
$scriptUrl  = "https://raw.githubusercontent.com/mrmaruan/azure/main/1.py"
$scriptPath = Join-Path $autoFolder "1.py"

Write-Host "Downloading script..."
Invoke-WebRequest -Uri $scriptUrl -OutFile $scriptPath -UseBasicParsing

if (Test-Path $scriptPath) {
    Write-Host "Script successfully saved to:"
    Write-Host $scriptPath
} else {
    Write-Error "Script download failed."
}

# ------------------------------
Write-Host "Setup completed successfully."
