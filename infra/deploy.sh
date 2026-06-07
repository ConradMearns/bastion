#!/bin/bash
# Deploy bastion app to the Hetzner server (run after pulumi up)
set -euo pipefail

IP="2a01:4ff:1f0:690::1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASTION_DIR="$SCRIPT_DIR/../bastion"

echo "==> Waiting for cloud-init to finish..."
ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 "root@$IP" "cloud-init status --wait"

echo "==> Uploading bastion app..."
ssh "root@$IP" "rm -rf /opt/bastion && mkdir -p /opt/bastion"
tar czf - -C "$BASTION_DIR" --exclude='.venv' --exclude='__pycache__' --exclude='*.pyc' . \
    | ssh "root@$IP" "tar xzf - -C /opt/bastion"

echo "==> Installing dependencies..."
ssh "root@$IP" "cd /opt/bastion && /root/.local/bin/uv sync"

echo "==> Setting up Caddy with self-signed cert..."
ssh "root@$IP" '
mkdir -p /etc/caddy/certs
openssl req -x509 -newkey rsa:2048 -keyout /etc/caddy/certs/key.pem \
    -out /etc/caddy/certs/cert.pem -days 3650 -nodes \
    -subj "/CN=bastion" \
    -addext "subjectAltName=IP:'"$IP"'"
chown -R caddy:caddy /etc/caddy/certs
chmod 600 /etc/caddy/certs/key.pem
chmod 644 /etc/caddy/certs/cert.pem

cat > /etc/caddy/Caddyfile << CADDYEOF
:443 {
    tls /etc/caddy/certs/cert.pem /etc/caddy/certs/key.pem
    reverse_proxy localhost:8000
}
CADDYEOF
'

echo "==> Starting services..."
ssh "root@$IP" "systemctl daemon-reload && systemctl enable bastion caddy && systemctl restart bastion caddy"

echo "==> Waiting for services..."
sleep 3
ssh "root@$IP" "systemctl status bastion caddy --no-pager"

echo ""
echo "==> Testing API..."
curl -k -s "https://[$IP]/health" | python3 -m json.tool
echo ""
echo "Done! Dashboard: https://conradmearns.github.io/bastion/"
