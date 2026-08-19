import argparse
import os
import sys

from .demo import AcmeAdapter
from .accountability import execute_run
from .offices import run_operating_loop
from .server import serve
from .sdk import AdapterError, scaffold_company, validate_adapter
from .store import AccountabilityStore, StoreError


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
    operate = sub.add_parser("operate", help="create a durable operating run and pending approval")
    operate.add_argument("--db", default=os.getenv("SOVRUNE_DB", "./sovrune.db"))
    runs = sub.add_parser("runs", help="list durable operating runs")
    runs.add_argument("--db", default=os.getenv("SOVRUNE_DB", "./sovrune.db"))
    approvals = sub.add_parser("approvals", help="list pending approvals")
    approvals.add_argument("--db", default=os.getenv("SOVRUNE_DB", "./sovrune.db"))
    for action in ("approve", "reject"):
        command = sub.add_parser(action, help=f"{action} one pending decision")
        command.add_argument("approval_id")
        command.add_argument("--by", required=True, dest="actor")
        command.add_argument("--note", default="")
        command.add_argument("--db", default=os.getenv("SOVRUNE_DB", "./sovrune.db"))
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
    elif args.command == "operate":
        created = execute_run(validate_and_load_state(), AccountabilityStore(args.db))
        print(f"run {created['id']} awaiting approval {created['approval']['id']}")
        print(created["decision"]["title"])
    elif args.command == "runs":
        for run in AccountabilityStore(args.db).list_runs():
            print(f"{run['id']}  {run['status']:18}  {run['company']}  {run['started_at']}")
    elif args.command == "approvals":
        for approval in AccountabilityStore(args.db).list_approvals():
            print(f"{approval['id']}  {approval['company']}  {approval['title']}")
    elif args.command in {"approve", "reject"}:
        try:
            result = AccountabilityStore(args.db).resolve_approval(args.approval_id, args.command,
                                                                    args.actor, args.note)
        except StoreError as error:
            print(f"cannot {args.command}: {error}", file=sys.stderr)
            raise SystemExit(1) from error
        print(f"{result['approval']['status']}: {result['decision']['title']}")
    else:
        serve(args.host, args.port)

def validate_and_load_state():
    from .sdk import load_adapter
    state = load_adapter().build_state()
    state.validate()
    return state
