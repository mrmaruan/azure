# ================================
# Script completo de setup
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
pip install --upgrade pip
pip install tzdata requests

# ------------------------------
# Instalar Visual Studio Code
# ------------------------------
Write-Host "Installing Visual Studio Code..."
choco install vscode -y

# ------------------------------
# Instalar extensiones en VSCode
# ------------------------------
# Ruta completa a code.cmd
$VSCodePath = "$env:ProgramFiles\Microsoft VS Code\bin\code.cmd"

# Lista de extensiones
$extensions = @(
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.python-devtools"
)

# Esperar que VSCode inicialice perfil
Start-Process -FilePath $VSCodePath -ArgumentList "--version" -Wait

# Listar extensiones ya instaladas
$installed = & $VSCodePath --list-extensions

foreach ($ext in $extensions) {
    if ($installed -contains $ext) {
        Write-Host "$ext already installed." -ForegroundColor Gray
    } else {
        Write-Host "Installing $ext..." -ForegroundColor White
        & $VSCodePath --install-extension $ext --force
    }
}

# ------------------------------
# Crear carpeta 'auto' en Documentos y descargar script.py
# ------------------------------
$autoFolder = "$env:USERPROFILE\Documents\auto"
if (-not (Test-Path $autoFolder)) {
    New-Item -ItemType Directory -Path $autoFolder | Out-Null
    Write-Host "Created folder: $autoFolder"
} else {
    Write-Host "Folder already exists: $autoFolder"
}

# URL de tu script raw en GitHub
$scriptUrl = "https://raw.githubusercontent.com/usuario/repositorio/rama/script.py"  # Cambia esto a tu URL
$scriptPath = Join-Path $autoFolder "1.py"

Write-Host "Downloading script.py from GitHub..."
Invoke-WebRequest -Uri $scriptUrl -OutFile $scriptPath
Write-Host "script.py saved to $scriptPath"

# ------------------------------
Write-Host "Installation completed successfully."
