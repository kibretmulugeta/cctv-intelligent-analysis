#!/usr/bin/env bash
# Cloudflare Local API Tunneling Script
# Exposes local FastAPI server on port 8000 via cloudflared

echo "============================================================"
echo " Starting Cloudflare Local Tunnel for CCTV AI Backend..."
echo "============================================================"

if ! command -v cloudflared &> /dev/null; then
    echo "cloudflared is not installed. Download from https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/create-local-tunnel/"
    exit 1
fi

cloudflared tunnel --url http://localhost:8000
