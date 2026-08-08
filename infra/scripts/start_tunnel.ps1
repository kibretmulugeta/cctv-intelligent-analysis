# Cloudflare Local HTTPS Tunneling Script for Windows PowerShell
# Exposes local FastAPI backend (8000) and React frontend (5173) via cloudflared

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Launching Cloudflare HTTPS Tunnel for CCTV AI Platform..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Check if cloudflared is installed
if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    Write-Host "[WARNING] cloudflared is not installed in system PATH." -ForegroundColor Yellow
    Write-Host "Download the Windows executable from:" -ForegroundColor Yellow
    Write-Host "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -ForegroundColor Green
    Write-Host "Or install via winget: winget install --id Cloudflare.cloudflared" -ForegroundColor Green
    exit 1
}

Write-Host "[INFO] Starting HTTPS Tunnel pointing to http://localhost:8000 (Backend API)..." -ForegroundColor Green
cloudflared tunnel --url http://localhost:8000
