import os
from pymongo import MongoClient
import jwt
from datetime import datetime, timedelta
import time
import hashlib
import uuid
import requests
from flask import Flask, send_file, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("DB_NAME")

app = Flask(__name__)

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

SECRET_KEY = "SEEKER"
TOKEN_KEY = "mytoken"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/job-edit/<uuid>", methods=["GET", "POST"])
def job_edit(uuid):
    if request.method == "POST":
        new_doc = {
            "position": request.form["position"],
            "description": request.form["description"],
            "province": request.form["prov"],
            "regency": request.form["kot"],
            "address": request.form["address"],
            "time_period": request.form["time_period"],
            "wage_min": request.form["wage_min"],
            "wage_max": request.form["wage_max"],
            "department": request.form["department"],
            "tag1": request.form["tag1"],
            "tag2": request.form["tag2"],
            "date": time.time(),
            "status": request.form["status"],
        }

        db.jobs.update_one({"uuid": uuid}, {"$set": new_doc})
        return redirect(f"/job-edit/{uuid}?msg=Lowongan+Berhasil+Diedit")
    token_receive = request.cookies.get(TOKEN_KEY)
    # token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.company.find_one({"email": payload["id"]})
        if user_info:
            thejob = db.jobs.find_one({"uuid": uuid})
            msg = request.args.get("msg")
            return render_template(
                "jobedit.html", user_info=user_info, job=thejob, msg=msg
            )
        return redirect(url_for("sign_in"))

    except jwt.ExpiredSignatureError:
        return redirect(url_for("sign_in", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("sign_in", msg="There was problem logging you in"))


@app.route("/job-post", methods=["GET", "POST"])
def job_post():
    if request.method == "POST":
        new_doc = {
            "uuid": f"{uuid.uuid1()}",
            "company": request.form["uuid"],
            "position": request.form["position"],
            "description": request.form["description"],
            "province": request.form["prov"],
            "regency": request.form["kot"],
            "address": request.form["address"],
            "time_period": request.form["time_period"],
            "wage_min": request.form["wage_min"],
            "wage_max": request.form["wage_max"],
            "department": request.form["department"],
            "tag1": request.form["tag1"],
            "tag2": request.form["tag2"],
            "date": time.time(),
            "status": "active",
            "approve": "no",
        }

        db.jobs.insert_one(new_doc)
        return redirect(url_for("job_post", msg="Lowongan Berhasil Dibuat"))
    token_receive = request.cookies.get(TOKEN_KEY)
    # token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.company.find_one({"email": payload["id"]})
        if user_info:
            msg = request.args.get("msg")
            return render_template(
                "jobpost.html", user_info=user_info, msg=msg, url="/job-post"
            )
        return redirect(url_for("sign_in"))

    except jwt.ExpiredSignatureError:
        return redirect(url_for("sign_in", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("sign_in", msg="There was problem logging you in"))


@app.route("/pelamar", methods=["GET"])
def pelamar_get():
    status = request.args["status"]
    job = request.args["job"]
    if status == "all":
        pelamar_list = list(
            db.applicant.find({"job": job}, {"_id": False}).sort("_id", -1)
        )
    else:
        pelamar_list = list(
            db.applicant.find({"status": status, "job": job}, {"_id": False}).sort(
                "_id", -1
            )
        )
    return jsonify({"pelamar_list": pelamar_list})


@app.route("/get_name", methods=["GET"])
def get_name():
    seeker_id = request.args["seeker"]
    name = db.seeker.find_one({"uuid": seeker_id}, {"_id": False})

    return jsonify({"name": name["username"]})


@app.template_filter()
def format_province(value):
    url = f"https://emsifa.github.io/api-wilayah-indonesia/api/province/{value}.json"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code

        data = response.json()
        return data["name"]

    except requests.exceptions.RequestException as e:
        return "Error"


@app.template_filter()
def format_regency(value):
    url = f"https://emsifa.github.io/api-wilayah-indonesia/api/regency/{value}.json"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code

        data = response.json()
        return data["name"]

    except requests.exceptions.RequestException as e:
        return "Error"


@app.template_filter()
def format_datetime(value):
    dt_object = datetime.fromtimestamp(value)
    return f"{dt_object.day}/{dt_object.month}/{dt_object.year}"


@app.route("/seeker-job/<uuid>/<uuid2>", methods=["GET", "POST"])
def seeker_jobdetail(uuid, uuid2):
    if request.method == "POST":
        db.applicant.update_one(
            {"uuid": request.form["uuid"]},
            {"$set": {"status": request.form["status"]}},
        )
        return jsonify({"msg": "Berhasil Update Status"})
    token_receive = request.cookies.get(TOKEN_KEY)
    # token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.company.find_one({"email": payload["id"]})
        if user_info:
            jobs = db.jobs.find_one({"uuid": uuid})
            theseeker = db.seeker.find_one({"uuid": uuid2})
            theapplicant = db.applicant.find_one({"seeker": uuid2, "job": uuid})

            return render_template(
                "detailpelamar.html",
                user_info=user_info,
                jobs=jobs,
                seeker=theseeker,
                applicant=theapplicant,
                url="/company-job",
            )
        return redirect(url_for("sign_in"))

    except jwt.ExpiredSignatureError:
        return redirect(url_for("sign_in", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("sign_in", msg="There was problem logging you in"))


@app.route("/seeker-job/<uuid>")
def seeker_job(uuid):
    token_receive = request.cookies.get(TOKEN_KEY)
    # token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.company.find_one({"email": payload["id"]})
        if user_info:
            jobs = db.jobs.find_one({"uuid": uuid})

            return render_template(
                "daftarpelamar.html",
                user_info=user_info,
                jobs=jobs,
                url="/company-job",
            )
        return redirect(url_for("sign_in"))

    except jwt.ExpiredSignatureError:
        return redirect(url_for("sign_in", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("sign_in", msg="There was problem logging you in"))


@app.route("/company-job/<uuid>")
def company_jobdetail(uuid):
    token_receive = request.cookies.get(TOKEN_KEY)
    # token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.company.find_one({"email": payload["id"]})
        if user_info:
            jobs = db.jobs.find_one({"uuid": uuid})

            return render_template(
                "companyjobdetail.html",
                user_info=user_info,
                jobs=jobs,
                url="/company-job",
            )
        return redirect(url_for("sign_in"))

    except jwt.ExpiredSignatureError:
        return redirect(url_for("sign_in", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("sign_in", msg="There was problem logging you in"))


@app.route("/search-job")
def search_job():
    offset = int(request.args["offset"])
    limit = int(request.args["limit"])
    starting_id = db.jobs.find({"approve": "yes", "status": "active"}).sort("_id", -1)
    try:
        last_id = starting_id[offset]["_id"]
    except IndexError:
        return redirect(
            url_for(
                "search_job",
                limit=str(limit),
                offset=str(offset - limit),
                query=request.args["query"],
                prov=request.args["prov"],
                kot=request.args["kot"],
                tag1=request.args["tag1"],
                tag2=request.args["tag2"],
                msg="Lowongan Hanya Sampai Sini",
                url="/search-job",
            )
        )

    cari = {"_id": {"$lte": last_id}, "approve": "yes", "status": "active"}

    if request.args["query"]:
        cari["position"] = {
            "$regex": f"{request.args['query']}",
            "$options": "i",
        }
    if request.args["prov"]:
        cari["province"] = f"{request.args['prov']}"
    if request.args["kot"]:
        cari["regency"] = f"{request.args['kot']}"

    if request.args["tag1"]:
        cari["$or"] = [
            {"tag1": request.args["tag1"]},
            {"tag2": request.args["tag1"]},
        ]
    if request.args["tag2"]:
        cari["$or"] = [
            {"tag1": request.args["tag2"]},
            {"tag2": request.args["tag2"]},
        ]
    if request.args["tag2"] and request.args["tag1"]:
        cari["$or"] = [
            {"tag1": {"$in": [request.args["tag2"], request.args["tag1"]]}},
            {"tag2": {"$in": [request.args["tag2"], request.args["tag1"]]}},
        ]

    thelist = (
        db.jobs.find(
            cari,
            {"_id": False},
        )
        .sort("_id", -1)
        .limit(limit)
    )

    output = []
    for i in thelist:
        output.append(i)
    # limit=4&offset=0&query=android&prov=52&kot=5202&tag1=Microsft-Office&tag2=Adobe-Photoshop
    next_url = (
        "search-job?limit="
        + str(limit)
        + "&offset="
        + str(offset + limit)
        + "&query="
        + request.args["query"]
        + "&prov="
        + str(request.args["prov"])
        + "&kot="
        + str(request.args["kot"])
        + "&tag1="
        + request.args["tag1"]
        + "&tag2="
        + request.args["tag2"]
    )
    prev_url = (
        "search-job?limit="
        + str(limit)
        + "&offset="
        + str(offset - limit)
        + "&query="
        + request.args["query"]
        + "&prov="
        + str(request.args["prov"])
        + "&kot="
        + str(request.args["kot"])
        + "&tag1="
        + request.args["tag1"]
        + "&tag2="
        + request.args["tag2"]
    )

    query = f"{request.args['query']}"
    msg = request.args.get("msg")

    token_receive = request.cookies.get(TOKEN_KEY)
    # token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.seeker.find_one({"email": payload["id"]})
        if user_info:
            return render_template(
                "searchresult.html",
                user_info=user_info,
                output=output,
                prev_url=prev_url,
                next_url=next_url,
                query=query,
                msg=msg,
                url="/search-job",
            )
        return redirect(url_for("sign_in"))

    except jwt.ExpiredSignatureError:
        return redirect(url_for("sign_in", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        user_info = None  # Set user_info to None in case of decoding error
        return render_template(
            "searchresult.html",
            user_info=user_info,
            output=output,
            prev_url=prev_url,
            next_url=next_url,
            query=query,
            msg=msg,
            url="/search-job",
        )


@app.route("/admin-job")
def admin_job():
    token_receive = request.cookies.get(TOKEN_KEY)
    # token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.admin.find_one({"email": payload["id"]})
        if user_info:
            offset = int(request.args["offset"])
            limit = int(request.args["limit"])
            starting_id = db.jobs.find({"approve": "no"}).sort("_id", -1)
            if db.jobs.count_documents({"approve": "no"}) == 0:
                # pindahkan ketempat lain
                return render_template(
                    "adminjob.html",
                    user_info=user_info,
                    msg="sedang tidak ada lamaran",
                    url="/admin-job",
                )
            try:
                last_id = starting_id[offset]["_id"]
            except IndexError:
                return redirect(
                    url_for(
                        "admin_job",
                        limit=str(limit),
                        offset=str(offset - limit),
                        msg="Lowongan Hanya Sampai Sini",
                        url="/admin-job",
                    )
                )

            thelist = (
                db.jobs.find(
                    {"_id": {"$lte": last_id}, "approve": "no"},
                    {"_id": False},
                )
                .sort("_id", -1)
                .limit(limit)
            )

            output = []
            for i in thelist:
                output.append(i)

            next_url = (
                "admin-job?limit=" + str(limit) + "&offset=" + str(offset + limit)
            )
            prev_url = (
                "admin-job?limit=" + str(limit) + "&offset=" + str(offset - limit)
            )

            msg = request.args.get("msg")
            return render_template(
                "adminjob.html",
                user_info=user_info,
                output=output,
                prev_url=prev_url,
                next_url=next_url,
                msg=msg,
                url="/admin-job",
            )
        return redirect(url_for("sign_in"))

    except jwt.ExpiredSignatureError:
        return redirect(url_for("sign_in", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("sign_in", msg="There was problem logging you in"))


@app.route("/company-job")
def company_job():
    token_receive = request.cookies.get(TOKEN_KEY)
    # token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.company.find_one({"email": payload["id"]})
        if user_info:
            offset = int(request.args.get("offset", 0))
            limit = int(request.args.get("limit", 3))
            starting_id = db.jobs.find({"company": user_info["uuid"]}).sort("_id", -1)
            if db.jobs.count_documents({"company": user_info["uuid"]}) > 0:
                try:
                    last_id = starting_id[offset]["_id"]
                except IndexError:
                    return redirect(
                        url_for(
                            "company_job",
                            limit=str(limit),
                            offset=str(offset - limit),
                            query=request.args["query"],
                            prov=request.args["prov"],
                            kot=request.args["kot"],
                            tag1=request.args["tag1"],
                            tag2=request.args["tag2"],
                            msg="Lowongan Hanya Sampai Sini",
                        )
                    )
            else:
                return redirect(
                    url_for(
                        "company_info",
                        msg="Lowongan Kosong",
                    )
                )

            cari = {"_id": {"$lte": last_id}, "company": user_info["uuid"]}
            if request.args["query"]:
                cari["position"] = {
                    "$regex": f"{request.args['query']}",
                    "$options": "i",
                }
            if request.args["prov"]:
                cari["province"] = f"{request.args['prov']}"
            if request.args["kot"]:
                cari["regency"] = f"{request.args['kot']}"

            if request.args["tag1"]:
                cari["$or"] = [
                    {"tag1": request.args["tag1"]},
                    {"tag2": request.args["tag1"]},
                ]
            if request.args["tag2"]:
                cari["$or"] = [
                    {"tag1": request.args["tag2"]},
                    {"tag2": request.args["tag2"]},
                ]
            if request.args["tag2"] and request.args["tag1"]:
                cari["$or"] = [
                    {"tag1": {"$in": [request.args["tag2"], request.args["tag1"]]}},
                    {"tag2": {"$in": [request.args["tag2"], request.args["tag1"]]}},
                ]

            thelist = (
                db.jobs.find(
                    cari,
                    {"_id": False},
                )
                .sort("_id", -1)
                .limit(limit)
            )
            # thelist = (
            #     db.jobs.find(
            #         {"_id": {"$lte": last_id}, "company": user_info["uuid"]},
            #         {"_id": False},
            #     )
            #     .sort("_id", -1)
            #     .limit(limit)
            # )

            output = []
            for i in thelist:
                output.append(i)

            next_url = (
                "company-job?limit="
                + str(limit)
                + "&offset="
                + str(offset + limit)
                + "&query="
                + request.args["query"]
                + "&prov="
                + str(request.args["prov"])
                + "&kot="
                + str(request.args["kot"])
                + "&tag1="
                + request.args["tag1"]
                + "&tag2="
                + request.args["tag2"]
            )
            prev_url = (
                "company-job?limit="
                + str(limit)
                + "&offset="
                + str(offset - limit)
                + "&query="
                + request.args["query"]
                + "&prov="
                + str(request.args["prov"])
                + "&kot="
                + str(request.args["kot"])
                + "&tag1="
                + request.args["tag1"]
                + "&tag2="
                + request.args["tag2"]
            )

            msg = request.args.get("msg")
            return render_template(
                "companyjob.html",
                user_info=user_info,
                output=output,
                prev_url=prev_url,
                next_url=next_url,
                msg=msg,
                url="/company-job",
            )
        return redirect(url_for("sign_in"))

    except jwt.ExpiredSignatureError:
        return redirect(url_for("sign_in", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("sign_in", msg="There was problem logging you in"))


@app.route("/company-info")
def company_info():
    token_receive = request.cookies.get(TOKEN_KEY)
    # token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.company.find_one({"email": payload["id"]})
        if user_info:
            jobs = db.jobs.find_one({"company": user_info["uuid"]})
            # return jsonify(
            #     {
            #         "result": "success",
            #         "msg": user_info,
            #     }
            # )
            msg = request.args.get("msg")
            return render_template(
                "companyinfo.html", user_info=user_info, jobs=jobs, msg=msg
            )
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
            lowongan = db.applicant.find_one({"seeker": user_info["uuid"]})
            if lowongan:
                job = db.jobs.find_one({"uuid": lowongan["job"]})
                return render_template("userinfo.html", user_info=user_info, jobs=job)
            return render_template("userinfo.html", user_info=user_info)

        return redirect(url_for("sign_in"))

    except jwt.ExpiredSignatureError:
        return redirect(url_for("sign_in", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("sign_in", msg="There was problem logging you in"))


@app.route("/company")
def companymain():
    token_receive = request.cookies.get(TOKEN_KEY)
    # token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.company.find_one({"email": payload["id"]})
        if user_info:
            return render_template(
                "companymainpage.html", user_info=user_info, url="/company"
            )
        return redirect(url_for("sign_in"))

    except jwt.ExpiredSignatureError:
        return redirect(url_for("sign_in", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("sign_in", msg="There was problem logging you in"))


@app.route("/user")
def usermain():
    token_receive = request.cookies.get(TOKEN_KEY)
    # token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.seeker.find_one({"email": payload["id"]})
        if user_info:
            return render_template(
                "usermainpage.html", user_info=user_info, url="/user"
            )
            # return render_template("userbase.html", user_info=user_info)
        return redirect(url_for("sign_in"))

    except jwt.ExpiredSignatureError:
        return redirect(url_for("sign_in", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("sign_in", msg="There was problem logging you in"))


@app.route("/user-editFile", methods=["POST"])
def user_editFile():
    token_receive = request.cookies.get(TOKEN_KEY)
    # token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        if "formFile" in request.files:
            if request.form["realFile"]:
                try:
                    os.remove(f"./static/{request.form['realFile']}")
                except FileNotFoundError:
                    a = "Not Found"
        file = request.files.get("formFile")
        folder_receive = request.form["folder"]
        filename = secure_filename(file.filename)
        extension = filename.split(".")[-1]
        seconds = time.time()
        file_path = f"{folder_receive}/{int(seconds)}.{extension}"
        file.save("./static/" + file_path)

        new_doc = {f"{folder_receive}": file_path}
        if payload["role"] == "pekerja":
            db.seeker.update_one(
                {"uuid": request.form["uuid"]},
                {"$set": new_doc},
            )
            return redirect(url_for("user_edit", msg="Update Profile Berhasil"))
            # return redirect(url_for("user_edit"))
        elif payload["role"] == "perusahaan":
            db.company.update_one(
                {"uuid": request.form["uuid"]},
                {"$set": new_doc},
            )
            return redirect(url_for("company_edit"))

        return redirect(url_for("sign_in"))

    except jwt.ExpiredSignatureError:
        return redirect(url_for("sign_in", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("sign_in", msg="There was problem logging you in"))


@app.route("/download")
def download_file():
    theFile = request.args["path"]
    p = f"static/{theFile}"
    try:
        return send_file(p, as_attachment=True)
    except FileNotFoundError:
        return "Not Found"


@app.route("/company-edit", methods=["GET", "POST"])
def company_edit():
    if request.method == "POST":
        uuid_receive = request.form["uuid"]
        name_receive = request.form["name"]
        email_receive = request.form["email"]
        address_receive = request.form["address"]
        sector_receive = request.form["sector"]
        sosmed_1_receive = request.form["sosmed_1"]
        sosmed_2_receive = request.form["sosmed_2"]
        licensing_receive = request.form["licensing"]
        description_receive = request.form["description"]

        new_doc = {
            "name": name_receive,
            "email": email_receive,
            "address": address_receive,
            "sector": sector_receive,
            "sosmed_1": sosmed_1_receive,
            "sosmed_2": sosmed_2_receive,
            "licensing": licensing_receive,
            "description": description_receive,
        }
        db.company.update_one(
            {"uuid": uuid_receive},
            {"$set": new_doc},
        )
        return redirect(url_for("company_edit", msg="Edit Perusahaan Berhasil"))

    token_receive = request.cookies.get(TOKEN_KEY)
    # token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.company.find_one({"email": payload["id"]})
        if user_info:
            msg = request.args.get("msg")
            return render_template(
                "editProfileCompany.html", user_info=user_info, msg=msg
            )
        return redirect(url_for("sign_in"))

    except jwt.ExpiredSignatureError:
        return redirect(url_for("sign_in", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("sign_in", msg="There was problem logging you in"))


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
        return redirect(url_for("user_edit", msg="Update Profile Berhasil"))

    token_receive = request.cookies.get(TOKEN_KEY)
    # token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.seeker.find_one({"email": payload["id"]})
        if user_info:
            msg = request.args.get("msg")
            return render_template(
                "editProfile.html", user_info=user_info, msg=msg, url="/user"
            )
        return redirect(url_for("sign_in"))

    except jwt.ExpiredSignatureError:
        return redirect(url_for("sign_in", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("sign_in", msg="There was problem logging you in"))


@app.route("/user-job-cancel", methods=["POST"])
def user_jobCancel():
    id_applicant = request.form["id_applicant"]
    db.applicant.delete_one({"uuid": id_applicant})
    return redirect(url_for("usermain", msg="Berhasil Cancel Lamaran"))

@app.route("/company-job-cancel", methods=["POST"])
def company_jobCancel():
    id_jobs = request.form["id_jobs"]
    db.jobs.delete_one({"uuid": id_jobs})
    return redirect(url_for("job_post", msg="Berhasil Hapus Lowongan"))


@app.route("/user-job")
def user_job():
    token_receive = request.cookies.get(TOKEN_KEY)
    # token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.seeker.find_one({"email": payload["id"]})
        if user_info:
            offset = int(request.args.get("offset", 0))
            limit = int(request.args.get("limit", 3))
            starting_id = db.applicant.find({"seeker": user_info["uuid"]}).sort(
                "_id", -1
            )
            try:
                last_id = starting_id[offset]["_id"]
            except IndexError:
                return redirect(
                    url_for(
                        "user_job",
                        limit=str(limit),
                        offset=str(offset - limit),
                        msg="Lowongan Hanya Sampai Sini",
                        url="/user-job",
                    )
                )
            jobku = []
            for i in starting_id:
                jobku.append(i["job"])

            starting_id2 = db.jobs.find({"uuid": {"$in": jobku}}).sort("_id", -1)
            try:
                last_id2 = starting_id2[offset]["_id"]
            except IndexError:
                return redirect(
                    url_for(
                        "user_job",
                        limit=str(limit),
                        offset=str(offset - limit),
                        msg="Lowongan Hanya Sampai Sini",
                        url="/user-job",
                    )
                )

            thelist = (
                db.jobs.find(
                    {"_id": {"$lte": last_id2}, "uuid": {"$in": jobku}},
                    {"_id": False},
                )
                .sort("_id", -1)
                .limit(limit)
            )

            output = []
            for i in thelist:
                output.append(i)

            next_url = "user-job?limit=" + str(limit) + "&offset=" + str(offset + limit)
            prev_url = "user-job?limit=" + str(limit) + "&offset=" + str(offset - limit)
            msg = request.args.get("msg")
            return render_template(
                "userjob.html",
                user_info=user_info,
                output=output,
                msg=msg,
                next_url=next_url,
                prev_url=prev_url,
                url="/user-job",
            )
        return redirect(url_for("sign_in"))

    except jwt.ExpiredSignatureError:
        return redirect(url_for("sign_in", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("sign_in", msg="There was problem logging you in"))


@app.route("/admin-job/<uuid2>", methods=["GET", "POST"])
def admin_jobdetail(uuid2):
    if request.method == "POST":
        new_doc = {
            "approve": request.form["approve_give"],
        }
        db.jobs.update_one({"uuid": uuid2}, {"$set": new_doc})
        return jsonify(
            {
                "result": "success",
                "msg": "Berhasil Approve",
            }
        )
    token_receive = request.cookies.get(TOKEN_KEY)
    # token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.admin.find_one({"email": payload["id"]})
        if user_info:
            jobs2 = db.jobs.find_one({"uuid": uuid2})
            return render_template(
                "adminjobdetail.html",
                user_info=user_info,
                jobs=jobs2,
                url="/admin-job",
            )
        return redirect(url_for("sign_in"))

    except jwt.ExpiredSignatureError:
        return redirect(url_for("sign_in", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("sign_in", msg="There was problem logging you in"))


@app.route("/user-job/<uuid2>", methods=["GET", "POST"])
def user_jobdetail(uuid2):
    if request.method == "POST":
        new_doc = {
            "uuid": f"{uuid.uuid1()}",
            "seeker": request.form["seeker"],
            "job": request.form["job"],
            "letter": request.form["Letter"],
            "status": "pending",
        }
        db.applicant.insert_one(new_doc)
        return redirect(
            url_for("user_job", msg="Berhasil Daftar", limit="3", offset="0")
        )

    jobs2 = db.jobs.find_one({"uuid": uuid2})
    token_receive = request.cookies.get(TOKEN_KEY)
    # token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.seeker.find_one({"email": payload["id"]})
        if user_info:
            cek = db.applicant.find_one({"job": uuid2, "seeker": user_info["uuid"]})
            if cek is None:
                cek = "belum Daftar"
            return render_template(
                "userjobdetail.html",
                user_info=user_info,
                jobs=jobs2,
                cek=cek,
                url="/user-job",
            )
        return redirect(url_for("sign_in"))

    except jwt.ExpiredSignatureError:
        return redirect(url_for("sign_in", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return render_template(
            "userjobdetail.html",
            jobs=jobs2,
            url="/search-job",
        )


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
        elif role == "admin":
            namespace = db.admin
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
        "address": "",
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
