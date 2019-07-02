import functools

from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from flaskr.db import get_db

bp = Blueprint("order_buyer", __name__, url_prefix="/order_buyer")

def login_required(view):
    """View decorator that
    redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = (
            get_db().execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
        )


@bp.route("/view")
def view():
    db = get_db()
    g.orderList=  db.execute("SELECT * FROM orderhistory WHERE buyername=?", (g.user['username'],)).fetchall()
    return render_template("order_buy/view.html")

@bp.route("/details<id>")
def details(id):
    db = get_db()
    print(id)
    g.orderDetail=  db.execute("SELECT * FROM orderdish WHERE orderid=?", (id,)).fetchall()
    print(g.orderDetail)
    return render_template("order_buy/details.html")

@bp.route("/myMeal")
def myMeal():
    db = get_db()
    g.myMeals = (db.execute("SELECT * FROM buffethistory WHERE joName=?",(g.user["username"],)).fetchall())
    return render_template("buyer/myMeals.html")