# import os

import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session

# from tempfile import mkdtemp
# from werkzeug.security import check_password_hash, generate_password_hash

# from helpers import apology, login_required, lookup, usd
# import re

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = sqlite3.connect("database.db")

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
    return render_template("index.html")


if __name__ == "__main__":
    app.run()
