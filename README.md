# bastion

Health monitoring dashboard for servers — collect health metrics and view status via a static web page.

**[Live Dashboard →](https://conradmearns.github.io/bastion/)**

## Architecture

```
Host Agents ──JWT──▶ Bastion API (Hetzner) ──HTTPS──▶ GitHub Pages Dashboard
```

- **bastion/** — FastAPI app collecting health reports, serves them via HTTPS (Caddy reverse proxy with self-signed cert)
- **host/** — Python agent that sends CPU/mem/disk/uptime every 60s
- **docs/** — Static HTML dashboard deployed via GitHub Pages
- **infra/** — Pulumi IaC for Hetzner Cloud (cpx11, IPv6-only, us-west)

## Running a Host Agent

```bash
cd host
uv sync

# Get a token from the bastion
TOKEN=$(curl -k -s -X POST "https://[2a01:4ff:1f0:690::1]/token?hostname=YOUR_HOSTNAME" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# Run the agent (reports every 60s)
uv run python agent.py \
  --bastion-url "https://[2a01:4ff:1f0:690::1]" \
  --token "$TOKEN" \
  --hostname "YOUR_HOSTNAME"
```

Or edit `host/config.yaml` with your token and run:

```bash
cd host
uv run python agent.py -c config.yaml
```

## Deploying the Bastion

```bash
cd infra
PULUMI_CONFIG_PASSPHRASE=... pulumi up --yes
bash deploy.sh
```
