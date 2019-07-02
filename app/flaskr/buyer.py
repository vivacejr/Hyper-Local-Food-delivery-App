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

bp = Blueprint("buyer", __name__, url_prefix="/buyer")

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

@bp.route("/order",methods=("GET","POST"))
def order():
    db = get_db()
    tm = time.time()
    userList = ( get_db().execute("SELECT username FROM user WHERE username!=?",(g.user['username'],) ).fetchall() )
    userDict = {}
    lc = (db.execute("SELECT locality FROM user WHERE username=?",(g.user["username"],)).fetchone())[0]
    if request.method == "POST":
        tp = request.form["type"]
        kword = request.form["search"]
        if tp == "Dish":
            global userList
            userList = (get_db().execute("SELECT sellerUsername FROM sell WHERE name LIKE ('%' || ? || '%')",(kword,)).fetchall())
        else:
            global userList
            userList = (get_db().execute("SELECT username FROM user WHERE username LIKE ('%' || ? || '%')",(kword,)).fetchall())
    
    for x in userList:
        L = (db.execute("SELECT locality FROM user WHERE username=?",(x[0],)).fetchone())[0]
        if lc == L:
            userDict[x[0]]= ( get_db().execute("SELECT name FROM sell WHERE sellerUsername = ? and ? < sellingTill", (x[0],tm,)).fetchall() )
    g.uDict = userDict
    # print(userDict)
    return render_template("buyer/order.html")

@bp.route("/menu<uname>",methods=("GET", "POST"))
def menu(uname):
    db= get_db()
    tm = time.time()
    g.seller = uname
    g.userDish = (  get_db().execute("SELECT * FROM sell WHERE sellerUsername=? and ? < sellingTill", (uname,tm,) ).fetchall() )
    if request.method == "POST" :
        dishes = request.form.getlist('name')
        buyerName = g.user["username"]
        sellerName = uname
        status = "Pending"
        total_cost = 0
        quantity = request.form["qty"]
        quantity = int(quantity)
        # print(quantity)
        fl = 0
        for x in dishes:
            Qt = (db.execute("SELECT qAvail FROM sell WHERE sellerUsername=? and name=?",(uname,x)).fetchone())[0]
            # print(Qt,quantity,fl)
            if Qt < quantity:
                fl = 1
        # quantity = int(quantity)
        # print(fl)
        if fl == 1:
            return redirect(url_for("buyer.order"))
            alert("Not in stock")

        mx =0
        for x in dishes:
            Qt = (db.execute("SELECT qAvail FROM sell WHERE sellerUsername=? and name=?",(uname,x)).fetchone())[0]
            Pr = (db.execute("SELECT price FROM sell WHERE sellerUsername=? and name=?",(uname,x)).fetchone())[0]
            P = (db.execute("SELECT sellingTill FROM sell WHERE sellerUsername=? and name=?",(uname,x)).fetchone())[0]
            mx=max(mx,P)
            # print(Qt,Pr,x)
            total_cost = total_cost + quantity*Pr
            Qt = Qt-quantity
            db.execute(
                "UPDATE sell SET qAvail=? WHERE sellerUsername=? and name=?",(Qt,uname,x)
            )
            db.commit()
        print(mx)

        db.execute(
            "INSERT INTO orderhistory (buyerName,sellerName,status,price,endTime,time) VALUES (?,?,?,?,?,?)",
            (buyerName,sellerName,status,total_cost,mx,tm)
        )
        db.commit()
        bid = (db.execute("SELECT max(orderid) FROM orderhistory").fetchone())
        bid = bid[0]      
        for x in dishes:       
            quantity = 1
            price = 1
            db.execute(
                "INSERT INTO orderdish (orderid,itemName,price,qty) VALUES (?,?,?,?)",
                (bid,x,price,quantity)
            )
            db.commit()
        return redirect(url_for("buyer.order"))
    return render_template("buyer/menu.html")


@bp.route("/meal<id>",methods=("GET","POST"))
def meal(id):
    if request.method == "POST":
        seats = request.form["seats"]
        db = get_db()
        ml = (db.execute("SELECT * FROM meal WHERE buffetNo=?",(id,)).fetchone())
        seats = int(seats)
        if seats > ml["seatAvail"]:
            return redirect(url_for('buyer.meal',id=id))            
        db.execute(
            "INSERT INTO buffethistory (invName,joName,total,price,time) VALUES (?,?,?,?,?)",
            (ml["inviterName"],g.user["username"],seats,int(seats)*int(ml["price"]),time.time())
        )
        db.commit()
        st = ml["seatAvail"]-seats
        db.execute(
            "UPDATE meal SET seatAvail = ? WHERE buffetNo=?",(st,ml["buffetNo"])
        )
        db.commit()
    db = get_db()
    g.meal = (db.execute("SELECT * FROM meal WHERE buffetNo=?",(id,)).fetchone())
    g.Menu = (db.execute("SELECT * FROM buffetdishes WHERE buffetNo=?",(id,)).fetchall())
    return render_template("buyer/meal.html")

@bp.route("/joinMeal")
def joinMeal():
    db = get_db()
    tm =time.time()
    userList = ( db.execute("SELECT username FROM user", ).fetchall() )
    userDict = {}
    lc = (db.execute("SELECT locality FROM user WHERE username=?",(g.user["username"],)).fetchone())[0]
    for x in userList:
        L = (db.execute("SELECT locality FROM user WHERE username=?",(x[0],)).fetchone())[0]
        if lc == L:
            userDict[x[0]] = (db.execute("SELECT * FROM meal WHERE inviterName = ? and ? <endTime",(x[0],tm)).fetchall())
    g.mealDict = userDict
    return render_template("buyer/joinMeal.html")


@bp.route("/myMeal")
def myMeal():
    g.myMeals = (db.execute("SELECT * FROM buffethistory WHERE joName=?"),(g.user["username"]).fetchall())
    return render_template("buyer/myMeals.html")