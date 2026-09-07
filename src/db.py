import sqlite3
import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "applications.db")

class Database:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    url TEXT UNIQUE NOT NULL,
                    platform TEXT NOT NULL,
                    description TEXT,
                    match_score REAL DEFAULT 0.0,
                    match_reason TEXT,
                    status TEXT DEFAULT 'DISCOVERED', -- DISCOVERED, MATCHED, REVIEW_READY, SUBMISSION_UNCONFIRMED, REJECTED, APPLYING, APPLIED, FAILED
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    applied_at TIMESTAMP
                )
            """)
            
            # Application logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS application_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER,
                    step TEXT NOT NULL,
                    log_level TEXT DEFAULT 'INFO',
                    message TEXT NOT NULL,
                    screenshot_path TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
                )
            """)
            # Older builds marked review/form-fill work as APPLIED. Keep actual
            # recorded submissions intact, but make ambiguous records honest.
            cursor.execute("""
                UPDATE jobs
                SET status = 'SUBMISSION_UNCONFIRMED', updated_at = CURRENT_TIMESTAMP
                WHERE status = 'APPLIED'
                  AND NOT EXISTS (
                    SELECT 1 FROM application_logs
                    WHERE application_logs.job_id = jobs.id
                      AND application_logs.step = 'SUBMITTED'
                  )
            """)
            conn.commit()

    def insert_job(self, job_data: Dict[str, Any]) -> Optional[int]:
        """Inserts a job posting into DB if URL doesn't exist."""
        sql = """
            INSERT INTO jobs (title, company, location, url, platform, description, match_score, match_reason, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                title=excluded.title,
                company=excluded.company,
                location=excluded.location,
                description=excluded.description,
                updated_at=CURRENT_TIMESTAMP
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (
                job_data.get("title", ""),
                job_data.get("company", ""),
                job_data.get("location", ""),
                job_data.get("url", ""),
                job_data.get("platform", "generic"),
                job_data.get("description", ""),
                job_data.get("match_score", 0.0),
                job_data.get("match_reason", ""),
                job_data.get("status", "DISCOVERED")
            ))
            conn.commit()
            return cursor.lastrowid

    def update_job_status(self, job_id: int, status: str, match_score: Optional[float] = None, match_reason: Optional[str] = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if match_score is not None and match_reason is not None:
                cursor.execute("""
                    UPDATE jobs 
                    SET status=?, match_score=?, match_reason=?, updated_at=CURRENT_TIMESTAMP 
                    WHERE id=?
                """, (status, match_score, match_reason, job_id))
            else:
                applied_clause = ", applied_at=CURRENT_TIMESTAMP" if status == "APPLIED" else ""
                cursor.execute(f"""
                    UPDATE jobs 
                    SET status=? {applied_clause}, updated_at=CURRENT_TIMESTAMP 
                    WHERE id=?
                """, (status, job_id))
            conn.commit()

    def log_step(self, job_id: int, step: str, message: str, log_level: str = "INFO", screenshot_path: Optional[str] = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO application_logs (job_id, step, log_level, message, screenshot_path)
                VALUES (?, ?, ?, ?, ?)
            """, (job_id, step, log_level, message, screenshot_path))
            conn.commit()

    def get_jobs(self, status: Optional[str] = None, min_score: Optional[float] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM jobs WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if min_score is not None:
            query += " AND match_score >= ?"
            params.append(min_score)
        query += " ORDER BY match_score DESC, created_at DESC"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_job_by_id(self, job_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_logs(self, job_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM application_logs WHERE job_id = ? ORDER BY timestamp ASC", (job_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, int]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status, COUNT(*) as cnt FROM jobs GROUP BY status")
            rows = cursor.fetchall()
            stats = {
                "DISCOVERED": 0,
                "MATCHED": 0,
                "REVIEW_READY": 0,
                "SUBMISSION_UNCONFIRMED": 0,
                "REJECTED": 0,
                "APPLYING": 0,
                "APPLIED": 0,
                "FAILED": 0,
                "TOTAL": 0
            }
            total = 0
            for r in rows:
                stats[r["status"]] = r["cnt"]
                total += r["cnt"]
            stats["TOTAL"] = total
            return stats
