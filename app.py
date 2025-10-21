import json
from pathlib import Path
from typing import Dict, List
from uuid import uuid4

from flask import (
    Flask,
    abort,
    jsonify,
    make_response,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

import config
import database

config.ensure_directories()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
app.config["UPLOAD_FOLDER"] = str(config.UPLOAD_DIR)

with app.app_context():
    database.init_db()


@app.context_processor
def inject_site_contests():
    return {
        "site_contests": config.all_contests(),
        "default_contest_slug": config.DEFAULT_CONTEST,
    }


@app.teardown_appcontext
def shutdown(_: object) -> None:
    database.close_connection()


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS


def resolve_contest(slug: str) -> Dict:
    try:
        return config.get_contest(slug)
    except KeyError:
        abort(404)


@app.route("/")
def index() -> str:
    contests = config.all_contests()
    default_contest = resolve_contest(config.DEFAULT_CONTEST)
    pumpkin_contest = next((contest for contest in contests if contest["slug"] == "pumpkins"), None)
    return render_template(
        "index.html",
        contests=contests,
        default_contest=default_contest,
        pumpkin_contest=pumpkin_contest,
    )


def render_upload(contest_slug: str) -> str:
    contest = resolve_contest(contest_slug)
    return render_template("upload.html", contest=contest)


@app.route("/upload")
def upload_page_default() -> str:
    return render_upload(config.DEFAULT_CONTEST)


@app.route("/<contest_slug>/upload")
def upload_page(contest_slug: str) -> str:
    return render_upload(contest_slug)


def render_vote(contest_slug: str) -> str:
    contest = resolve_contest(contest_slug)
    return render_template("vote.html", contest=contest)


@app.route("/vote")
def vote_page_default() -> str:
    return render_vote(config.DEFAULT_CONTEST)


@app.route("/<contest_slug>/vote")
def vote_page(contest_slug: str) -> str:
    return render_vote(contest_slug)


def render_results(contest_slug: str) -> str:
    contest = resolve_contest(contest_slug)
    return render_template("results.html", contest=contest)


@app.route("/results")
def results_page_default() -> str:
    return render_results(config.DEFAULT_CONTEST)


@app.route("/<contest_slug>/results")
def results_page(contest_slug: str) -> str:
    return render_results(contest_slug)


@app.route("/uploads/<path:filename>")
def uploaded_file(filename: str):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.get("/api/categories")
def get_categories():
    contest_slug = request.args.get("contest", config.DEFAULT_CONTEST)
    contest = resolve_contest(contest_slug)
    return jsonify(contest["categories"])


@app.get("/api/photos")
def api_photos():
    contest_slug = request.args.get("contest", config.DEFAULT_CONTEST)
    contest = resolve_contest(contest_slug)

    photos = database.fetch_photos(contest_slug)
    vote_summary = database.aggregate_votes()

    for photo in photos:
        photo_votes: Dict[str, int] = {}
        for category in photo["categories"]:
            category_votes = vote_summary.get(category, [])
            vote_count = next(
                (entry["votes"] for entry in category_votes if entry["photo_id"] == photo["id"]),
                0,
            )
            photo_votes[category] = vote_count

        photo["votes"] = photo_votes
        photo["image_url"] = url_for("uploaded_file", filename=photo["filename"])

    return jsonify(
        {
            "photos": photos,
            "categories": contest["categories"],
            "contest": contest,
        }
    )


@app.get("/api/results")
def api_results():
    contest_slug = request.args.get("contest", config.DEFAULT_CONTEST)
    contest = resolve_contest(contest_slug)

    photos = database.fetch_photos(contest_slug)
    vote_summary = database.aggregate_votes()
    photos_by_id = {photo["id"]: photo for photo in photos}

    results: Dict[str, List[Dict[str, object]]] = {}
    for category in (c["id"] for c in contest["categories"]):
        category_votes = vote_summary.get(category, [])
        entries = []
        for entry in category_votes:
            photo = photos_by_id.get(entry["photo_id"])
            if not photo:
                continue
            entries.append(
                {
                    "photo_id": photo["id"],
                    "uploader_name": photo["uploader_name"],
                    "caption": photo["caption"],
                    "image_url": url_for("uploaded_file", filename=photo["filename"]),
                    "votes": entry["votes"],
                }
            )
        entries.sort(key=lambda record: record["votes"], reverse=True)
        results[category] = entries

    return jsonify({"results": results, "contest": contest})


@app.post("/api/photos")
def create_photo():
    contest_slug = request.form.get("contest", config.DEFAULT_CONTEST)
    try:
        contest = config.get_contest(contest_slug)
    except KeyError:
        return jsonify({"error": "Unknown contest. Please refresh the page."}), 400

    uploader_name = request.form.get("uploader_name", "").strip()
    email = request.form.get("email", "").strip() or None
    caption = request.form.get("caption", "").strip() or None

    if not uploader_name:
        return jsonify({"error": "Please include a name so we know who to cheer for!"}), 400

    raw_categories = request.form.getlist("categories")
    if not raw_categories and "categories" in request.form:
        try:
            raw_categories = json.loads(request.form["categories"])
        except json.JSONDecodeError:
            raw_categories = []

    categories = sorted(set(raw_categories))
    valid_category_ids = config.contest_category_ids(contest_slug)
    if not categories:
        return jsonify({"error": "Pick at least one superlative to enter."}), 400
    if not set(categories).issubset(valid_category_ids):
        return jsonify({"error": "One or more selected superlatives are not valid."}), 400

    file_storage = request.files.get("photo")
    if file_storage is None or file_storage.filename == "":
        return jsonify({"error": "Please attach a photo to your submission."}), 400

    if not allowed_file(file_storage.filename):
        return jsonify({"error": "Only png, jpg, jpeg, and gif files are allowed."}), 400

    original_name = secure_filename(file_storage.filename)
    file_extension = Path(original_name).suffix.lower()
    unique_name = f"{uuid4().hex}{file_extension}"
    destination = Path(app.config["UPLOAD_FOLDER"]) / unique_name
    file_storage.save(destination)

    photo_id = database.add_photo(
        uploader_name=uploader_name,
        email=email,
        caption=caption,
        categories=categories,
        filename=unique_name,
        contest=contest_slug,
    )

    return jsonify(
        {
            "id": photo_id,
            "message": "Photo submitted! Share the voting page so the hype begins.",
        }
    )


@app.post("/api/votes")
def create_vote():
    payload = request.get_json(silent=True) or {}
    category = payload.get("category")
    photo_id = payload.get("photo_id")

    valid_category_ids = config.all_category_ids()
    if category not in valid_category_ids:
        return jsonify({"error": "Unknown superlative. Refresh and try again."}), 400

    try:
        photo_id = int(photo_id)
    except (TypeError, ValueError):
        return jsonify({"error": "Pick a photo before submitting your vote."}), 400

    photo = database.fetch_photo(photo_id)
    if photo is None:
        return jsonify({"error": "That photo disappeared. Try another!"}), 404

    if category not in photo["categories"]:
        return jsonify({"error": "This photo is not competing in that superlative."}), 400

    contest_slug = photo["contest"]

    voter_token = request.cookies.get("voter_token")
    token_created = False
    if not voter_token:
        voter_token = uuid4().hex
        token_created = True

    database.record_vote(photo_id=photo_id, category=category, voter_token=voter_token)

    response_data = {
        "message": "Thanks for voting!",
        "category": category,
        "photo_id": photo_id,
        "contest": contest_slug,
    }

    response = make_response(jsonify(response_data))
    if token_created:
        response.set_cookie(
            "voter_token",
            voter_token,
            max_age=60 * 60 * 24 * 365,
            samesite="Lax",
            httponly=True,
        )

    return response


@app.get("/healthz")
def healthcheck():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
