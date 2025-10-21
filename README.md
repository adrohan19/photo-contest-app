## Halloween Photo Throwdown

Gather costumes, hype the crowd, and crown superlative winners in one simple app. This project lets friends or coworkers upload Halloween photos, nominate themselves for categories, and vote for the winners live at the party.

### Features
- Two contests out of the box: **Costume Throwdown** and **The Great Pumpkin-Off** with their own routes, copy, and superlatives.
- Photo uploads with captions, email (optional), and multiple superlative categories per contest.
- Live voting with one vote per browser per category (cookies, no accounts required).
- Results dashboards that auto-refresh to show the current leaderboard.
- Mobile-friendly responsive layout with a Halloween vibe.
- SQLite for quick persistence and file storage on disk.

### Quick Start
1. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv env
   source env/bin/activate
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the server:**
   ```bash
   python app.py
   ```
   The app loads at http://localhost:5000.

The first run automatically creates `data/app.db` and ensures `uploads/` exists.

### Project Structure
- `app.py` – Flask application with HTML pages and JSON APIs.
- `database.py` – SQLite helpers and vote aggregation logic.
- `config.py` – Contest definitions, upload limits, and directory setup.
- `templates/` – Jinja pages for landing, upload, voting, and results.
- `static/` – CSS and JavaScript for client interactions.
- `uploads/` – Saved images (ignored by git, but kept on disk).
- `data/app.db` – SQLite database file (auto-generated).

### Contests & Categories
- Costume pages live at `/upload`, `/vote`, `/results` (or `/costumes/...`).
- Pumpkin pages live at `/pumpkins/upload`, `/pumpkins/vote`, `/pumpkins/results`.
- Edit `config.CONTESTS` in `config.py` to rename contests, tweak copy, or adjust category lists. Each category needs a unique `id` and a `label`.
- Restart the server after changes so templates and APIs pick up the new configuration.

### Managing Data
- Clear all submissions: stop the server, delete `data/app.db` and everything in `uploads/`, then restart.
- Increase file size limit: adjust `MAX_CONTENT_LENGTH` in `config.py` (bytes).
- Expand allowed image types: update `ALLOWED_EXTENSIONS` in `config.py`.

### Deployment (Render / Heroku-style)
The repository includes a `Procfile` and `runtime.txt` for PaaS platforms.

1. Commit the project to your repo.
2. Deploy with a service such as Render, Railway, or Heroku (via Docker/Buildpacks).
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
3. Attach a persistent disk and mount it to `/opt/render/project/src/uploads` and `/opt/render/project/src/data` (or the equivalent path on your platform) so images and the database survive restarts.
4. Configure HTTPS, share the public URL with your guests, and you’re ready.

> **Note:** If you plan to host uploads long-term, consider using cloud storage (S3, GCS, etc.) and switching `config.UPLOAD_DIR` to point to that mount.

### Testing / Verification
No automated tests are included yet. You can sanity-check the APIs with:
```bash
python3 -m compileall app.py database.py config.py
```
Then run the server, upload a sample photo, and confirm voting and results behave as expected.

### Next Ideas
- Add admin authentication to moderate entries.
- Email notifications when someone wins a category.
- Downloadable photo gallery or carousel for party displays.
- Export votes as CSV after the event.
