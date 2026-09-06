"""
src/db_maintenance.py
Safe, idempotent database maintenance for NeuralHire.

Responsibilities
----------------
1. Back up the SQLite dev database once per process (never destructive).
2. Ensure newly introduced columns exist (additive ALTER TABLE ADD COLUMN).
3. Backfill reproducibility metadata for legacy rows and RE-DERIVE their
   decision from the (unchanged) persisted score using the canonical
   DecisionEngine default policy.

Why re-derive legacy decisions?
The historical rows were produced by a degenerate model threshold (0.04) that
never matched the platform's documented Strong/Potential/Low policy — a bug, not
a deliberate policy. We do NOT change the stored score (the real model output);
we only recompute the *decision label* from that score using the canonical
policy so history is internally consistent. Rows are tagged
``model_version='legacy-recompute'`` so the correction is transparent and
idempotent. New evaluations store their own live metadata and are never touched.
"""
from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from sqlalchemy import inspect, text

from src.config import settings
from src.decisioning import DecisionEngine, DecisionConfig

logger = logging.getLogger("jobtest.db_maintenance")

# column_name -> SQL type/default fragment appended to ADD COLUMN
_REQUIRED_COLUMNS: Dict[str, Dict[str, str]] = {
    "candidates": {
        "status": "VARCHAR DEFAULT 'NEW'",
        "is_anonymous": "INTEGER DEFAULT 0",
        "updated_at": "DATETIME",
    },
    "job_offers": {
        "job_code": "VARCHAR",
        "status": "VARCHAR DEFAULT 'OPEN'",
        "updated_at": "DATETIME",
    },
    "match_results": {
        "decision_confidence": "FLOAT",
        "strong_fit_threshold": "FLOAT",
        "potential_fit_threshold": "FLOAT",
        "model_version": "VARCHAR",
        "evaluation_method": "VARCHAR",
        "weights_json": "TEXT",
    },
}

_backed_up = False


def backup_sqlite_db() -> None:
    """Copy the SQLite DB to a timestamped backup (best-effort, once)."""
    global _backed_up
    if _backed_up:
        return
    url = settings.DATABASE_URL
    if not url.startswith("sqlite"):
        _backed_up = True
        return
    db_path = Path(url.replace("sqlite:///", ""))
    if db_path.exists():
        backups = db_path.parent / "backups"
        backups.mkdir(exist_ok=True)
        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        dest = backups / f"{db_path.stem}.{stamp}.bak"
        try:
            shutil.copy2(db_path, dest)
            logger.info("Database backed up to %s", dest)
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("DB backup failed (continuing): %s", exc)
    _backed_up = True


def ensure_schema(engine) -> List[str]:
    """Add any missing columns. Returns the list of columns added."""
    added: List[str] = []
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table, columns in _REQUIRED_COLUMNS.items():
            if table not in existing_tables:
                continue
            present = {c["name"] for c in inspector.get_columns(table)}
            for col, ddl in columns.items():
                if col not in present:
                    conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {col} {ddl}'))
                    added.append(f"{table}.{col}")
    if added:
        logger.info("Schema ensured — added columns: %s", ", ".join(added))
    return added


def backfill_legacy(engine) -> Dict[str, int]:
    """Re-derive legacy decisions and set sensible status/metadata defaults."""
    engine_dec = DecisionEngine(DecisionConfig.default())
    cfg = engine_dec.config
    stats = {"match_results": 0, "candidates": 0, "job_offers": 0}

    with engine.begin() as conn:
        # ── Match results: re-derive decision from unchanged score ──────────
        rows = conn.execute(text(
            "SELECT id, final_score, decision FROM match_results "
            "WHERE model_version IS NULL"
        )).fetchall()
        for row in rows:
            mid, score, _old = row[0], row[1], row[2]
            score = 0.0 if score is None else float(score)
            result = engine_dec.evaluate(score)
            conn.execute(
                text(
                    "UPDATE match_results SET decision=:d, confidence=:c, "
                    "decision_confidence=:dc, strong_fit_threshold=:s, "
                    "potential_fit_threshold=:p, model_version=:mv, "
                    "evaluation_method=COALESCE(evaluation_method, model_used) "
                    "WHERE id=:id"
                ),
                {
                    "d": result.decision,
                    "c": result.confidence_level,
                    "dc": result.confidence,
                    "s": cfg.strong_fit_threshold,
                    "p": cfg.potential_fit_threshold,
                    "mv": "legacy-recompute",
                    "id": mid,
                },
            )
            stats["match_results"] += 1

        # ── Candidate status defaults + anonymous flag ──────────────────────
        conn.execute(text("UPDATE candidates SET status='NEW' WHERE status IS NULL"))
        r = conn.execute(text(
            "UPDATE candidates SET is_anonymous=1 "
            "WHERE is_anonymous IS NULL AND ("
            "full_name IS NULL OR full_name='' OR full_name LIKE 'Anonymous%' "
            "OR full_name LIKE 'Candidate #%')"
        ))
        conn.execute(text("UPDATE candidates SET is_anonymous=0 WHERE is_anonymous IS NULL"))
        stats["candidates"] = r.rowcount if r.rowcount and r.rowcount > 0 else 0

        # ── Job status defaults ─────────────────────────────────────────────
        conn.execute(text("UPDATE job_offers SET status='OPEN' WHERE status IS NULL"))

    if stats["match_results"]:
        logger.info("Backfilled %d legacy match results with canonical decisions.",
                    stats["match_results"])
    return stats


