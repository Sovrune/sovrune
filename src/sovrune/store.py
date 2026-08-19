"""SQLite accountability store for Community Edition."""
from __future__ import annotations
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

SCHEMA_VERSION = 1

def now() -> str:
    return datetime.now(UTC).isoformat()

class StoreError(RuntimeError):
    pass

class AccountabilityStore:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or os.getenv("SOVRUNE_DB", "./sovrune.db")).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.migrate()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def migrate(self) -> None:
        with self.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS operating_run (
                    id TEXT PRIMARY KEY, company TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('awaiting_approval','approved','rejected','completed','failed')),
                    confidence REAL NOT NULL, state_json TEXT NOT NULL,
                    started_at TEXT NOT NULL, completed_at TEXT
                );
                CREATE TABLE IF NOT EXISTS artifact (
                    id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES operating_run(id),
                    office TEXT NOT NULL, kind TEXT NOT NULL, status TEXT NOT NULL,
                    summary TEXT NOT NULL, payload_json TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS decision (
                    id TEXT PRIMARY KEY, run_id TEXT NOT NULL UNIQUE REFERENCES operating_run(id),
                    title TEXT NOT NULL, rationale TEXT NOT NULL, evidence_json TEXT NOT NULL,
                    expected_outcome TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('proposed','approved','rejected')),
                    created_at TEXT NOT NULL, resolved_at TEXT
                );
                CREATE TABLE IF NOT EXISTS approval (
                    id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES operating_run(id),
                    decision_id TEXT NOT NULL UNIQUE REFERENCES decision(id),
                    status TEXT NOT NULL CHECK(status IN ('pending','approved','rejected')),
                    requested_at TEXT NOT NULL, resolved_at TEXT, resolved_by TEXT, note TEXT
                );
                CREATE TABLE IF NOT EXISTS prediction (
                    id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES operating_run(id),
                    decision_id TEXT NOT NULL UNIQUE REFERENCES decision(id),
                    metric TEXT NOT NULL, baseline REAL, target REAL, unit TEXT NOT NULL,
                    window_opens TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('pending_approval','open','cancelled','graded')),
                    actual REAL, verdict TEXT, created_at TEXT NOT NULL, graded_at TEXT
                );
                CREATE INDEX IF NOT EXISTS artifact_run_idx ON artifact(run_id, created_at);
                CREATE INDEX IF NOT EXISTS approval_status_idx ON approval(status, requested_at);
                CREATE INDEX IF NOT EXISTS prediction_status_idx ON prediction(status, window_opens);
            """)
            db.execute("INSERT OR IGNORE INTO schema_version(version, applied_at) VALUES (?, ?)",
                       (SCHEMA_VERSION, now()))

    @staticmethod
    def _decode(row: sqlite3.Row | None, *json_fields: str) -> dict[str, Any] | None:
        if row is None:
            return None
        data = dict(row)
        for field in json_fields:
            data[field.removesuffix("_json")] = json.loads(data.pop(field))
        return data

    def create_run(self, run: dict[str, Any], artifacts: list[dict[str, Any]], decision: dict[str, Any],
                   approval: dict[str, Any], prediction: dict[str, Any]) -> None:
        with self.connection() as db:
            db.execute("INSERT INTO operating_run VALUES (?,?,?,?,?,?,?)", (
                run["id"], run["company"], run["status"], run["confidence"],
                json.dumps(run["state"], separators=(",", ":")), run["started_at"], None))
            db.executemany("INSERT INTO artifact VALUES (?,?,?,?,?,?,?,?)", [(
                a["id"], run["id"], a["office"], a["kind"], a["status"], a["summary"],
                json.dumps(a["payload"], separators=(",", ":")), a["created_at"]) for a in artifacts])
            db.execute("INSERT INTO decision VALUES (?,?,?,?,?,?,?,?,?)", (
                decision["id"], run["id"], decision["title"], decision["rationale"],
                json.dumps(decision["evidence"], separators=(",", ":")),
                decision["expected_outcome"], decision["status"], decision["created_at"], None))
            db.execute("INSERT INTO approval VALUES (?,?,?,?,?,?,?,?)", (
                approval["id"], run["id"], decision["id"], approval["status"],
                approval["requested_at"], None, None, None))
            db.execute("INSERT INTO prediction VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                prediction["id"], run["id"], decision["id"], prediction["metric"],
                prediction["baseline"], prediction["target"], prediction["unit"],
                prediction["window_opens"], prediction["status"], None, None,
                prediction["created_at"], None))

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connection() as db:
            rows = db.execute("SELECT id,company,status,confidence,started_at,completed_at FROM operating_run ORDER BY started_at DESC LIMIT ?", (max(1, min(limit, 200)),)).fetchall()
        return [dict(row) for row in rows]

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self.connection() as db:
            run = self._decode(db.execute("SELECT * FROM operating_run WHERE id=?", (run_id,)).fetchone(), "state_json")
            if not run:
                return None
            artifacts = [self._decode(row, "payload_json") for row in db.execute("SELECT * FROM artifact WHERE run_id=? ORDER BY created_at,id", (run_id,)).fetchall()]
            decision = self._decode(db.execute("SELECT * FROM decision WHERE run_id=?", (run_id,)).fetchone(), "evidence_json")
            approval = self._decode(db.execute("SELECT * FROM approval WHERE run_id=?", (run_id,)).fetchone())
            prediction = self._decode(db.execute("SELECT * FROM prediction WHERE run_id=?", (run_id,)).fetchone())
        return {**run, "artifacts": artifacts, "decision": decision, "approval": approval, "prediction": prediction}

    def list_approvals(self, status: str | None = "pending") -> list[dict[str, Any]]:
        query = "SELECT a.*,d.title,d.expected_outcome,r.company FROM approval a JOIN decision d ON d.id=a.decision_id JOIN operating_run r ON r.id=a.run_id"
        params: tuple[Any, ...] = ()
        if status:
            query += " WHERE a.status=?"
            params = (status,)
        query += " ORDER BY a.requested_at DESC"
        with self.connection() as db:
            return [dict(row) for row in db.execute(query, params).fetchall()]

    def resolve_approval(self, approval_id: str, action: str, actor: str, note: str = "") -> dict[str, Any]:
        if action not in {"approve", "reject"}:
            raise StoreError("action must be approve or reject")
        if not actor.strip():
            raise StoreError("actor is required")
        terminal = "approved" if action == "approve" else "rejected"
        prediction = "open" if action == "approve" else "cancelled"
        resolved = now()
        with self.connection() as db:
            row = db.execute("SELECT run_id,decision_id,status FROM approval WHERE id=?", (approval_id,)).fetchone()
            if not row:
                raise StoreError(f"approval not found: {approval_id}")
            if row["status"] != "pending":
                raise StoreError(f"approval is already {row['status']}")
            changed = db.execute("UPDATE approval SET status=?,resolved_at=?,resolved_by=?,note=? WHERE id=? AND status='pending'", (terminal, resolved, actor.strip(), note.strip(), approval_id)).rowcount
            if changed != 1:
                raise StoreError("approval changed concurrently")
            db.execute("UPDATE decision SET status=?,resolved_at=? WHERE id=?", (terminal, resolved, row["decision_id"]))
            db.execute("UPDATE prediction SET status=? WHERE decision_id=?", (prediction, row["decision_id"]))
            db.execute("UPDATE operating_run SET status=?,completed_at=? WHERE id=?", (terminal, resolved, row["run_id"]))
        result = self.get_run(row["run_id"])
        assert result is not None
        return result
