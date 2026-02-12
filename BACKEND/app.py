from flask_cors import CORS
from s3_config import s3, BUCKET_NAME
from flask import Flask, request, jsonify
from db import init_db, mysql
import bcrypt
from flask_jwt_extended import JWTManager, create_access_token

app = Flask(__name__)
CORS(app)

init_db(app)

# JWT secret key
app.config["JWT_SECRET_KEY"] = "supersecretkey"
jwt = JWTManager(app)

# Home route
@app.route("/")
def home():
    return jsonify({"message": "CloudVault API Running 🚀"})


@app.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json(force=True)

        if not data:
            return jsonify({"error":"No data received"}),400

        name = data.get("name")
        email = data.get("email")
        password = data.get("password")

        if not name or not email or not password:
            return jsonify({"error":"All fields required"}),400

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cursor = mysql.connection.cursor()

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            return jsonify({"error": "Email already registered"}), 400

        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s,%s,%s)",
            (name, email, hashed_password)
        )

        mysql.connection.commit()
        cursor.close()

        return jsonify({"message":"User registered successfully!"}),201

    except Exception as e:
        print(e)
        return jsonify({"error":str(e)}),500



@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json(force=True)

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error":"Missing fields"}),400

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if not user:
            return jsonify({"error":"User not found"}),404

        stored_password = user[3].encode('utf-8')

        if bcrypt.checkpw(password.encode('utf-8'), stored_password):
            token = create_access_token(identity=email)
            return jsonify({"token":token}),200

        return jsonify({"error":"Invalid password"}),401

    except Exception as e:
        print(e)
        return jsonify({"error":str(e)}),500




# ☁️ FILE UPLOAD API
@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]

        s3.upload_fileobj(file, BUCKET_NAME, file.filename)

        file_url = f"https://{BUCKET_NAME}.s3.ap-south-1.amazonaws.com/{file.filename}"

        return jsonify({
            "message": "File uploaded successfully!",
            "file_url": file_url
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 📄 GET ALL FILES FROM S3
@app.route("/files", methods=["GET"])
def list_files():
    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME)

        files = []
        if "Contents" in response:
            for obj in response["Contents"]:
                files.append(obj["Key"])

        return jsonify(files)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🗑️ DELETE FILE FROM S3
@app.route("/delete/<filename>", methods=["DELETE"])
def delete_file(filename):
    try:
        s3.delete_object(Bucket=BUCKET_NAME, Key=filename)
        return jsonify({"message": "File deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
