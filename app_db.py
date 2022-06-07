import sqlite3


class Database:
    def __init__(self, db_name="database.db"):
        db = sqlite3.connect(db_name)

        db.execute(
            """CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
    username TEXT NOT NULL, 
    hash TEXT NOT NULL)"""
        )

        self.db = db

    def get_connection(self):
        return self.db
