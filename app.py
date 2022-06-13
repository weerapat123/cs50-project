from genericpath import exists
import os
import math

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

from werkzeug.security import check_password_hash, generate_password_hash
import uuid

from helpers import (
    apology,
    login_required,
    usd,
    is_password_valid,
    allowed_file,
)

UPLOAD_FOLDER = "upload"
DB_NAME = "database.db"
CATEGORIES = ["plants", "others", "food", "pets"]
CATEGORIES.sort()
# Item process
ADD = "add"
REMOVE = "remove"

# Item status
DELETED = 0
ACTIVE = 1

# Keys
cart_key = "cart_item"

# Pagination
data_per_page = 9

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
    sold_number INTEGER DEFAULT 0 NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES users (id))"""
    )
    db.execute("CREATE INDEX IF NOT EXISTS items_list ON items (owner_id, status)")
    db.execute("CREATE INDEX IF NOT EXISTS remove_item ON items (id, owner_id)")

    # Table `histories`
    db.execute(
        """CREATE TABLE IF NOT EXISTS histories (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    process_type TEXT NOT NULL,
    process_datetime TEXT NOT NULL,
    item_id INTEGER NOT NULL,
    FOREIGN KEY (item_id) REFERENCES items (id))"""
    )


def init_upload():
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.before_request
def log_request_info():
    if request.method == "POST":
        app.logger.debug('request body: %s', request.get_data())

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
    try:
        page = int(request.args.get("page"))
    except Exception as e:
        page = 1

    if page is None or page < 1:
        page = 1

    items = db.execute(
        "SELECT * FROM items LIMIT ? OFFSET ?",
        data_per_page,
        (page - 1) * data_per_page,
    )

    total_rows = db.execute("SELECT COUNT(*) as total FROM items")
    total_page = math.ceil(total_rows[0]["total"] / 12)
    pagination = {"current_page": page, "total_page": total_page}
    return render_template("index.html", items=items, pagination=pagination)


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
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


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

        return redirect("/login")

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


@app.route("/backoffice/add_item", methods=["GET", "POST"])
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
            """INSERT INTO histories (process_type, process_datetime, item_id)
            VALUES(?, datetime('now', 'localtime'), ?)""",
            ADD,
            item_id,
        )

        flash("You have successfully added an item!")
        return render_template("add_item.html", categories=CATEGORIES)

    return render_template("add_item.html", categories=CATEGORIES)


@app.route("/uploads/<path:filename>")
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/backoffice/list_items")
@login_required
def list_items():

    items = db.execute(
        f"SELECT * FROM items WHERE owner_id = ? AND status = ?",
        session["user_id"],
        ACTIVE,
    )

    return render_template("list_items.html", items=items)


@app.route("/backoffice/remove_item", methods=["POST"])
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
        """INSERT INTO histories (process_type, process_datetime, item_id)
            VALUES(?, datetime('now', 'localtime'), ?)""",
        REMOVE,
        item_id,
    )

    flash("You have successfully removed an item!")
    return redirect("/list_items")


@app.route("/backoffice/history")
@login_required
def history():

    items = db.execute(
        f"""SELECT htr.process_type, htr.process_datetime, items.name, items.price, items.description, items.image_name, items.category
        FROM histories AS htr 
        JOIN items ON items.id = htr.item_id 
        WHERE owner_id = ?""",
        session["user_id"],
    )

    return render_template("history.html", items=items)


@app.route("/add_to_cart", methods=["POST"])
@login_required
def add_to_cart():
    try:
        item_id = request.form.get("item_id")
        quantity = int(request.form.get("quantity"))

        if not item_id:
            return apology("must provide item id")
        elif not quantity:
            return apology("must provide quantity")

        rows = db.execute(
            "SELECT * FROM items WHERE id = ? AND status = ?", item_id, ACTIVE
        )
        if len(rows) == 0:
            return apology("item does not exist")

        dict_items = {item_id: {"quantity": quantity}}

        if cart_key in session:
            app.logger.debug(f"cart items from session: {session[cart_key]}")
            if item_id in session[cart_key]:
                flash("This item is already in your cart")
            else:
                # add item to session
                session[cart_key][item_id] = dict_items[item_id]
                flash("Item is successfully added into your cart")
                return redirect(request.referrer)
        else:
            session[cart_key] = dict_items
            flash("Item is successfully added into your cart")
            return redirect(request.referrer)

    except Exception as e:
        app.logger.error(f"exception found: {e}")
        return apology("somthing wrong", 500)

    return redirect(request.referrer)


@app.route("/cart")
@login_required
def cart():
    cart_items = session[cart_key]
    app.logger.debug(f"cart items: {cart_items}")

    keys = tuple(cart_items.keys())
    if len(keys) == 1:
        keys = str(keys).replace(",", "")

    items = db.execute(
        f"SELECT * FROM items WHERE id IN {keys} AND status = ?",
        ACTIVE,
    )

    total_price: float = 0
    for i, item in enumerate(items):
        id = item["id"]
        q = cart_items[str(id)]["quantity"]
        items[i]["quantity"] = q
        total_price += item["price"] * q

    return render_template("cart.html", items=items, total_price=total_price)


@app.route("/remove_from_cart", methods=["POST"])
@login_required
def remove_from_cart():
    try:
        item_id = request.form.get("item_id")

        if not item_id:
            return apology("must provide item id")

        if cart_key in session:
            if item_id in session[cart_key]:
                # del session[cart_key][item_id]
                session[cart_key].pop(item_id, None)

        flash("Item is successfully removed from your cart")

    except Exception as e:
        app.logger.error(f"exception found: {e}")
        return apology("somthing wrong", 500)

    return redirect(request.referrer)


@app.route("/checkout", methods=["POST"])
@login_required
def checkout():
    cart_items = session[cart_key]
    app.logger.debug(f"checkout cart items: {cart_items}")

    for item_id, item in cart_items.items():
        db.execute(
            "UPDATE items SET sold_number = sold_number + ? WHERE id = ?",
            item["quantity"],
            item_id,
        )

    session.pop(cart_key)
    flash("You ahve successfully checkouted your cart")
    return redirect("/")


if __name__ == "__main__":
    init_db()
    init_upload()
    app.run(debug=True)
