# Summit College

A responsive college website built with Flask. The site includes an academic-program explorer, admissions inquiry form, contact form, newsletter signup, campus-life content, and an FAQ.

## Run locally

1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env`.
4. Replace `SECRET_KEY` with a long, random secret and set the five `PG*` values to your Neon connection details. Keep `PGSSLMODE=require` for Neon.
5. Start the development server with `flask --app app run`.
6. Open `http://127.0.0.1:5000`.

The app loads `.env` automatically. When `PGHOST` is configured, it connects to PostgreSQL using `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`, and `PGSSLMODE`. The three application tables are initialized on startup. If no PostgreSQL host or `DATABASE_URL` is set, the app uses a local SQLite database in Flask's `instance` directory. For security, `.env` contains credentials and should not be committed.

## Notes

- The college name, program catalog, dates, and contact details are sample content; update them in `app.py` and `templates/index.html` before publishing.
- Set `SECRET_KEY` to a long, random value for deployment and set `FLASK_DEBUG=0`. Do not use Flask's debug server in production.
- The Unsplash campus photos and Google Fonts require an internet connection.
