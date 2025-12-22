#!/usr/bin/env python3
"""
Database Layer - SQLite for Face Recognition
=============================================
Manages persons, face samples, and events.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class Database:
    """SQLite database for face recognition system"""

    def __init__(self, db_path: str = "faces.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Dict-like access

        cursor = self.conn.cursor()

        # Person table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS person (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_merged_into INTEGER,
                FOREIGN KEY (is_merged_into) REFERENCES person(id)
            )
        """)

        # Face sample table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS face_sample (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                embedding BLOB NOT NULL,
                image_path TEXT NOT NULL,
                quality_score REAL,
                bbox TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (person_id) REFERENCES person(id) ON DELETE CASCADE
            )
        """)

        # Event table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS event (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                person_id INTEGER,
                confidence REAL,
                distance REAL,
                margin REAL,
                status TEXT,
                image_path TEXT NOT NULL,
                device_id TEXT,
                FOREIGN KEY (person_id) REFERENCES person(id)
            )
        """)

        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_person_name ON person(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_face_person ON face_sample(person_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_person ON event(person_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_timestamp ON event(timestamp DESC)")

        self.conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    # ========================================================================
    # PERSON OPERATIONS
    # ========================================================================

    def create_person(self, name: Optional[str] = None) -> int:
        """Create new person (auto-name if None)"""
        cursor = self.conn.cursor()

        if name is None:
            # Auto-generate name
            cursor.execute("SELECT COUNT(*) FROM person WHERE name LIKE 'Unbekannt #%'")
            count = cursor.fetchone()[0]
            name = f"Unbekannt #{count + 1}"

        cursor.execute(
            "INSERT INTO person (name, created_at, updated_at) VALUES (?, ?, ?)",
            (name, datetime.now(), datetime.now())
        )
        self.conn.commit()

        person_id = cursor.lastrowid
        logger.info(f"Created person: {name} (ID: {person_id})")
        return person_id

    def get_person(self, person_id: int) -> Optional[Dict]:
        """Get person by ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM person WHERE id = ? AND is_merged_into IS NULL", (person_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_persons(self, include_merged: bool = False) -> List[Dict]:
        """Get all persons"""
        cursor = self.conn.cursor()

        if include_merged:
            cursor.execute("SELECT * FROM person ORDER BY created_at DESC")
        else:
            cursor.execute("SELECT * FROM person WHERE is_merged_into IS NULL ORDER BY created_at DESC")

        return [dict(row) for row in cursor.fetchall()]

    def update_person_name(self, person_id: int, new_name: str) -> bool:
        """Update person name"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE person SET name = ?, updated_at = ? WHERE id = ?",
            (new_name, datetime.now(), person_id)
        )
        self.conn.commit()
        logger.info(f"Updated person {person_id} name to '{new_name}'")
        return cursor.rowcount > 0

    def merge_persons(self, from_id: int, into_id: int) -> bool:
        """Merge person from_id into person into_id"""
        cursor = self.conn.cursor()

        # Move all face samples
        cursor.execute(
            "UPDATE face_sample SET person_id = ? WHERE person_id = ?",
            (into_id, from_id)
        )

        # Update events
        cursor.execute(
            "UPDATE event SET person_id = ? WHERE person_id = ?",
            (into_id, from_id)
        )

        # Mark source person as merged
        cursor.execute(
            "UPDATE person SET is_merged_into = ?, updated_at = ? WHERE id = ?",
            (into_id, datetime.now(), from_id)
        )

        self.conn.commit()
        logger.info(f"Merged person {from_id} into {into_id}")
        return True

    def delete_person(self, person_id: int) -> bool:
        """Delete person and all associated data"""
        cursor = self.conn.cursor()

        # Delete face samples
        cursor.execute("DELETE FROM face_sample WHERE person_id = ?", (person_id,))

        # Delete events (or set person_id to NULL if you want to keep history)
        cursor.execute("DELETE FROM event WHERE person_id = ?", (person_id,))

        # Delete person
        cursor.execute("DELETE FROM person WHERE id = ?", (person_id,))

        self.conn.commit()
        logger.info(f"Deleted person {person_id}")
        return cursor.rowcount > 0

    # ========================================================================
    # FACE SAMPLE OPERATIONS
    # ========================================================================

    def add_face_sample(
        self,
        person_id: int,
        embedding: np.ndarray,
        image_path: str,
        quality_score: float = 0.0,
        bbox: Optional[List[int]] = None
    ) -> int:
        """Add face sample to person"""
        cursor = self.conn.cursor()

        # Convert embedding to blob
        embedding_blob = embedding.tobytes()

        # Convert bbox to JSON
        bbox_json = json.dumps(bbox) if bbox else None

        cursor.execute(
            """INSERT INTO face_sample
               (person_id, embedding, image_path, quality_score, bbox, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (person_id, embedding_blob, image_path, quality_score, bbox_json, datetime.now())
        )
        self.conn.commit()

        sample_id = cursor.lastrowid
        logger.debug(f"Added face sample {sample_id} for person {person_id}")
        return sample_id

    def get_face_samples(self, person_id: int) -> List[Dict]:
        """Get all face samples for person"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM face_sample WHERE person_id = ? ORDER BY created_at DESC",
            (person_id,)
        )

        samples = []
        for row in cursor.fetchall():
            sample = dict(row)
            # Convert blob back to numpy array
            sample['embedding'] = np.frombuffer(sample['embedding'], dtype=np.float32)
            # Parse bbox JSON
            sample['bbox'] = json.loads(sample['bbox']) if sample['bbox'] else None
            samples.append(sample)

        return samples

    def get_all_embeddings(self) -> List[Tuple[int, np.ndarray]]:
        """Get all embeddings with person_id (for matching)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT fs.person_id, fs.embedding
            FROM face_sample fs
            JOIN person p ON fs.person_id = p.id
            WHERE p.is_merged_into IS NULL
        """)

        embeddings = []
        for row in cursor.fetchall():
            person_id = row[0]
            embedding = np.frombuffer(row[1], dtype=np.float32)
            embeddings.append((person_id, embedding))

        return embeddings

    def delete_face_sample(self, sample_id: int) -> bool:
        """Delete face sample"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM face_sample WHERE id = ?", (sample_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def count_face_samples(self, person_id: int) -> int:
        """Count face samples for person"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM face_sample WHERE person_id = ?", (person_id,))
        return cursor.fetchone()[0]

    def get_oldest_face_sample(self, person_id: int) -> Optional[int]:
        """Get ID of oldest face sample (for replacement)"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id FROM face_sample WHERE person_id = ? ORDER BY created_at ASC LIMIT 1",
            (person_id,)
        )
        row = cursor.fetchone()
        return row[0] if row else None

    # ========================================================================
    # EVENT OPERATIONS
    # ========================================================================

    def create_event(
        self,
        image_path: str,
        person_id: Optional[int] = None,
        confidence: float = 0.0,
        distance: float = 999.0,
        margin: float = 0.0,
        status: str = "UNKNOWN",
        device_id: str = "ESP32-CAM"
    ) -> int:
        """Create event record"""
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO event
               (timestamp, person_id, confidence, distance, margin, status, image_path, device_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (datetime.now(), person_id, confidence, distance, margin, status, image_path, device_id)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_latest_event(self) -> Optional[Dict]:
        """Get latest event"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT e.*, p.name as person_name
            FROM event e
            LEFT JOIN person p ON e.person_id = p.id
            ORDER BY e.timestamp DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_events(self, limit: int = 50, person_id: Optional[int] = None) -> List[Dict]:
        """Get events (optionally filtered by person)"""
        cursor = self.conn.cursor()

        if person_id:
            cursor.execute("""
                SELECT e.*, p.name as person_name
                FROM event e
                LEFT JOIN person p ON e.person_id = p.id
                WHERE e.person_id = ?
                ORDER BY e.timestamp DESC
                LIMIT ?
            """, (person_id, limit))
        else:
            cursor.execute("""
                SELECT e.*, p.name as person_name
                FROM event e
                LEFT JOIN person p ON e.person_id = p.id
                ORDER BY e.timestamp DESC
                LIMIT ?
            """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def get_stats(self) -> Dict:
        """Get database statistics"""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM person WHERE is_merged_into IS NULL")
        person_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM face_sample")
        sample_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM event")
        event_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM event WHERE status = 'GREEN'")
        green_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM event WHERE status = 'YELLOW'")
        yellow_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM event WHERE status = 'UNKNOWN'")
        unknown_count = cursor.fetchone()[0]

        return {
            'total_persons': person_count,
            'total_samples': sample_count,
            'total_events': event_count,
            'green_events': green_count,
            'yellow_events': yellow_count,
            'unknown_events': unknown_count
        }

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
