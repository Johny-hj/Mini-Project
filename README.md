# Course Progress Tracker

A small Flask app for tracking course progress.

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

## Deploy on Render

This repository includes `render.yaml` for a Render Blueprint deployment.

1. Push the project to GitHub.
2. In Render, choose **New > Blueprint** and connect the repository.
3. Render will create:
   - a Python web service using `gunicorn app:app`
   - a Postgres database
   - `SECRET_KEY` and `DATABASE_URL` environment variables

Python is pinned with `.python-version`.
The app creates its database tables automatically on startup.
