import hmac
import logging
import os
import re
import secrets
import sqlite3
import tempfile
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, current_app, flash, jsonify, redirect, render_template, request, session, url_for

load_dotenv()

PROGRAMS = [
    {"name": "Computer Science", "school": "School of Technology", "level": "Undergraduate", "duration": "4 years", "icon": "⌘", "description": "Build intelligent systems, software, and the ideas that shape our digital future."},
    {"name": "Environmental Studies", "school": "School of Arts & Sciences", "level": "Undergraduate", "duration": "4 years", "icon": "↗", "description": "Turn your concern for the planet into practical, lasting environmental change."},
    {"name": "Business & Innovation", "school": "School of Business", "level": "Undergraduate", "duration": "4 years", "icon": "◈", "description": "Learn to lead with purpose, think entrepreneurially, and make good ideas happen."},
    {"name": "Psychology", "school": "School of Arts & Sciences", "level": "Undergraduate", "duration": "4 years", "icon": "◎", "description": "Explore the mind and human behavior through research, empathy, and discovery."},
    {"name": "Data Science", "school": "School of Technology", "level": "Graduate", "duration": "2 years", "icon": "⌁", "description": "Find the signal in complex data and turn evidence into meaningful decisions."},
    {"name": "Public Health", "school": "School of Health", "level": "Graduate", "duration": "2 years", "icon": "✳", "description": "Improve health outcomes by understanding communities, policy, and prevention."},
    {"name": "Creative Writing", "school": "School of Arts & Sciences", "level": "Undergraduate", "duration": "4 years", "icon": "✎", "description": "Find your voice, sharpen your craft, and bring original stories into the world."},
    {"name": "Sustainable Design", "school": "School of Technology", "level": "Graduate", "duration": "2 years", "icon": "⌂", "description": "Design thoughtful places and products for a more sustainable everyday life."},
]

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VALID_TERMS = {"Fall 2027", "Spring 2028"}


def create_app(test_config=None):
    app = Flask(
        __name__,
        static_folder="public/static",
        static_url_path="/static",
        instance_relative_config=True,
    )
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY") or secrets.token_hex(32),
        DATABASE_URL=os.getenv("DATABASE_URL", "").strip(),
        PGHOST=os.getenv("PGHOST", "").strip(),
        PGPORT=os.getenv("PGPORT", "5432").strip(),
        PGUSER=os.getenv("PGUSER", "").strip(),
        PGPASSWORD=os.getenv("PGPASSWORD", ""),
        PGDATABASE=os.getenv("PGDATABASE", "").strip(),
        PGSSLMODE=os.getenv("PGSSLMODE", "require").strip(),
        DATABASE_PATH=os.getenv("DATABASE_PATH", ""),
        DEBUG=os.getenv("FLASK_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"},
        MAX_CONTENT_LENGTH=1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    if not app.config["DATABASE_PATH"]:
        if os.getenv("VERCEL"):
            app.config["DATABASE_PATH"] = str(Path(tempfile.gettempdir()) / "college.db")
        else:
            Path(app.instance_path).mkdir(parents=True, exist_ok=True)
            app.config["DATABASE_PATH"] = str(Path(app.instance_path) / "college.db")
    try:
        initialize_database(app)
        app.extensions["college_database_initialized"] = True
    except Exception:
        if not os.getenv("VERCEL"):
            raise
        app.extensions["college_database_initialized"] = False
        app.logger.exception(
            "Database initialization failed on Vercel; database-backed forms will retry when submitted"
        )

    @app.before_request
    def protect_forms():
        if request.method == "POST":
            submitted_token = request.form.get("csrf_token", "")
            session_token = session.get("csrf_token", "")
            if not session_token or not hmac.compare_digest(submitted_token, session_token):
                abort(400, description="The form expired or could not be verified. Please refresh and try again.")

    @app.get("/")
    def home():
        session.setdefault("csrf_token", secrets.token_urlsafe(32))
        return render_template(
            "index.html",
            programs=PROGRAMS,
            csrf_token=session["csrf_token"],
            year=date.today().year,
        )

    @app.get("/api/programs")
    def list_programs():
        search = request.args.get("q", "").strip().casefold()
        level = request.args.get("level", "").strip().casefold()
        matches = [
            program for program in PROGRAMS
            if (not search or search in " ".join(program.values()).casefold())
            and (not level or level == "all" or program["level"].casefold() == level)
        ]
        return jsonify(matches)

    @app.post("/apply")
    def apply():
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        program = request.form.get("program", "").strip()
        term = request.form.get("term", "").strip()

        if not full_name or len(full_name) > 120 or not EMAIL_PATTERN.match(email) or len(email) > 254:
            flash("Please enter your name and a valid email address.", "error")
        elif len(phone) > 40 or program not in {item["name"] for item in PROGRAMS} or term not in VALID_TERMS:
            flash("Please check your program, entry term, and phone number.", "error")
        else:
            try:
                execute(
                    app,
                    "INSERT INTO applications (full_name, email, phone, program, term) VALUES (?, ?, ?, ?, ?)",
                    (full_name, email, phone, program, term),
                )
                flash("Your application inquiry is in! Our admissions team will be in touch shortly.", "success")
            except Exception:
                current_app.logger.exception("Unable to save an application inquiry")
                flash("We couldn't save your inquiry right now. Please try again in a little while.", "error")
        return redirect(url_for("home") + "#admissions")

    @app.post("/contact")
    def contact():
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if not full_name or len(full_name) > 120 or not EMAIL_PATTERN.match(email) or len(email) > 254:
            flash("Please enter your name and a valid email address.", "error")
        elif not subject or len(subject) > 160 or not message or len(message) > 5000:
            flash("Please add a subject and a message (up to 5,000 characters).", "error")
        else:
            try:
                execute(
                    app,
                    "INSERT INTO contact_messages (full_name, email, subject, message) VALUES (?, ?, ?, ?)",
                    (full_name, email, subject, message),
                )
                flash("Thanks for reaching out. The right person on campus will get back to you soon.", "success")
            except Exception:
                current_app.logger.exception("Unable to save a contact message")
                flash("We couldn't send your message right now. Please try again in a little while.", "error")
        return redirect(url_for("home") + "#contact")

    @app.post("/newsletter")
    def newsletter():
        email = request.form.get("email", "").strip().lower()
        if not EMAIL_PATTERN.match(email) or len(email) > 254:
            flash("Please enter a valid email address.", "error")
        else:
            try:
                inserted = execute(
                    app,
                    "INSERT INTO newsletter_subscribers (email) VALUES (?) ON CONFLICT (email) DO NOTHING",
                    (email,),
                )
                flash(
                    "You're on the list. Watch your inbox for Summit College news!"
                    if inserted else "You're already subscribed. Thanks for staying connected!",
                    "success",
                )
            except Exception:
                current_app.logger.exception("Unable to save a newsletter subscription")
                flash("We couldn't subscribe you right now. Please try again in a little while.", "error")
        return redirect(url_for("home") + "#newsletter")

    return app


