import sqlite3


def search(connection: sqlite3.Connection, query: str | None) -> list[dict]:
    if query is None or not query.strip():
        rows = connection.execute(
            "SELECT id, question, answer, category FROM faqs ORDER BY id"
        ).fetchall()
    else:
        # Treat %, _, and backslash as literal characters rather than LIKE wildcards.
        escaped = query.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        rows = connection.execute(
            """SELECT id, question, answer, category FROM faqs
            WHERE question LIKE ? ESCAPE '\\' OR answer LIKE ? ESCAPE '\\' ORDER BY id""",
            (pattern, pattern),
        ).fetchall()
    return [dict(row) for row in rows]

