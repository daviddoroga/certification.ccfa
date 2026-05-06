# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python Flask REST API for a notes management system with JWT-based authentication and role-based access control. Remote: `https://github.com/daviddoroga/certification.ccfa`

## Running the App

```bash
export SECRET_KEY="your-secret-key"
python app.py
# Optional: FLASK_DEBUG=true python app.py
```

Dependencies (install manually — no requirements.txt): `flask`, `bcrypt`, `pyjwt`. `sqlite3` is built-in.

## Architecture

All application logic lives in `app.py` (single-file Flask app). SQLite database is created in-memory/local on first run.

**Database schema:**
- `users`: id, username (unique), password (bcrypt hash), role (default: `'user'`)
- `notes`: id, user_id, content

**Auth flow:** Register → Login returns a JWT (HS256, signed with `SECRET_KEY`) → include token in `Authorization: Bearer <token>` header for protected routes.

**API endpoints:**
- `POST /register` — create account
- `POST /login` — returns JWT
- `GET /notes` — list notes (optional `?id=` for single); requires auth
- `POST /notes` — create note; requires auth
- `GET /admin/users` — list all users; requires admin role
- `GET /search?q=` — search notes by content; requires auth

## Custom Claude Code Skills

Three skills live in `.claude/skills/` and are invoked via slash commands:

- `/backend-review` — security-focused review (SQL injection, auth bypass, weak hashing, IDOR, etc.)
- `/pr-description` — writes structured PR descriptions from git diff
- `/release-notes` — generates a changelog from recent git history using `.claude/skills/release-notes/assets/changelog-template.md`

The `release-notes` skill uses `.claude/skills/release-notes/scripts/get-history.sh` to extract git log before generating the document.