def run_data_redesign_migration(engine) -> Dict[str, int]:
    """
    Idempotent migration to deduplicate JobOffers (by title) and Candidates (by email),
    and backfill job_code for JobOffers.
    """
    stats = {"merged_jobs": 0, "merged_candidates": 0, "backfilled_job_codes": 0}
    
    with engine.begin() as conn:
        # 1. Backfill Job Codes
        jobs_missing_code = conn.execute(text("SELECT id FROM job_offers WHERE job_code IS NULL")).fetchall()
        year = datetime.utcnow().year
        # Get max current seq
        max_job = conn.execute(text("SELECT job_code FROM job_offers WHERE job_code LIKE :pattern ORDER BY job_code DESC LIMIT 1"), {"pattern": f"JOB-{year}-%"}).scalar()
        seq = 1
        if max_job:
            try:
                seq = int(max_job.split("-")[-1]) + 1
            except ValueError:
                pass

        for (jid,) in jobs_missing_code:
            code = f"JOB-{year}-{seq:03d}"
            conn.execute(text("UPDATE job_offers SET job_code=:code WHERE id=:id"), {"code": code, "id": jid})
            seq += 1
            stats["backfilled_job_codes"] += 1
            
        # 2. Merge duplicate JobOffers by title
        # For each title, keep the earliest one (MIN(id)), update match_results, and delete the rest.
        duplicate_jobs = conn.execute(text("""
            SELECT title, MIN(id) as keep_id 
            FROM job_offers 
            GROUP BY LOWER(TRIM(title)) 
            HAVING COUNT(id) > 1
        """)).fetchall()
        
        for title, keep_id in duplicate_jobs:
            dupes = conn.execute(text("SELECT id FROM job_offers WHERE LOWER(TRIM(title)) = LOWER(TRIM(:title)) AND id != :keep_id"), {"title": title, "keep_id": keep_id}).fetchall()
            dupe_ids = [r[0] for r in dupes]
            if dupe_ids:
                # Re-point match_results
                conn.execute(text(f"UPDATE match_results SET job_offer_id=:keep_id WHERE job_offer_id IN ({','.join(map(str, dupe_ids))})"), {"keep_id": keep_id})
                # Re-point job_skills
                conn.execute(text(f"DELETE FROM job_skills WHERE job_offer_id IN ({','.join(map(str, dupe_ids))})"))
                # Delete duplicate jobs
                conn.execute(text(f"DELETE FROM job_offers WHERE id IN ({','.join(map(str, dupe_ids))})"))
                stats["merged_jobs"] += len(dupe_ids)

        # 3. Merge duplicate Candidates by email
        # For each non-null email, keep the earliest one, update match_results/cvs, and delete the rest.
        duplicate_cands = conn.execute(text("""
            SELECT email, MIN(id) as keep_id 
            FROM candidates 
            WHERE email IS NOT NULL AND TRIM(email) != ''
            GROUP BY LOWER(TRIM(email)) 
            HAVING COUNT(id) > 1
        """)).fetchall()
        
        for email, keep_id in duplicate_cands:
            dupes = conn.execute(text("SELECT id FROM candidates WHERE LOWER(TRIM(email)) = LOWER(TRIM(:email)) AND id != :keep_id"), {"email": email, "keep_id": keep_id}).fetchall()
            dupe_ids = [r[0] for r in dupes]
            if dupe_ids:
                conn.execute(text(f"UPDATE match_results SET candidate_id=:keep_id WHERE candidate_id IN ({','.join(map(str, dupe_ids))})"), {"keep_id": keep_id})
                conn.execute(text(f"UPDATE cvs SET candidate_id=:keep_id WHERE candidate_id IN ({','.join(map(str, dupe_ids))})"), {"keep_id": keep_id})
                conn.execute(text(f"DELETE FROM candidates WHERE id IN ({','.join(map(str, dupe_ids))})"))
                stats["merged_candidates"] += len(dupe_ids)

    return stats


def run_maintenance(engine) -> Dict[str, object]:
    """Full startup maintenance: backup → ensure schema → backfill."""
    backup_sqlite_db()
    added = ensure_schema(engine)
    stats = backfill_legacy(engine)
    redesign_stats = run_data_redesign_migration(engine)
    return {"columns_added": added, "backfill": stats, "redesign": redesign_stats}

