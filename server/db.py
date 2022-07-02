import sqlite3
from typing import Optional

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS USER_REQUESTS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER,
    filename STRING,
    mask TINYINT,
    temperature SMALLINT
);
"""

INSERT_CMD = """
INSERT INTO USER_REQUESTS (timestamp, filename, mask, temperature)
VALUES (?, ?, ?, ?);
"""

DB_PATH = "./esp_project.db"

class DataBase:
    def __init__(self, db_path: str = DB_PATH) -> None:
        self.conn = sqlite3.connect(db_path)
        self.migrate()

    def migrate(self) -> None:
        cur = self.conn.cursor()
        cur.execute(CREATE_TABLE)
    
    def add_new_record(self, timestamp: int, filename: str, mask: Optional[bool], temp: int) -> bool:
        cur = self.conn.cursor()
        if mask:
            mask_int = 1
        elif mask is None:
            mask_int = -1
        else:
            mask_int = 0
        try:
            cur.execute(INSERT_CMD, (timestamp, filename, mask_int, temp))
            self.conn.commit()
        except Exception:
            return False

        return True

DB = DataBase()