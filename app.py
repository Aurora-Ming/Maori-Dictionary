import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from flask import Flask, render_template, request, redirect, session, app

DATABASE = "dictionary.db"
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "66666"


def create_connection(db_file):
    """
        creat a connection with the database
        parameter: name of the database file
        returns:a connection to the file
        """
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
    return None


@app.route('/')
def render_homepage():
    con = create_connection(DATABASE)
    query = " SELECT Maori ,  English , Category , Level , Definition FROM vocab_list "
    cur = con.cursor()
    cur.execute(query,)
    vocabs_list = cur.fetchall()
    return render_template('home.html',vocabs=vocabs_list)


@app.route('/category')
def render_category_Page():

    return render_template('category.html')


@app.route('/login')
def render_login_page():
    return render_template('login.html')


app.run(host='0.0.0.0', debug=True)
