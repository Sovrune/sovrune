import argparse
import os

from .demo import AcmeAdapter
from .offices import run_operating_loop
from .server import serve


def main() -> None:
    parser = argparse.ArgumentParser(prog="sovrune")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="print the deterministic Acme operating loop")
    server = sub.add_parser("serve", help="start the command center")
    server.add_argument("--host", default=os.getenv("SOVRUNE_HOST", "127.0.0.1"))
    server.add_argument("--port", type=int, default=int(os.getenv("SOVRUNE_PORT", "8787")))
    args = parser.parse_args()
    if args.command == "demo":
        for step in run_operating_loop(AcmeAdapter().build_state()):
            print(f"{step['office']:12} {step['status']:10} {step['summary']}")
    else:
        serve(args.host, args.port)
