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
import os
import math

from helpers import (
    apology,
    login_required,
    usd,
    is_password_valid,
    allowed_file,
)
import pymongo
import config
import datetime
from bson.objectid import ObjectId

app = Flask(__name__)

# Connect to the database
client = None
client = pymongo.MongoClient(config.MONGODB_URI)

db = client[config.DATABASE]
users_coll = db[config.COLLECTIONS.users]
items_coll = db[config.COLLECTIONS.items]
histories_coll = db[config.COLLECTIONS.histories]

UPLOAD_FOLDER = "upload"
CATEGORIES = ["plant", "other", "food", "pet", "accessory"]
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


def init_db():
    users_coll.create_index(
        [("username", pymongo.ASCENDING)], background=True, unique=True
    )

    items_status_index = pymongo.IndexModel(
        [("status", pymongo.ASCENDING)], background=True
    )
    items_owner_index = pymongo.IndexModel(
        [("owner_id", pymongo.ASCENDING)], background=True
    )
    remove_item_index = pymongo.IndexModel(
        [("_id", pymongo.ASCENDING), ("owner_id", pymongo.ASCENDING)], background=True
    )
    list_items_index = pymongo.IndexModel(
        [("owner_id", pymongo.ASCENDING), ("status", pymongo.ASCENDING)],
        background=True,
    )
    items_coll.create_indexes(
        [items_status_index, items_owner_index, remove_item_index, list_items_index]
    )


def init_upload():
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.before_request
def log_request_info():
    if request.method == "POST":
        if len(request.files) > 0:
            app.logger.debug("request body: %s", request.get_data()[:1024])
        else:
            app.logger.debug("request body: %s", request.get_data())


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    try:
        page = int(request.args.get("page"))
    except Exception as e:
        app.logger.debug(f"page error {e}")
        page = 1

    if page is None or page < 1:
        page = 1

    cursor = (
        items_coll.find({"status": ACTIVE})
        .skip((page - 1) * data_per_page)
        .limit(data_per_page)
    )

    total_items = items_coll.count_documents({"status": ACTIVE})
    total_page = math.ceil(total_items / data_per_page)
    pagination = {"current_page": page, "total_page": total_page}
    return render_template(
        "index.html", items=[item for item in cursor], pagination=pagination
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # Ensure username was submitted
        if not username:
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 403)

        # Query database for username
        user = users_coll.find_one({"username": username})

        # Ensure username exists and password is correct
        if user is None or not check_password_hash(user["hash"], password):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        # user_id = str(user["_id"])
        # app.logger.debug(f"user_id: {user_id}")
        # session["user_id"] = user_id
        session["user_id"] = user["_id"]

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

        if not is_password_valid(password):
            return apology(
                "password must contain at least one character, one number and one special character",
                400,
            )

        if password != confirmation:
            return apology("passwords do not match", 400)

        # Query database for username
        user = users_coll.find_one({"username": username})

        # Username already exists
        if user is not None:
            return apology("this username was already taken", 400)

        users_coll.insert_one(
            {"username": username, "hash": generate_password_hash(password)}
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

        user = users_coll.find_one({"_id": user_id})
        if user is None:
            return apology("something wrong", 500)

        if not check_password_hash(user["hash"], current_password):
            return apology("invalid password", 400)
        elif check_password_hash(user["hash"], new_password):
            return apology("new password must not match with current password", 400)

        app.logger.debug(f"[change_password] user_id: {user_id}")

        res = users_coll.update_one(
            {"_id": user_id}, {"$set": {"hash": generate_password_hash(new_password)}}
        )
        if res.modified_count == 0:
            return apology("internal server error", 500)

        flash("Your password has been changed.")
        return redirect("/")

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
        app.logger.debug(f"[add_item] user_id: {user_id}")

        res = items_coll.insert_one(
            {
                "name": name,
                "price": price,
                "description": description,
                "image_name": filename,
                "category": category,
                "owner_id": user_id,
                "status": ACTIVE,
                "sold_number": 0,
            }
        )

        item_id = res.inserted_id

        histories_coll.insert_one(
            {
                "process_type": ADD,
                "process_datetime": datetime.datetime.now(),
                "item_id": item_id,
            }
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

    cursor = items_coll.find({"owner_id": session["user_id"], "status": ACTIVE})

    return render_template("list_items.html", items=[item for item in cursor])


@app.route("/backoffice/remove_item", methods=["POST"])
@login_required
def remove_item():
    user_id = session["user_id"]
    item_id = request.form.get("item_id")

    if not item_id:
        return apology("must provide item id")

    items_coll.update_one(
        {"_id": ObjectId(item_id), "owner_id": user_id},
        {"$set": {"status": DELETED}},
    )

    histories_coll.insert_one(
        {
            "process_type": REMOVE,
            "process_datetime": datetime.datetime.now(),
            "item_id": ObjectId(item_id),
        }
    )

    flash("You have successfully removed an item!")
    return redirect("/backoffice/list_items")


@app.route("/backoffice/history")
@login_required
def history():

    cursor = items_coll.aggregate(
        [
            {"$match": {"owner_id": session["user_id"]}},
            {
                "$lookup": {
                    "from": "histories",
                    "localField": "_id",
                    "foreignField": "item_id",
                    "as": "histories",
                }
            },
            {"$unwind": "$histories"},
            {
                "$addFields": {
                    "process_type": "$histories.process_type",
                    "process_datetime": "$histories.process_datetime",
                }
            },
        ]
    )

    return render_template("history.html", items=[item for item in cursor])


@app.route("/add_to_cart", methods=["POST"])
@login_required
def add_to_cart():
    item_id = request.form.get("item_id")
    try:
        quantity = int(request.form.get("quantity"))
    except Exception as e:
        return apology("invalid quantity")

    if not item_id:
        return apology("must provide item id")
    elif not quantity:
        return apology("must provide quantity")

    item = items_coll.find_one({"_id": ObjectId(item_id), "status": ACTIVE})

    if item is None:
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

    return redirect(request.referrer)


@app.route("/cart")
@login_required
def cart():
    cart_items = session.get(cart_key)
    if cart_items is None:
        return render_template("cart.html", items=[], total_price=0)

    app.logger.debug(f"cart items: {cart_items}")

    keys = [ObjectId(_id) for _id in cart_items.keys()]

    cursor = items_coll.find({"_id": {"$in": keys}, "status": ACTIVE})

    items = [item for item in cursor]

    total_price: float = 0
    for i, item in enumerate(items):
        _id = item["_id"]
        q = cart_items[str(_id)]["quantity"]
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

    bulk_req = []
    for item_id, item in cart_items.items():
        req = pymongo.UpdateOne(
            {"_id": ObjectId(item_id)}, {"$inc": {"sold_number": item["quantity"]}}
        )
        bulk_req.append(req)

    items_coll.bulk_write(bulk_req)

    session.pop(cart_key)
    flash("You ahve successfully checkouted your cart")
    return redirect("/")


if __name__ == "__main__":
    try:
        init_db()
        init_upload()
        app.run(debug=True)
    except Exception as e:
        print(f"Exception found: {e}")
    finally:
        client.close()

    app.logger.info("app is shutdowned")
