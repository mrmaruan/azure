# Permitir ejecución de scripts temporalmente
Set-ExecutionPolicy Bypass -Scope Process -Force

# Instalar Chocolatey si no existe
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Chocolatey..."
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
}

# Instalar Python
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

# Instalar Visual Studio Code
Write-Host "Installing Visual Studio Code..."
choco install vscode -y

# Asegurar ruta completa a code.cmd
$VSCodePath = "${env:ProgramFiles}\Microsoft VS Code\bin\code.cmd"

# Lista de extensiones que quieres instalar
$extensions = @(
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.python-devtools"
)

# Instalar extensiones en VSCode
foreach ($ext in $extensions) {
    Write-Host "Installing VSCode extension: $ext"
    Start-Process -FilePath $VSCodePath -ArgumentList "--install-extension $ext --force" -Wait
}

Write-Host "Installation completed successfully."

