$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$BackendOutLog = Join-Path $Root "backend.out.log"
$BackendErrLog = Join-Path $Root "backend.err.log"
$FrontendOutLog = Join-Path $Root "frontend.out.log"
$FrontendErrLog = Join-Path $Root "frontend.err.log"
$LocalPython = Join-Path $Root "backend\.venv\Scripts\python.exe"
$SiblingPython = Join-Path (Split-Path -Parent $Root) "sana-video-prep\.venv\Scripts\python.exe"
$SiblingModel = Join-Path (Split-Path -Parent $Root) "sana-video-prep\models\SANA-Video_2B_480p_diffusers"

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

if (-not $env:SANA_MODEL_DIR -and (Test-Path $SiblingModel)) {
    $env:SANA_MODEL_DIR = $SiblingModel
}

if (Test-Path $LocalPython) {
    $Python = $LocalPython
} elseif (Test-Path $SiblingPython) {
    $Python = $SiblingPython
} else {
    $Python = "python"
}

$BackendArgs = @(
    "-m",
    "uvicorn",
    "backend.app:app",
    "--host",
    "127.0.0.1",
    "--port",
    "8008"
)

if (Test-LocalPort -Port 8008) {
    Write-Output "Backend already reachable: http://127.0.0.1:8008"
} else {
    $Backend = Start-Process -FilePath $Python `
        -ArgumentList $BackendArgs `
        -WorkingDirectory $Root `
        -RedirectStandardOutput $BackendOutLog `
        -RedirectStandardError $BackendErrLog `
        -WindowStyle Hidden `
        -PassThru
    Write-Output "Backend PID: $($Backend.Id)  http://127.0.0.1:8008"
}

if (Test-LocalPort -Port 5173) {
    Write-Output "Frontend already reachable: http://127.0.0.1:5173"
} else {
    $Frontend = Start-Process -FilePath "npm.cmd" `
        -ArgumentList @("run", "dev", "--", "--port", "5173") `
        -WorkingDirectory (Join-Path $Root "frontend") `
        -RedirectStandardOutput $FrontendOutLog `
        -RedirectStandardError $FrontendErrLog `
        -WindowStyle Hidden `
        -PassThru
    Write-Output "Frontend PID: $($Frontend.Id)  http://127.0.0.1:5173"
}

Write-Output "Logs: $BackendOutLog, $BackendErrLog, $FrontendOutLog, $FrontendErrLog"
