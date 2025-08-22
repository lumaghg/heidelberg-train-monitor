import sqlite3
import time
from pathlib import Path

DB_PATH = Path("./tmp/ratelimit_db.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS requests (ts INTEGER)")
    conn.commit()
    conn.close()

init_db()

def acquire_slot(limit=60, window=60):
    now = int(time.time())
    conn = sqlite3.connect(DB_PATH, timeout=10, isolation_level='EXCLUSIVE')
    c = conn.cursor()
    try:
        c.execute("BEGIN EXCLUSIVE")
        # Alte Einträge löschen
        c.execute("DELETE FROM requests WHERE ts < ?", (now - window,))
        # Anzahl zählen
        c.execute("SELECT COUNT(*) FROM requests")
        count = c.fetchone()[0]
        if count >= limit:
            conn.commit()
            conn.close()
            return False
        # Slot eintragen
        c.execute("INSERT INTO requests (ts) VALUES (?)", (now,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.OperationalError:
        conn.rollback()
        conn.close()
        return False

# leave two slots for hd
def wait_for_slot(limit: int = 58, window: int = 58, sleep: int = 1):
    """
    Blockiert solange, bis ein Slot frei ist.
    Gibt eine Konsoleninfo aus, wenn gewartet werden muss.
    """
    waited = False
    while not acquire_slot(limit, window):
        if not waited:
            print(f"[RateLimit] Limit erreicht ({limit}/{window}s). Warte auf freien Slot...")
            waited = True
        time.sleep(sleep)
    if waited:
        print(f"[RateLimit] Slot frei, Request wird gesendet.")
