import os
from pymongo import MongoClient
import jwt
from datetime import datetime, timedelta
import time
import hashlib
import uuid
from flask import Flask, send_file, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

MONGODB_CONNECTION_STRING = "mongodb+srv://ahmadlutfi606:wolfattax@cluster0.xctxali.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGODB_CONNECTION_STRING)
db = client.jobseeking

SECRET_KEY = "SEEKER"
TOKEN_KEY = "mytoken"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/job-post")
def job_post():
    token_receive = request.cookies.get(TOKEN_KEY)
    # token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.company.find_one({"email": payload["id"]})
        if user_info:
            return render_template("jobpost.html", user_info=user_info)
        return redirect(url_for("sign_in"))

    except jwt.ExpiredSignatureError:
        return redirect(url_for("sign_in", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("sign_in", msg="There was problem logging you in"))


@app.route("/user-info")
def user_info():
    token_receive = request.cookies.get(TOKEN_KEY)
    # token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.seeker.find_one({"email": payload["id"]})
        if user_info:
            return render_template("userinfo.html", user_info=user_info)
        return redirect(url_for("sign_in"))

    except jwt.ExpiredSignatureError:
        return redirect(url_for("sign_in", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("sign_in", msg="There was problem logging you in"))


@app.route("/user-editFile", methods=["POST"])
def user_editFile():
    if "formFile" in request.files:
        if request.form["realFile"]:
            os.remove(f"./static/{request.form['realFile']}")
    file = request.files.get("formFile")
    folder_receive = request.form["folder"]
    filename = secure_filename(file.filename)
    extension = filename.split(".")[-1]
    seconds = time.time()
    file_path = f"{folder_receive}/{int(seconds)}.{extension}"
    file.save("./static/" + file_path)

    new_doc = {f"{folder_receive}": file_path}
    db.seeker.update_one(
        {"uuid": request.form["uuid"]},
        {"$set": new_doc},
    )
    return redirect(url_for("user_edit"))


@app.route("/download")
def download_file():
    theFile = request.args["path"]
    p = f"static/{theFile}"
    return send_file(p, as_attachment=True)


@app.route("/user-edit", methods=["GET", "POST"])
def user_edit():
    if request.method == "POST":
        uuid_receive = request.form["uuid"]
        username_receive = request.form["username"]
        sex_receive = request.form["sex"]
        address_receive = request.form["address"]
        university_receive = request.form["university"]
        department_receive = request.form["department"]
        entry_year_receive = request.form["entry_year"]
        description_receive = request.form["description"]

        new_doc = {
            "username": username_receive,
            "sex": sex_receive,
            "address": address_receive,
            "university": university_receive,
            "department": department_receive,
            "entry_year": entry_year_receive,
            "description": description_receive,
        }
        db.seeker.update_one(
            {"uuid": uuid_receive},
            {"$set": new_doc},
        )

    token_receive = request.cookies.get(TOKEN_KEY)
    # token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.seeker.find_one({"email": payload["id"]})
        if user_info:
            return render_template("editProfile.html", user_info=user_info)
        return redirect(url_for("sign_in"))

    except jwt.ExpiredSignatureError:
        return redirect(url_for("sign_in", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("sign_in", msg="There was problem logging you in"))


@app.route("/user-job")
def user_job():
    token_receive = request.cookies.get(TOKEN_KEY)
    # token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.seeker.find_one({"email": payload["id"]})
        if user_info:
            return render_template("userjob.html", user_info=user_info)
        return redirect(url_for("sign_in"))

    except jwt.ExpiredSignatureError:
        return redirect(url_for("sign_in", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("sign_in", msg="There was problem logging you in"))    


@app.route("/user-jobdetail")
def user_jobdetail():
    return render_template("userjobdetail.html")


@app.route("/sign-in", methods=["GET", "POST"])
def sign_in():
    if request.method == "POST":
        email_receive = request.form["email_give"]
        password_receive = request.form["password_give"]
        pw_hash = hashlib.sha256(password_receive.encode("utf-8")).hexdigest()
        role = request.form["role_give"]
        if role == "pekerja":
            namespace = db.seeker
        elif role == "perusahaan":
            namespace = db.company
        else:
            return jsonify(
                {
                    "result": "fail",
                    "msg": "Pilih role dengan benar",
                }
            )
        result = namespace.find_one(
            {
                "email": email_receive,
                "password": pw_hash,
            }
        )
        if result:
            payload = {
                "id": email_receive,
                "role": role,
                # the token will be valid for 24 hours
                "exp": datetime.utcnow() + timedelta(seconds=60 * 60 * 24),
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

            return jsonify({"result": "success", "token": token, "role": role})

        else:
            return jsonify(
                {
                    "result": "fail",
                    "msg": "Email atau password salah",
                }
            )
    
    token_receive = request.cookies.get(TOKEN_KEY)
    # token_receive = request.cookies.get("mytoken")
    if token_receive:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        if payload["role"] == "pekerja":            
            return redirect(url_for("user_info"))
        elif payload["role"] == "perusahaan":            
           return redirect(url_for("job_post"))
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
