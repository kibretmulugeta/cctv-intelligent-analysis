<#
.SYNOPSIS
    Deploys the CCTV backend to Hugging Face Spaces as a Docker-based Space.

.DESCRIPTION
    This script:
    1. Creates a temporary staging directory
    2. Copies backend source, model weights, Dockerfile, README into a flat structure
    3. Initializes a git repo and pushes to HF Spaces

.PARAMETER HfUsername
    Your Hugging Face username (e.g., "kibretmulugeta")

.PARAMETER SpaceName
    The Space name (default: "cctv-ai-backend")

.EXAMPLE
    .\deploy_hf.ps1 -HfUsername "kibretmulugeta"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$HfUsername,

    [string]$SpaceName = "cctv-ai-backend"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
$BackendDir = Join-Path $ProjectRoot "backend"
$InfraHF = Join-Path $ProjectRoot "infra\huggingface"
$StagingDir = Join-Path $ProjectRoot "infra\huggingface\_staging"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  HF Spaces Deployment: $HfUsername/$SpaceName" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Clean staging
if (Test-Path $StagingDir) { Remove-Item -Recurse -Force $StagingDir }
New-Item -ItemType Directory -Path $StagingDir | Out-Null

Write-Host "`n[1/5] Copying Dockerfile & README..." -ForegroundColor Yellow
Copy-Item (Join-Path $InfraHF "Dockerfile") (Join-Path $StagingDir "Dockerfile")
Copy-Item (Join-Path $InfraHF "README.md") (Join-Path $StagingDir "README.md")
Copy-Item (Join-Path $InfraHF "requirements.txt") (Join-Path $StagingDir "requirements.txt")

Write-Host "[2/5] Copying backend app/ source..." -ForegroundColor Yellow
Copy-Item -Recurse (Join-Path $BackendDir "app") (Join-Path $StagingDir "app")

Write-Host "[3/5] Copying YOLO model weights..." -ForegroundColor Yellow
$yoloPt = Join-Path $BackendDir "yolo11n.pt"
if (Test-Path $yoloPt) {
    Copy-Item $yoloPt (Join-Path $StagingDir "yolo11n.pt")
} else {
    $yoloPt = Join-Path $ProjectRoot "yolo11n.pt"
    if (Test-Path $yoloPt) {
        Copy-Item $yoloPt (Join-Path $StagingDir "yolo11n.pt")
    } else {
        Write-Warning "yolo11n.pt not found! The Space will need to download it on first run."
    }
}

Write-Host "[4/5] Creating .env for production..." -ForegroundColor Yellow
@"
DEBUG=false
DEVICE=cpu
ALLOWED_ORIGINS=*
DATABASE_URL=sqlite+aiosqlite:///./cctv.db
YOLO_MODEL=yolo11n.pt
"@ | Out-File -Encoding UTF8 (Join-Path $StagingDir ".env")

Write-Host "[5/5] Initializing git and pushing to HF Spaces..." -ForegroundColor Yellow
Push-Location $StagingDir

git init
git lfs install
git lfs track "*.pt"
git lfs track "*.onnx"
git add -A
git commit -m "Deploy CCTV AI backend to HF Spaces"

$RemoteUrl = "https://huggingface.co/spaces/$HfUsername/$SpaceName"
Write-Host "`nPushing to: $RemoteUrl" -ForegroundColor Green
git remote add origin $RemoteUrl
git push --force origin main

Pop-Location

Write-Host "`n=============================================" -ForegroundColor Green
Write-Host "  Deployment complete!" -ForegroundColor Green
Write-Host "  Space URL: https://huggingface.co/spaces/$HfUsername/$SpaceName" -ForegroundColor Green
Write-Host "  API URL:   https://$HfUsername-$SpaceName.hf.space" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
