from pymongo import MongoClient
import jwt
from datetime import datetime, timedelta
import hashlib
import uuid
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

MONGODB_CONNECTION_STRING = "mongodb+srv://ahmadlutfi606:wolfattax@cluster0.xctxali.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGODB_CONNECTION_STRING)
db = client.jobseeking

TOKEN_KEY = "mytoken"


@app.route("/sign-in")
def sign_in():
    msg = request.args.get("msg")
    return render_template("signin.html", msg=msg)


@app.route("/sign-up")
def sign_up():
    msg = request.args.get("msg")
    return render_template("signup.html", msg=msg)


@app.route("/sign_up/seeker", methods=["POST"])
def sign_up_seeker():
    theId = f"{uuid.uuid1()}"
    username_receive = request.form["name"]
    email_receive = request.form["email"]
    email_info = db.seeker.find_one({"email": email_receive})
    password_receive = request.form["password"]
    confirm_password_receive = request.form["confirm_password"]
    if email_info:
        return redirect(url_for("sign_up", msg="Email Sudah Terdaftar"))
    if len(password_receive) < 8:
        return redirect(url_for("sign_up", msg="Password Terlalu Pendek"))
    if password_receive != confirm_password_receive:
        return redirect(url_for("sign_up", msg="Password Tidak valid"))
    password_hash = hashlib.sha256(password_receive.encode("utf-8")).hexdigest()
    doc = {
        "uuid": theId,
        "username": username_receive,
        "email": email_receive,
        "password": password_hash,  # password
        "sex": "",
        "address": "",
        "university": "",
        "department": "",
        "entry_year": "",
        "description": "",
        "profile_pic": "",
        "cv": "",
        "certification": "",
        # "profile_info": "",  # a profile description
        # "profile_pic_real": "profile_pics/profile_placeholder.png",  # a default profile image
    }
    db.seeker.insert_one(doc)
    # return jsonify({"result": "success"})
    return redirect(url_for("sign_in", msg="Silahkan Login"))


@app.route("/sign_up/company", methods=["POST"])
def sign_up_company():
    theId = f"{uuid.uuid1()}"
    username_receive = request.form["name"]
    email_receive = request.form["email"]
    email_info = db.company.find_one({"email": email_receive})
    password_receive = request.form["password"]
    confirm_password_receive = request.form["confirm_password"]
    if email_info:
        return redirect(url_for("sign_up", msg="Email Sudah Terdaftar"))
    if len(password_receive) < 8:
        return redirect(url_for("sign_up", msg="Password Terlalu Pendek"))
    if password_receive != confirm_password_receive:
        return redirect(url_for("sign_up", msg="Password Tidak valid"))
    password_hash = hashlib.sha256(password_receive.encode("utf-8")).hexdigest()
    doc = {
        "uuid": theId,
        "name": username_receive,
        "email": email_receive,  # id
        "password": password_hash,  # password
        "sector": "",
        "sosmed_1": "",
        "sosmed_2": "",
        "licensing": "",
        "description": "",
        "company_pic": "",
    }
    db.company.insert_one(doc)
    return redirect(url_for("sign_in", msg="Silahkan Login"))


if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)
