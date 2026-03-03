from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

@app.route("/")
def home():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alerts ORDER BY timestamp DESC")
    alerts = cursor.fetchall()

    conn.close()

    return render_template("index.html", alerts=alerts)

if __name__ == "__main__":
    app.run(debug=True)