def initialize_database(app):
    connection, postgres = connect_database(app)
    id_column = "SERIAL PRIMARY KEY" if postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
    statements = [
        f"""CREATE TABLE IF NOT EXISTS applications (
            id {id_column},
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL DEFAULT '',
            program TEXT NOT NULL,
            term TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS contact_messages (
            id {id_column},
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS newsletter_subscribers (
            id {id_column},
            email TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""",
    ]
    try:
        cursor = connection.cursor()
        for statement in statements:
            cursor.execute(statement)
        connection.commit()
    except Exception:
        connection.rollback()
        app.logger.exception("Unable to initialize the application database")
        raise
    finally:
        connection.close()


def execute(app, query, parameters):
    if not app.extensions.get("college_database_initialized", False):
        initialize_database(app)
        app.extensions["college_database_initialized"] = True
    connection, postgres = connect_database(app)
    if postgres:
        query = query.replace("?", "%s")
    try:
        cursor = connection.cursor()
        cursor.execute(query, parameters)
        inserted = cursor.rowcount > 0
        connection.commit()
        return inserted
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def connect_database(app):
    if app.config["DATABASE_URL"]:
        import psycopg2

        return psycopg2.connect(app.config["DATABASE_URL"]), True

    if app.config["PGHOST"]:
        required = ("PGHOST", "PGUSER", "PGPASSWORD", "PGDATABASE")
        missing = [name for name in required if not app.config[name]]
        if missing:
            raise ValueError(f"Missing PostgreSQL environment settings: {', '.join(missing)}")
        try:
            port = int(app.config["PGPORT"])
        except ValueError as error:
            raise ValueError("PGPORT must be a valid port number") from error
        if not 1 <= port <= 65535:
            raise ValueError("PGPORT must be between 1 and 65535")

        import psycopg2

        return psycopg2.connect(
            host=app.config["PGHOST"],
            port=port,
            user=app.config["PGUSER"],
            password=app.config["PGPASSWORD"],
            dbname=app.config["PGDATABASE"],
            sslmode=app.config["PGSSLMODE"],
        ), True

    return sqlite3.connect(app.config["DATABASE_PATH"]), False


app = create_app()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(debug=app.config["DEBUG"])
