#!/bin/bash
set -euo pipefail
umask 077

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WGCF="$DIR/wgcf"
cd "$DIR"

echo "=== Cloudflare WARP Optimizer ==="

# 1. Check/Register Account
if [ ! -f "wgcf-account.toml" ]; then
    echo "No local WARP account. Install wgcf, then run ./wgcf register yourself."
    echo "Review and accept the provider's terms in that interactive command."
    exit 1
else
    echo "Account already exists."
fi

# 2. Generate Profile
if [ ! -f "wgcf-profile.conf" ]; then
    echo "Generating WireGuard profile..."
    "$WGCF" generate
fi

# 3. Scan for Best IP
echo "Scanning for preferred endpoint..."
python3 "$DIR/latency_test.py"

if [ -f "best_endpoint.txt" ]; then
    BEST_EP=$(cat best_endpoint.txt)
    echo "Updating profile with endpoint: $BEST_EP"
    
    # Validate scan output before updating a private configuration.
    python3 - "$BEST_EP" <<'PY'
import ipaddress
from pathlib import Path
import re
import sys

endpoint = sys.argv[1]
host, port = endpoint.rsplit(":", 1)
ipaddress.ip_address(host)
if not 1 <= int(port) <= 65535:
    raise ValueError("Invalid endpoint port")
path = Path("wgcf-profile.conf")
text, count = re.subn(r"(?m)^Endpoint\s*=.*$", "Endpoint = " + endpoint, path.read_text())
if count != 1:
    raise ValueError("Expected one Endpoint field")
path.write_text(text)
PY
    
    echo "=== Success! ==="
    echo "Your optimized WireGuard configuration is ready: wgcf-profile.conf"
    
    # Run export script
    echo "Exporting to Clash/Loon formats..."
    python3 "$DIR/export_config.py"
    
    echo ""
    echo "1. For WireGuard App: Import 'wgcf-profile.conf'"
    echo "2. For Proxies:"
    echo "   - Clash Meta: warp_clash.yaml"
    echo "   - Loon:       warp_loon.conf"
    echo "   - Surge:      warp_surge.conf"
    echo "   - QuanX:      warp_quanx.conf"
    echo "   - Shadowrocket: warp_shadowrocket.conf"
    echo "   - Sing-box:   warp_singbox.json"
else
    echo "Scanning failed. Retaining default endpoint."
    exit 1
fi
