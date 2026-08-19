import argparse
import os
import sys

from .demo import AcmeAdapter
from .offices import run_operating_loop
from .server import serve
from .sdk import AdapterError, scaffold_company, validate_adapter


def main() -> None:
    parser = argparse.ArgumentParser(prog="sovrune")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="print the deterministic Acme operating loop")
    init = sub.add_parser("init", help="scaffold a Company Adapter project")
    init.add_argument("name", help="company name")
    init.add_argument("--output", "-o", default="./sovrune-company")
    init.add_argument("--provider", choices=["ollama", "openai-compatible", "anthropic", "gemini"], default="ollama")
    validate = sub.add_parser("validate", help="validate a Company Adapter without starting the server")
    validate.add_argument("adapter", nargs="?", help="module:Class or /path/adapter.py:Class")
    server = sub.add_parser("serve", help="start the command center")
    server.add_argument("--host", default=os.getenv("SOVRUNE_HOST", "127.0.0.1"))
    server.add_argument("--port", type=int, default=int(os.getenv("SOVRUNE_PORT", "8787")))
    args = parser.parse_args()
    if args.command == "demo":
        for step in run_operating_loop(AcmeAdapter().build_state()):
            print(f"{step['office']:12} {step['status']:10} {step['summary']}")
    elif args.command == "init":
        try:
            target, class_name = scaffold_company(args.name, args.output, args.provider)
        except AdapterError as error:
            parser.error(str(error))
        print(f"created Company Adapter in {target}")
        print(f"next: sovrune validate '{target / 'adapter.py'}:{class_name}'")
    elif args.command == "validate":
        try:
            print(validate_adapter(args.adapter).summary())
        except (AdapterError, ValueError) as error:
            print(f"invalid adapter: {error}", file=sys.stderr)
            raise SystemExit(1) from error
    else:
        serve(args.host, args.port)
