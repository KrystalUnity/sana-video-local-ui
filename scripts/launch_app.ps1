$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$RunDev = Join-Path $Root "scripts\run_dev.ps1"
$Url = "http://127.0.0.1:5173"

function Test-LocalPort {
    param([int]$Port)

    $Client = [System.Net.Sockets.TcpClient]::new()
    try {
        $Connect = $Client.BeginConnect("127.0.0.1", $Port, $null, $null)
        if (-not $Connect.AsyncWaitHandle.WaitOne(300)) {
            return $false
        }
        $Client.EndConnect($Connect)
        return $true
    } catch {
        return $false
    } finally {
        $Client.Close()
    }
}

Write-Output "Starting SANA Video Workbench..."
powershell -NoProfile -ExecutionPolicy Bypass -File $RunDev

Write-Output "Waiting for frontend: $Url"
$ready = $false
for ($i = 0; $i -lt 40; $i++) {
    if (Test-LocalPort -Port 5173) {
        $ready = $true
        break
    }
    Start-Sleep -Milliseconds 500
}

if (-not $ready) {
    throw "Frontend did not become reachable at $Url. Check frontend.err.log and frontend.out.log."
}

Start-Process $Url
Write-Output "Opened $Url"
