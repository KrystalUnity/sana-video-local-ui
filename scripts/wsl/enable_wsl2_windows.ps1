$ErrorActionPreference = "Stop"

$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "Run this script from an elevated PowerShell window."
}

Write-Host "Enabling Windows Subsystem for Linux..."
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

Write-Host "Enabling Virtual Machine Platform..."
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

Write-Host ""
Write-Host "WSL2 Windows features are enabled."
Write-Host "If WSL still does not launch, reboot Windows."
Write-Host ""
Write-Host "Then install Ubuntu:"
Write-Host "  wsl.exe --install -d Ubuntu"
Write-Host ""
Write-Host "After Ubuntu launches, verify NVIDIA CUDA visibility:"
Write-Host "  wsl.exe -d Ubuntu -- nvidia-smi"
