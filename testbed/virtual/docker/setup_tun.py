"""Single-subnet tunnel setup for the isolated Open5GS lab.

The pinned upstream entrypoint calls `python3 setup_tun.py --ip_range ...`.
Its helper creates the same interface repeatedly in a 256-iteration loop.
This replacement creates one TUN and its connected route. Experiments target
the local gateway, so no Internet NAT or host routing changes are required.
"""
import argparse
import ipaddress
import subprocess


def setup(if_name: str, ip_range: str) -> None:
    network = ipaddress.ip_network(ip_range)
    if network.version != 4 or network.prefixlen > 30:
        raise ValueError("Use an IPv4 subnet with at least two host addresses")
    gateway = str(next(network.hosts()))
    for command in (
        ["ip", "tuntap", "add", "dev", if_name, "mode", "tun"],
        ["ip", "address", "add", f"{gateway}/{network.prefixlen}", "dev", if_name],
        ["ip", "link", "set", "dev", if_name, "up"],
    ):
        subprocess.run(command, check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--if_name", default="ogstun")
    parser.add_argument("--ip_range", required=True)
    args = parser.parse_args()
    setup(args.if_name, args.ip_range)
