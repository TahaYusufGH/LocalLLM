param([int]$Port = 8765)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$py = "python"
# Sistemdeki Python gerekli paketlere sahipse sanal ortam kurmadan calistir.
& python -c "import fastapi, uvicorn, numpy, requests" 2>$null
if ($LASTEXITCODE -ne 0) {
    if (-not (Test-Path ".venv\Scripts\python.exe")) {
        Write-Host "Sanal ortam olusturuluyor..." -ForegroundColor Cyan
        python -m venv .venv
        & ".venv\Scripts\python.exe" -m pip install --upgrade pip -q
        Write-Host "Bagimliliklar kuruluyor..." -ForegroundColor Cyan
        & ".venv\Scripts\python.exe" -m pip install -r requirements.txt -q
    }
    $py = ".venv\Scripts\python.exe"
}
& $py main.py --port $Port
