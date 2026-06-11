import sqlite3
from datetime import datetime

DB = "schedule.db"

def save_events(events):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            artist TEXT,
            title TEXT,
            date TEXT,
            place TEXT,
            url TEXT,
            source TEXT,
            created_at TEXT
        )
    """)

    cur.execute("DELETE FROM schedules")

    for e in events:
        cur.execute("""
            INSERT INTO schedules VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            e["artist"],
            e["title"],
            e["date"].strftime("%Y-%m-%d") if e["date"] else None,
            e["place"],
            e["url"],
            e["source"],
            datetime.now().isoformat()
        ))

    conn.commit()
    conn.close()

def load_events():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT artist, title, date, place, url, source
        FROM schedules
        ORDER BY date ASC
    """)

    rows = cur.fetchall()
    conn.close()

    events = []
    for r in rows:
        events.append({
            "artist": r[0],
            "title": r[1],
            "date": r[2],
            "place": r[3],
            "url": r[4],
            "source": r[5],
        })

    return events
