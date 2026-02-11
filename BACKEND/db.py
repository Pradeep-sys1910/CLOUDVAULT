from flask_mysqldb import MySQL
from flask import Flask

mysql = MySQL()

def init_db(app):
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'root123'
    app.config['MYSQL_DB'] = 'cloudvault'

    mysql.init_app(app)
