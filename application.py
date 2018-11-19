import os
import re

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# custom filter
app.jinja_env.filters["usd"] = usd

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter used for USD strings
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("postgres://hcoahudmlqlorv:f50bf8f07c5ee415f85911c12955d1e659a377c409ec9a2b1bae5008681a1786@ec2-54-75-242-47.eu-west-1.compute.amazonaws.com:5432/dad232sods7f39")


@app.route("/")
@login_required
def index():
    return render_template("/infoboard.html")  #zzz


@app.route("/infoboard", methods=["GET", "POST"])
@login_required
def infoboard():
    """Show infoboard"""

    stocks = db.execute("SELECT AssetName || ' (' || AssetShortName || ' - ' || WKN || ')' as name_shortname FROM tb_assets ORDER BY assetname ASC")
    print(stocks[0])

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Get selection from submitted form:
        WKN = str(request.form.get("name_shortname"))
        # Save newly chosen stock to database
        rows = db.execute("SELECT AssetName, AssetShortName FROM tb_Assets WHERE WKN=:WKN", WKN=WKN)
        SelectionName = rows[0]['AssetName'] + '(' + rows[0]['AssetShortName'] + ' - - ' + WKN + ')'

        # db.execute("UPDATE tb_users SET Last_stock=:new_sym WHERE id=:uid", uid=session["user_id"], new_sym=symbol)

    # User reached route via GET (as by clicking a link or via redirect), not POST
    else:
        # Read from database what was user's last stock selected:

        try:
            last_stock_symbol = db.execute("SELECT last_stock FROM tb_users WHERE id=:uid", uid=session["user_id"])
            WKN = last_stock_symbol[0]['last_stock']
            print ('WKN: ' + WKN)
            if WKN is None:
                WKN = "520000"
        except:
            # if lookup of last stock throws an error, go for Apple:
            WKN = "520000"

        print("Debug: WKN: " + WKN)
        last_stock_name = db.execute("SELECT AssetName, AssetShortName FROM tb_assets WHERE WKN=:WKN", WKN=WKN)

        SelectionName = last_stock_name[0]['AssetName'] + ' (' + last_stock_name[0]['AssetName'] + ' - ' + WKN + ')'


    # render html:
    return render_template("infoboard.html", stocks=stocks, SelectionName=SelectionName, main_heading=SelectionName, sub_heading="Info board")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Query database for username
        rows = db.execute("SELECT * FROM tb_users WHERE username = :username",
                           username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect to home page
        return redirect("/infoboard")
    # User reached route via GET (as by clicking a link or via redirect), not POST
    else:
        return render_template("login.html", main_heading="Stock infoboard", sub_heading="Login")


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

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Check if both passwords are the same:
        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("passwords don't match")

        # Query database for username
        rows = db.execute("SELECT * FROM tb_users WHERE username = :username",
                          username=request.form.get("username"))

        # Check if user already exists
        if len(rows) > 0:
            return apology("username already exists")

        # Write new user to database:
        hash = generate_password_hash(request.form.get("password"))
        rows = db.execute("INSERT INTO tb_users (username, hash) VALUES (:username, :hash)",
                          username=request.form.get("username"), hash=hash)

        # Identify new user id:
        # Query database for username
        rows = db.execute("SELECT * FROM tb_users WHERE username = :username",
                          username=request.form.get("username"))

        # Auto log-in new user:
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return render_template("/login.html")

    # User reached route via GET (as by clicking a link or via redirect), not POST
    else:
        return render_template("register.html", main_heading="Stock infoboard", sub_heading="Register new user")


@app.route("/search")
def search():
    """Search for places that match query"""

    # add % to search string to get similar matches
    try:

        str_search = request.args.get("q") + "%"
        str_search = str_search.replace("\'", " ")
        str_search = str_search.replace("\"", " ")
        # print("str_search after replacments: " + str_search)

    except:
        raise ValueError('Missing parameter q in search')
        return jsonify([])

    # search in postal codes of database:
    rows = db.execute("SELECT * FROM tb_Assets \
                      WHERE AssetName LIKE :q \
                      OR AssetShortName LIKE :q \
                      OR WKN LIKE :q", q=str_search)

    return jsonify(rows[:10])


def errorhandler(e):
    """Handle error"""
    print('ERROR: ')
    print(e)
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
