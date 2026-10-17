import os
import re
import sqlite3
from datetime import datetime

from flask import Flask, g, jsonify, request, send_from_directory

from summarizer import summarize

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "summaries.db")
MAX_CHARS = 300_000

app = Flask(__name__, static_folder="static", static_url_path="/static")


# ---------- database ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original TEXT NOT NULL,
                summary TEXT NOT NULL,
                selected TEXT NOT NULL,
                original_words INTEGER NOT NULL,
                summary_words INTEGER NOT NULL,
                ratio REAL NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )


def words(t):
    return len(re.findall(r"\S+", t))


def row_to_dict(r, full=True):
    d = {
        "id": r["id"],
        "summary": r["summary"],
        "original_words": r["original_words"],
        "summary_words": r["summary_words"],
        "ratio": r["ratio"],
        "created_at": r["created_at"],
        "preview": r["original"][:90].strip(),
    }
    if full:
        d["original"] = r["original"]
        d["selected"] = [int(x) for x in r["selected"].split(",") if x != ""]
    return d


# ---------- pages ----------
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


# ---------- API ----------
@app.route("/api/health")
def health():
    get_db().execute("SELECT 1")
    return jsonify(status="ok")


@app.route("/api/summarize", methods=["POST"])
def api_summarize():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    try:
        ratio = float(data.get("ratio", 0.3))
    except (TypeError, ValueError):
        return jsonify(error="Summary length must be a number."), 400
    ratio = min(max(ratio, 0.05), 0.9)

    if words(text) < 30:
        return jsonify(error="Paste at least 30 words so there is something to summarize."), 400
    if len(text) > MAX_CHARS:
        return jsonify(error="Text is too long. Keep it under 300,000 characters."), 400

    result = summarize(text, ratio=ratio)
    if not result["summary"]:
        return jsonify(error="Could not find any sentences in this text."), 422

    db = get_db()
    cur = db.execute(
        "INSERT INTO summaries (original, summary, selected, original_words, summary_words, ratio, created_at)"
        " VALUES (?,?,?,?,?,?,?)",
        (
            text,
            result["summary"],
            ",".join(map(str, result["selected"])),
            words(text),
            words(result["summary"]),
            ratio,
            datetime.now().strftime("%Y-%m-%d %H:%M"),
        ),
    )
    db.commit()
    row = db.execute("SELECT * FROM summaries WHERE id=?", (cur.lastrowid,)).fetchone()
    out = row_to_dict(row)
    out["sentences"] = [s["text"] for s in result["sentences"]]
    return jsonify(out), 201


@app.route("/api/history")
def api_history():
    rows = get_db().execute("SELECT * FROM summaries ORDER BY id DESC LIMIT 50").fetchall()
    return jsonify([row_to_dict(r, full=False) for r in rows])


@app.route("/api/history/<int:item_id>")
def api_history_item(item_id):
    row = get_db().execute("SELECT * FROM summaries WHERE id=?", (item_id,)).fetchone()
    if row is None:
        return jsonify(error="That summary no longer exists."), 404
    from summarizer import split_sentences
    out = row_to_dict(row)
    out["sentences"] = split_sentences(row["original"])
    return jsonify(out)


@app.route("/api/history/<int:item_id>", methods=["DELETE"])
def api_delete_item(item_id):
    db = get_db()
    db.execute("DELETE FROM summaries WHERE id=?", (item_id,))
    db.commit()
    return jsonify(deleted=item_id)


@app.route("/api/history", methods=["DELETE"])
def api_clear():
    db = get_db()
    db.execute("DELETE FROM summaries")
    db.commit()
    return jsonify(cleared=True)


init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=False)
