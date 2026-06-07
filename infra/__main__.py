"""Bastion host on Hetzner Cloud — cpx11, us-west (Hillsboro), IPv6 only."""

import base64
import io
import os
import tarfile
import pulumi
import pulumi_hcloud as hcloud

# --- SSH key ---
ssh_key_path = os.path.expanduser("~/.ssh/id_ed25519.pub")
with open(ssh_key_path) as f:
    public_key = f.read().strip()

ssh_key = hcloud.SshKey(
    "bastion-key",
    name="bastion",
    public_key=public_key,
)

# --- Package bastion app as base64 tarball ---
bastion_dir = os.path.join(os.path.dirname(__file__), "..", "bastion")
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w:gz") as tar:
    for root, dirs, files in os.walk(bastion_dir):
        dirs[:] = [d for d in dirs if d not in (".venv", "__pycache__")]
        for fname in files:
            if fname.endswith(".pyc"):
                continue
            full = os.path.join(root, fname)
            arcname = os.path.relpath(full, bastion_dir)
            tar.add(full, arcname=arcname)
bastion_tarball_b64 = base64.b64encode(buf.getvalue()).decode()

# --- Cloud-init ---
with open("cloud-init.yaml") as f:
    user_data = f.read().replace("__BASTION_TARBALL__", bastion_tarball_b64)

# --- Firewall ---
firewall = hcloud.Firewall(
    "bastion-fw",
    name="bastion-fw",
    rules=[
        hcloud.FirewallRuleArgs(
            direction="in",
            protocol="tcp",
            port="22",
            source_ips=["::/0"],
        ),
        hcloud.FirewallRuleArgs(
            direction="in",
            protocol="tcp",
            port="8000",
            source_ips=["::/0"],
        ),
        hcloud.FirewallRuleArgs(
            direction="in",
            protocol="icmp",
            source_ips=["::/0"],
        ),
    ],
)

# --- Server ---
server = hcloud.Server(
    "bastion",
    name="bastion",
    server_type="cpx11",
    location="hil",               # Hillsboro, Oregon (us-west)
    image="ubuntu-24.04",
    public_nets=hcloud.ServerPublicNetArgs(
        ipv4_enabled=False,
        ipv6_enabled=True,
    ),
    ssh_keys=[ssh_key.id],
    firewall_ids=[firewall.id],
    user_data=user_data,
    # no volumes
)

# --- Outputs ---
pulumi.export("server_name", server.name)
pulumi.export("ipv6_address", server.ipv6_address)
pulumi.export("ipv6_network", server.ipv6_network)
