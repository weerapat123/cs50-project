from genericpath import exists
import os

from logging import root
from cs50 import SQL
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    send_from_directory,
)
from flask_session import Session

from tempfile import mkdtemp
from sqlalchemy import desc
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import uuid

from helpers import (
    apology,
    login_required,
    lookup,
    usd,
    is_password_valid,
    allowed_file,
)

UPLOAD_FOLDER = "upload"
DB_NAME = "database.db"
CATEGORIES = ["plants", "others"]

# Item process
ADD = "add"
REMOVE = "remove"

# Item status
DELETED = 0
ACTIVE = 1

MB = 1024 * 1024

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Set Upload folder
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Set maximum content length
app.config["MAX_CONTENT_LENGTH"] = 2 * MB

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
# os.urandom(24).hex()
app.config["SECRET_KEY"] = "6ddd1effd35eeee6661c299a749377d293cf9921c8143dfd"
Session(app)

# Connect to the database
db = SQL(f"sqlite:///{DB_NAME}")


def init_db():
    # Table `users`
    db.execute(
        """CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT NOT NULL,
    hash TEXT NOT NULL)"""
    )
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS username ON users (username)")

    # Table `items`
    db.execute(
        """CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    description TEXT NOT NULL,
    image_name TEXT NOT NULL,
    category TEXT NOT NULL,
    owner_id INTEGER NOT NULL,
    status INTEGER DEFAULT 1 NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES users (id))"""
    )
    db.execute("CREATE INDEX IF NOT EXISTS items_list ON items (owner_id, status)")
    db.execute("CREATE INDEX IF NOT EXISTS remove_item ON items (id, owner_id)")

    # Table `histories`
    db.execute(
        """CREATE TABLE IF NOT EXISTS histories (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    process_type TEXT NOT NULL,
    item_id INTEGER NOT NULL,
    FOREIGN KEY (item_id) REFERENCES items (id))"""
    )


def init_upload():
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# # Make sure API key is set
# if not os.environ.get("API_KEY"):
#     raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
# @login_required
def index():
    # Mock up data
    img_paths = ["plant1.jpg", "plant2.jpg", "plant3.jpg"]
    items = []
    for i, img in enumerate(img_paths):
        item = {
            "name": f"Plant {i+1}",
            "price": (100.0 * (i + 1)) - 1,
            "description": f"This is description of an item of plant {i+1}." * (i + 1),
            "image_name": img,
        }
        items.append(item)

    rows = db.execute(f"SELECT * FROM items")
    items += rows
    return render_template("index.html", items=items)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/backoffice")

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/backoffice")


# TODO: For debug. Remove later. Only manual register needed!
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 400)
        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 400)
        # Ensure password confirmation was submitted
        elif not confirmation:
            return apology("must provide password confirmation", 400)

        # if not is_password_valid(password):
        #     return apology(
        #         "password must contain at least one character, one number and one special character",
        #         400,
        #     )

        if password != confirmation:
            return apology("passwords do not match", 400)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ? LIMIT 1",
            request.form.get("username"),
        )
        # Username already exists
        if rows:
            return apology("this username was already taken", 400)

        db.execute(
            "INSERT INTO users (username, hash) VALUES(?, ?)",
            username,
            generate_password_hash(password),
        )

        return render_template("register.html", is_registered=True)

    return render_template("register.html")


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        user_id = session["user_id"]
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")

        if not current_password:
            return apology("must provide password", 400)
        elif not new_password:
            return apology("must provide new password", 400)
        elif not confirmation:
            return apology("must provide new password confirmation", 400)

        if not is_password_valid(new_password):
            return apology(
                "password must contain at least one character, one number and one special character",
                400,
            )

        if new_password != confirmation:
            return apology("new passwords do not match", 400)

        rows = db.execute("SELECT * FROM users WHERE id = ?", user_id)
        if len(rows) != 1:
            return apology("something wrong", 500)

        user = rows[0]
        if not check_password_hash(user["hash"], current_password):
            return apology("invalid password", 400)
        elif check_password_hash(user["hash"], new_password):
            return apology("new password must not match with current password", 400)

        db.execute(
            "UPDATE users SET hash = ? WHERE id = ?",
            generate_password_hash(new_password),
            user_id,
        )

        return render_template("change_password.html", is_changed=True)

    return render_template("change_password.html")


@app.route("/backoffice")
@login_required
def backoffice():
    return render_template("backoffice.html")


@app.route("/add_item", methods=["GET", "POST"])
@login_required
def add_item():
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        category = request.form.get("category")

        try:
            price = float(request.form.get("price"))
        except (ValueError, TypeError):
            return apology("invalid amount")

        if not name:
            return apology("must provide name")
        elif not description:
            return apology("must provide description")
        elif price <= 0:
            return apology("invalid price")
        elif category not in CATEGORIES:
            return apology("invalid category")
        elif "image" not in request.files:
            return apology("must provide image")

        file = request.files.get("image")

        if file.filename == "":
            flash("Image file is invalid")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            ext = file.filename.rsplit(".", 1)[-1]
            filename = f"image_{category}_{uuid.uuid4()}.{ext}"
            # filename = secure_filename(filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        user_id = session["user_id"]

        db.execute(
            """INSERT INTO items (name, price, description, image_name, category, owner_id, status)
            VALUES(?, ?, ?, ?, ?, ?, ?)""",
            name,
            price,
            description,
            filename,
            category,
            user_id,
            ACTIVE,
        )

        rows = db.execute(
            "SELECT id FROM items WHERE owner_id = ? ORDER BY id DESC LIMIT 1", user_id
        )
        item_id = rows[0]["id"]

        db.execute(
            """INSERT INTO histories (process_type, item_id)
            VALUES(?, ?)""",
            ADD,
            item_id,
        )

        flash("You have successfully added an item!")
        return render_template("add_item.html", categories=CATEGORIES)

    return render_template("add_item.html", categories=CATEGORIES)


@app.route("/uploads/<path:filename>")
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/list_items")
@login_required
def list_items():
    user_id = session["user_id"]
    items = db.execute(
        f"SELECT * FROM items WHERE owner_id = ? AND status = ?", user_id, ACTIVE
    )

    return render_template("list_items.html", items=items)


@app.route("/remove_item", methods=["POST"])
@login_required
def remove_item():
    user_id = session["user_id"]
    item_id = request.form.get("item_id")

    if not item_id:
        return apology("must provide item id")

    db.execute("BEGIN TRANSACTION")
    db.execute(
        "UPDATE items SET status = ? WHERE id = ? AND owner_id = ?",
        DELETED,
        item_id,
        user_id,
    )
    db.execute("COMMIT")

    db.execute(
        """INSERT INTO histories (process_type, item_id)
            VALUES(?, ?)""",
        REMOVE,
        item_id,
    )

    flash("You have successfully removed an item!")
    return redirect("/list_items")


if __name__ == "__main__":
    init_db()
    init_upload()
    app.run(debug=True)
