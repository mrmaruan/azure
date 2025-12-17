$ErrorActionPreference = "Stop"

Write-Output "Installing Chocolatey..."
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

Write-Output "Installing Python 3.11.4..."
choco install python --version=3.11.4 -y

Write-Output "Installing Visual Studio Code..."
choco install vscode -y

Write-Output "Installation completed successfully."
