import os
import uuid
import bcrypt
from datetime import datetime, timedelta
from flask_mail import Mail, Message
from dotenv import load_dotenv
from flask_cors import CORS
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from db import init_db, mysql
from s3_config import s3, BUCKET_NAME

load_dotenv()

app = Flask(__name__)
CORS(app)
init_db(app)
BASE_URL = os.getenv("BASE_URL")
FRONTEND_URL = os.getenv("FRONTEND_URL")


# ================= JWT =================
app.config["JWT_SECRET_KEY"] = "cloudvault-super-secret-jwt-key-2026-secure"
jwt = JWTManager(app)

# ================= MAIL CONFIG =================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("EMAIL_USER")
app.config['MAIL_PASSWORD'] = os.getenv("EMAIL_PASS")
mail = Mail(app)

# ================= SIGNUP =================
@app.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json(force=True)
        name,email,password = data.get("name"),data.get("email"),data.get("password")

        if not name or not email or not password:
            return jsonify({"error":"All fields required"}),400

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s",(email,))
        if cursor.fetchone():
            cursor.close()
            return jsonify({"error":"Email already registered"}),400

        verify_token = str(uuid.uuid4())

        cursor.execute(
            "INSERT INTO users (name,email,password,verify_token) VALUES (%s,%s,%s,%s)",
            (name,email,hashed,verify_token)
        )
        mysql.connection.commit()
        cursor.close()

        verify_link = f"{BASE_URL}/verify-email/{verify_token}"


        msg = Message(
            "Verify CloudVault Account ☁️",
            sender=os.getenv("EMAIL_USER"),
            recipients=[email]
        )
        msg.body = f"Verify your account:\n{verify_link}"

        try:
            mail.send(msg)
            return jsonify({"message":"Signup successful! Check your email 📧"}),201
        except Exception as e:
            print("MAIL ERROR:", e)
            return jsonify({"message":"Signup ok but mail failed", "debug_verify_link":verify_link}),201

    except Exception as e:
        print("SIGNUP ERROR:", e)
        return jsonify({"error":"Server error"}),500


# ================= EMAIL VERIFY =================
@app.route("/verify-email/<token>")
def verify_email(token):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE verify_token=%s",(token,))
    user = cursor.fetchone()

    if not user:
        return "Invalid verification link"

    cursor.execute("UPDATE users SET is_verified=TRUE, verify_token=NULL WHERE verify_token=%s",(token,))
    mysql.connection.commit()
    cursor.close()
    return "Email verified! You can login now."


# ================= LOGIN =================
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json(force=True)
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error":"Missing email or password"}),400

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s",(email,))
        user = cursor.fetchone()
        cursor.close()

        if not user:
            return jsonify({"error":"User not found"}),404

        # email verification check
        if not user[4]:
            return jsonify({"error":"Please verify your email"}),403

        # password check
        if not bcrypt.checkpw(password.encode(), user[3].encode()):
            return jsonify({"error":"Wrong password"}),401

        token = create_access_token(identity=email)
        return jsonify({"token":token}),200

    except Exception as e:
        print("LOGIN ERROR:", e)
        return jsonify({"error":"Server login crash"}),500


# ================= FORGOT PASSWORD =================
@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    email = request.json.get("email")

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE email=%s",(email,))
    user = cursor.fetchone()

    if not user:
        return jsonify({"error":"Email not registered"}),404

    token = str(uuid.uuid4())
    expiry = datetime.now() + timedelta(minutes=10)

    cursor.execute("UPDATE users SET reset_token=%s, reset_expiry=%s WHERE email=%s",(token,expiry,email))
    mysql.connection.commit()
    cursor.close()

    reset_link = f"{FRONTEND_URL}/reset.html?token={token}"


    msg = Message("CloudVault Reset 🔐",
        sender=os.getenv("EMAIL_USER"),
        recipients=[email])
    msg.body = f"Reset password:\n{reset_link}"

    try:
        mail.send(msg)
        return jsonify({"message":"Reset link sent 📧"})
    except Exception as e:
        print("MAIL ERROR:", e)
        return jsonify({"message":"Mail failed", "debug_reset_link":reset_link})


# ================= RESET PASSWORD =================
@app.route("/reset-password", methods=["POST"])
def reset_password():
    token = request.json.get("token")
    new_password = request.json.get("password")

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE reset_token=%s",(token,))
    user = cursor.fetchone()

    if not user:
        return jsonify({"error":"Invalid token"}),400

    if datetime.now() > user[6]:
        return jsonify({"error":"Token expired"}),400

    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())

    cursor.execute("UPDATE users SET password=%s, reset_token=NULL, reset_expiry=NULL WHERE reset_token=%s",(hashed,token))
    mysql.connection.commit()
    cursor.close()

    return jsonify({"message":"Password updated"})


# ================= FILE UPLOAD =================
@app.route("/upload", methods=["POST"])
@jwt_required()
def upload_file():
    user = get_jwt_identity()
    file = request.files["file"]

    key = f"{user}/{file.filename}"
    s3.upload_fileobj(file, BUCKET_NAME, key)

    return jsonify({"message":"Uploaded"})


# ================= LIST FILES =================
@app.route("/files", methods=["GET"])
@jwt_required()
def list_files():
    user = get_jwt_identity()
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=user+"/")

    files=[]
    total_size=0

    if "Contents" in response:
        for obj in response["Contents"]:
            size_kb = round(obj["Size"]/1024,2)
            total_size += size_kb
            files.append({
                "name": obj["Key"].split("/")[-1],
                "size": size_kb
            })

    return jsonify(files)


# ================= STORAGE STATS =================

@app.route("/stats")
@jwt_required()
def stats():
    try:
        user = get_jwt_identity()
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=user+"/")

        total_size = 0
        file_count = 0

        if "Contents" in response:
            for obj in response["Contents"]:
                total_size += obj["Size"]
                file_count += 1

        return jsonify({
            "storage_mb": round(total_size/(1024*1024),2),
            "files": file_count
        })

    except Exception as e:
        print("STATS ERROR:", e)
        return jsonify({"storage_mb":0,"files":0})


# ================= DELETE =================
@app.route("/delete/<filename>", methods=["DELETE"])
@jwt_required()
def delete_file(filename):
    user = get_jwt_identity()
    s3.delete_object(Bucket=BUCKET_NAME, Key=f"{user}/{filename}")
    return jsonify({"message":"Deleted"})


# ================= DOWNLOAD =================
@app.route("/download/<filename>")
@jwt_required()
def download_file(filename):
    user = get_jwt_identity()
    url = s3.generate_presigned_url("get_object",
        Params={"Bucket":BUCKET_NAME,"Key":f"{user}/{filename}"},
        ExpiresIn=60)
    return jsonify({"url":url})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)

