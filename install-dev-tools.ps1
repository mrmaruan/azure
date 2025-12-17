Set-ExecutionPolicy Bypass -Scope Process -Force

# Instalar Chocolatey si no existe
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Chocolatey..."
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
}

# Instalar Python
Write-Host "Installing Python ${python_version}..."
choco install python --version=${python_version} -y

# Asegurarse de que Python y pip estén en el PATH
$env:PATH += ";$($env:ProgramFiles)\Python$($python_version.Replace('.',''))\Scripts;$($env:ProgramFiles)\Python$($python_version.Replace('.',''))\"

# Instalar Visual Studio Code
Write-Host "Installing Visual Studio Code..."
choco install vscode -y

# Instalar extensión de Python en VSCode
Write-Host "Installing Python extension in VSCode..."
code --install-extension ms-python.python --force

# Instalar paquetes de Python
Write-Host "Installing Python packages: tzdata, requests..."
pip install --upgrade pip
pip install tzdata requests

Write-Host "Installation completed successfully."
