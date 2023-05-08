import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from flask import Flask, render_template, request, redirect, session, app, g

DATABASE = "dictionary.db"
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "66666"


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


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


def is_logged_in():
    if session.get("email") is None:
        print("not logged in")
        return False
    else:
        print("logged in")
        return True


def teacher_logged_in():
    if session.get("account_type") == "teacher":
        print("teacher in")
        return True
    else:
        print("student in")
        return False


@app.route('/', methods=['post', 'get'])
def render_homepage():
    return render_template('home.html', logged_in=is_logged_in(), teacher_in=teacher_logged_in())




@app.route('/category_list')
def render_category():
    db = get_db()
    categories = db.execute('SELECT * FROM category').fetchall()
    return render_template('category_list.html', logged_in=is_logged_in(), categories=categories,
                           teacher_in=teacher_logged_in())


@app.route('/category_detail/<int:cat_id>')
def category_detail(cat_id):
    db = get_db()
    words = db.execute('SELECT * FROM vocab_list WHERE cat_id = ?', (cat_id,)).fetchall()
    category_name = db.execute('SELECT * FROM Category WHERE cat_id = ?', (cat_id,)).fetchone()[1]
    return render_template('category_detail.html', category_name=category_name, words=words)


@app.route('/word/<int:word_id>')
def word_detail(word_id):
    db = get_db()
    word = db.execute('SELECT * FROM vocab_list WHERE word_id = ?', (word_id,)).fetchone()
    return render_template('word_detail.html', word=word, logged_in=is_logged_in()
                           , teacher_in=teacher_logged_in())


@app.route('/list')
def render_list():
    db = get_db()
    words = db.execute('SELECT * FROM vocab_list').fetchall()
    return render_template('list.html', words=words, logged_in=is_logged_in(), teacher_in=teacher_logged_in())


@app.route('/login', methods=['POST', 'GET'])
def render_login():
    if is_logged_in():
        print("logged_in")
        return redirect('/')
    print('Logging in')
    if request.method == "POST":
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()

        query = "SELECT user_id,fname,password,account_type FROM user WHERE email=?"
        con = create_connection(DATABASE)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchone()
        con.close()

        try:
            user_id = user_data[0]
            first_name = user_data[1]
            db_password = user_data[2]
            account_type = user_data[3]
        except IndexError:
            return redirect("/login?error=Invalid+username+or+password")

        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + "?error=Email+invalid+or+password incorrect")

        session['email'] = email
        session['firstname'] = first_name
        session['user_id'] = user_id
        session['account_type'] = account_type
        print(session)
        return redirect('/')
    return render_template("login.html", logged_in=is_logged_in(), teacher_in=teacher_logged_in())


@app.route('/logout')
def logout():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect('/?message=See+you+next+time!')


@app.route("/signup", methods=['POST', 'GET'])
def render_signup(cur=None):
    if is_logged_in():
        return redirect('/')
    if request.method == 'POST':

        fname = request.form.get('fname').title().strip()
        lname = request.form.get('lname').title().strip()
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')
        account_type = request.form.get('account_type')

        if password != password2:
            return redirect("/signup?error=Password+do+not+match")

        if len(password) < 8:
            return redirect("/signup?error=Password+must+be+at+least+8+characters")

        hashed_password = bcrypt.generate_password_hash(password)
        con = create_connection(DATABASE)
        query = "INSERT INTO user(fname, lname,email,password,account_type) VALUES (?,?,?,?,?)"
        cur = con.cursor()
        try:
            cur.execute(query, (fname, lname, email, hashed_password, account_type))
        except sqlite3.IntegrityError:
            con.close()
            return redirect('/signup?error=Email+is+already+used')

        con.commit()
        con.close()

        return redirect("/login")
    return render_template("signup.html", logged_in=is_logged_in(), teacher_in=teacher_logged_in())


@app.route("/admin")
def render_admin():
    if not is_logged_in():
        return redirect('/?message=Need+to+be+logged+in.')
    con = create_connection(DATABASE)
    query = "SELECT * FROM vocab_list"
    cur = con.cursor()
    cur.execute(query)
    words = cur.fetchall()
    con.close
    return render_template("admin.html", logged_in=is_logged_in(), categories=category, teacher_in=teacher_logged_in(),
                           word=words)


app.run(host='0.0.0.0', debug=True)
