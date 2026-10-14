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

## Deploy to Vercel

Import the GitHub repository as a Vercel project and deploy it with the Python runtime. Vercel detects the Flask `app` in the root `app.py`. Static assets are kept in `public/static/` and are also served at `/static/` by Flask for local development.

Add `SECRET_KEY`, `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, and `PGDATABASE` under the Vercel project's **Settings → Environment Variables** for the environments you deploy to. Set `PGSSLMODE` to `require` for Neon and `FLASK_DEBUG` to `0` in production. Values in your local `.env` file are not uploaded with the repository. Redeploy after changing Vercel environment variables.

Vercel's filesystem is temporary. If PostgreSQL credentials are not configured, the site falls back to SQLite in `/tmp` so the pages can start, but form submissions will not be durable across function instances or redeploys. Configure Neon for persistent submissions. If a Neon connection fails during startup, the app logs the error and keeps the pages available; database forms retry the connection and show an error rather than reporting a failed submission as successful. Inspect the function's runtime logs in the Vercel deployment details for the underlying database error.

## Notes

- The college name, program catalog, dates, and contact details are sample content; update them in `app.py` and `templates/index.html` before publishing.
- Set `SECRET_KEY` to a long, random value for deployment and set `FLASK_DEBUG=0`. Do not use Flask's debug server in production.
- The Unsplash campus photos and Google Fonts require an internet connection.
