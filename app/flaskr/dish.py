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

bp = Blueprint("dish", __name__, url_prefix="/dish")

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

@bp.route("/mydishes")
def mydishes():
    db = get_db()
    g.myDishes = ( get_db().execute("SELECT * FROM item WHERE sellerUsername = ?", (g.user["username"],)).fetchall() )
    return render_template("dish/mydishes.html")

@bp.route("/addDish",methods=("GET", "POST"))
def addDish():
    if request.method == "POST" :
        name = request.form["name"]
        price = request.form["price"]
        desc = request.form["description"]
        typ = request.form["type"]
        db = get_db()
        price = int(price)
        print(type(price))
        db.execute(
            "INSERT INTO item (name,sellerUsername,price,description,type) VALUES (?,?,?,?,?)",
            (name,g.user['username'],price,desc,typ),
        )
        db.commit()
        return redirect(url_for("dish.mydishes"))
    return render_template("dish/addDish.html")

@bp.route("/sell",methods=("GET", "POST"))
def sell():
    db = get_db()
    g.dishList = ( db.execute("SELECT * FROM item WHERE sellerUsername = ?", (g.user["username"],)).fetchall() )
    if request.method == "POST" :
        dishes = request.form.getlist('name')
        quantity = request.form["quantity"]
        stime = request.form["stime"]
        etime = request.form["etime"]
        print(dishes)
        for x in dishes:       
            price= ( db.execute("SELECT price FROM item WHERE sellerUsername = ? and name = ? ", (g.user["username"],x)).fetchone() )
            description= ( db.execute("SELECT description FROM item WHERE sellerUsername = ? and name = ? ", (g.user["username"],x)).fetchone() )
            typ= ( db.execute("SELECT type FROM item WHERE sellerUsername = ? and name = ? ", (g.user["username"],x)).fetchone() )
            print(x)
            print(price)
            price=price[0]
            description=description[0]
            typ=typ[0]
            db.execute(
                "INSERT INTO sell (name,sellerUsername,price,qAvail,readyTime,sellingTill,description,type) VALUES (?,?,?,?,?,?,?,?)",
                (x,g.user['username'],price,quantity,stime,etime,description,typ)
            )
            db.commit()
        return redirect(url_for("dish.salelist"))
    return render_template("dish/sell.html")    


@bp.route("/salelist")
def salelist():
    db = get_db()
    tm = time.time()
    g.sellList = ( get_db().execute("SELECT * FROM sell WHERE sellerUsername = ? and ? < sellingTill", (g.user["username"],tm,)).fetchall() )
    return render_template("dish/salelist.html")



@bp.route("/mealInvites")
def mealInvites():
    db = get_db()
    tm = time.time()
    g.menuList = (db.execute("SELECT * FROM meal WHERE inviterName = ? and ? < endTime ",(g.user["username"],tm)).fetchall())
    return render_template("dish/mealInvites.html")


@bp.route("/mealMenu<id>")
def mealMenu(id):
    db = get_db()
    B = (db.execute("SELECT * FROM meal WHERE buffetNo = ?",(id)).fetchone())
    g.st = B["startTime"]
    g.en = B["endTime"]
    g.pr = B["price"]
    g.seat = B["seatAvail"]
    g.tp = B["type"]
    g.menuL = (db.execute("SELECT * FROM buffetdishes WHERE buffetNo = ?",(id)).fetchall())
    return render_template("dish/mealMenu.html")

@bp.route("/addInvite",methods=("GET","POST"))
def addInvite():
    db = get_db()
    g.dL = ( db.execute("SELECT * FROM item WHERE sellerUsername = ?", (g.user["username"],)).fetchall() )    
    if request.method == "POST":
        dishes = request.form.getlist('name')
        seats = request.form["seats"]
        price = request.form["price"]
        stime = request.form["stime"]
        etime = request.form["etime"]
        typ = request.form["type"]
        # print(price)
        # print(dishes)
        db.execute(
            "INSERT INTO meal (inviterName,price,startTime,endTime,seatAvail,type) VALUES(?,?,?,?,?,?)",
            (g.user["username"],price,stime,etime,seats,typ)
        )
        bid = (db.execute("SELECT MAX(buffetNo) from meal").fetchone())
        bid = bid[0]
        db.commit()
        for x in dishes:
            tp = ( db.execute("SELECT type FROM item WHERE sellerusername = ? and name = ?",(g.user["username"],x)).fetchone() )[0]
            db.execute(
                "INSERT INTO buffetdishes (buffetNo,itemName,type) VALUES(?,?,?)",
                (bid,x,tp)
            )
            db.commit()
        return redirect('mealInvites')
    return render_template("dish/addInvite.html")
