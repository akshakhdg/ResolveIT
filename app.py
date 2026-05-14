import sqlite3
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

def get_db_connection():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    return connection

def create_table():
    connection = get_db_connection()
    connection.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requester_name TEXT NOT NULL,
            email TEXT NOT NULL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Open',
            resolution_note TEXT
        )
    """)

    try:
        connection.execute("ALTER TABLE tickets ADD COLUMN resolution_note TEXT")
    except sqlite3.OperationalError:
        pass

    connection.commit()
    connection.close()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    search = request.args.get("search", "")
    status_filter = request.args.get("status", "")
    priority_filter = request.args.get("priority", "")

    connection = get_db_connection()

    query = "SELECT * FROM tickets WHERE 1=1"
    params = []

    if search:
        query += " AND requester_name LIKE ?"
        params.append(f"%{search}%")

    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)

    if priority_filter:
        query += " AND priority = ?"
        params.append(priority_filter)

    tickets = connection.execute(query, params).fetchall()

    total_tickets = connection.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
    open_tickets = connection.execute("SELECT COUNT(*) FROM tickets WHERE status = 'Open'").fetchone()[0]
    in_progress_tickets = connection.execute("SELECT COUNT(*) FROM tickets WHERE status = 'In Progress'").fetchone()[0]
    resolved_tickets = connection.execute("SELECT COUNT(*) FROM tickets WHERE status = 'Resolved'").fetchone()[0]
    urgent_tickets = connection.execute("SELECT COUNT(*) FROM tickets WHERE priority = 'Urgent'").fetchone()[0]

    connection.close()

    return render_template(
        "dashboard.html",
        tickets=tickets,
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        in_progress_tickets=in_progress_tickets,
        resolved_tickets=resolved_tickets,
        urgent_tickets=urgent_tickets,
        search=search,
        status_filter=status_filter,
        priority_filter=priority_filter
    )

@app.route("/ticket/<int:ticket_id>/update", methods=["POST"])
def update_ticket(ticket_id):
    status = request.form["status"]
    resolution_note = request.form["resolution_note"]

    connection = get_db_connection()
    connection.execute(
        "UPDATE tickets SET status = ?, resolution_note = ? WHERE id = ?",
        (status, resolution_note, ticket_id)
    )
    connection.commit()
    connection.close()

    return redirect(f"/ticket/{ticket_id}")

@app.route("/ticket/<int:ticket_id>/delete", methods=["POST"])
def delete_ticket(ticket_id):
    connection = get_db_connection()
    connection.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
    connection.commit()
    connection.close()

    return redirect("/dashboard")

@app.route("/submit", methods=["GET", "POST"])

def submit_ticket():
    if request.method == "POST":
        requester_name = request.form["requester_name"]
        email = request.form["email"]
        category = request.form["category"]
        priority = request.form["priority"]
        description = request.form["description"]

        connection = get_db_connection()
        connection.execute(
            "INSERT INTO tickets (requester_name, email, category, priority, description) VALUES (?, ?, ?, ?, ?)",
            (requester_name, email, category, priority, description)
        )
        connection.commit()
        connection.close()

        return redirect("/")

    return render_template("submit_ticket.html")

if __name__ == "__main__":
    create_table()
    app.run(debug=True, port=5001)