"""Bastion host on Hetzner Cloud — cpx11, us-west (Hillsboro), IPv6 only."""

import os
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
    # no volumes
)

# --- Outputs ---
pulumi.export("server_name", server.name)
pulumi.export("ipv6_address", server.ipv6_address)
pulumi.export("ipv6_network", server.ipv6_network)
