from flask import Flask, jsonify
from db import init_db, mysql

app = Flask(__name__)

# initialize database
init_db(app)

@app.route("/")
def home():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT 'Database Connected!'")
    result = cursor.fetchone()
    cursor.close()

    return jsonify({"message": result[0]})

if __name__ == "__main__":
    app.run(debug=True)
