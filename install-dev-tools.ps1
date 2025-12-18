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
Write-Host "Setup completed successfully."
