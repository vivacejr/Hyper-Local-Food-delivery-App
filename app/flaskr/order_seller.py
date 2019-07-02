import functools
import time 
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

bp = Blueprint("order_seller", __name__, url_prefix="/order_seller")

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


@bp.route('/View')
def view():
    db = get_db()
    tm =time.time()
    db.execute( "UPDATE orderhistory SET STATUS='Completed' WHERE  endTime < ? ",(tm,)
     )
    db.commit()
    g.orderList = (db.execute("SELECT * FROM orderhistory WHERE sellername = ?",(g.user["username"],)))
    return render_template("order_sell/view.html")


@bp.route('/orderDetails<id>',methods=("GET","POST"))
def orderDetails(id):
    db = get_db()
    if request.method == "POST":
        dcs = request.form.getlist('decision')
        if dcs[0] == "accept":
            db.execute(
                "UPDATE orderhistory SET STATUS='Confirmed' WHERE orderid = ? and STATUS = 'Pending'",(id,)
            )
        else :
            db.execute(
                "UPDATE orderhistory SET STATUS='Cancelled' WHERE orderid = ? and STATUS = 'Pending'",(id,)
            )
        db.commit()
        return redirect(url_for('order_seller.view'))
    g.od = (db.execute("SELECT * FROM orderhistory WHERE orderid = ?",(id,)).fetchone())
    g.Dishes = (db.execute("SELECT * FROM orderdish WHERE orderid = ?",(id,)).fetchall())
    return render_template("order_sell/orderDetails.html")