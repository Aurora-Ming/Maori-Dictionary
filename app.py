import os
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
        print("teacher not in")
        return False


@app.route('/', methods=['post', 'get'])
def render_homepage():
    return render_template('home.html', logged_in=is_logged_in(), teacher_in=teacher_logged_in())


@app.route('/category_list')
def render_category():
    db = get_db()
    categories = db.execute('SELECT * FROM category').fetchall()
    # get categories from database
    return render_template('category_list.html', logged_in=is_logged_in(), categories=categories,
                           teacher_in=teacher_logged_in())


@app.route('/category_detail/<int:cat_id>')
def category_detail(cat_id):
    db = get_db()
    words = db.execute('SELECT * FROM vocab_list WHERE cat_id = ?', (cat_id,)).fetchall()
    category_name = db.execute('SELECT * FROM Category WHERE cat_id = ?', (cat_id,)).fetchone()[1]
    # Extract all the words under that category from the database
    return render_template('category_detail.html', category_name=category_name, words=words)


@app.route('/word/<int:word_id>')
def word_detail(word_id):
    db = get_db()
    word = db.execute('SELECT * FROM vocab_list WHERE word_id = ?', (word_id,)).fetchone()
    editor_id = word['editor_id']
    editor = db.execute('SELECT fname FROM user WHERE user_id = ?', (editor_id,)).fetchone()
    cat_id = word['cat_id']
    category = db.execute('SELECT cat_name FROM category WHERE cat_id = ?', (cat_id,)).fetchone()
    # get all the details of the word from the database
    return render_template('word_detail.html', word=word, logged_in=is_logged_in()
                           , teacher_in=teacher_logged_in(), editor=editor, category=category)


@app.route('/word/<int:word_id>/delete', methods=['POST'])
def delete_word(word_id):
    db = get_db()
    db.execute('DELETE FROM vocab_list WHERE word_id = ?', (word_id,))
    db.commit()
    # delete word
    return redirect("/")


@app.route('/list')
def render_list():
    db = get_db()
    words = db.execute('SELECT * FROM vocab_list').fetchall()
    word_list = []
    for word in words:
        editor_id = word['editor_id']
        editor = db.execute('SELECT fname FROM user WHERE user_id = ?', (editor_id,)).fetchone()
        cat_id = word['cat_id']
        category = db.execute('SELECT cat_name FROM category WHERE cat_id = ?', (cat_id,)).fetchone()
        word_list.append((word, editor, category))
        # get all the words and their details from the database
    return render_template('list.html', word_list=word_list, logged_in=is_logged_in(), teacher_in=teacher_logged_in())


@app.route('/login', methods=['POST', 'GET'])
def render_login():
    if is_logged_in():
        print("logged_in")
        return redirect('/')
    # Determine whether the user has logged in
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
        # Extract user data from the database
        try:
            user_id = user_data[0]
            first_name = user_data[1]
            db_password = user_data[2]
            account_type = user_data[3]
        except IndexError:
            return redirect("/login?error=Invalid+username+or+password")

        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + "?error=Email+invalid+or+password incorrect")
        # Check whether the password is correct
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
        # Record user data
        if password != password2:
            return redirect("/signup?error=Password+do+not+match")

        if len(password) < 8:
            return redirect("/signup?error=Password+must+be+at+least+8+characters")

        hashed_password = bcrypt.generate_password_hash(password)  # Encrypt a password
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
    db = get_db()
    words = db.execute('SELECT * FROM vocab_list').fetchall()
    categories = db.execute('SELECT * FROM category').fetchall()
    # get words and categories from database
    return render_template("admin.html", logged_in=is_logged_in(), teacher_in=teacher_logged_in(), words=words,
                           categories=categories)


@app.route("/add_word", methods=['POST'])
def add_word():
    db = get_db()
    maori = request.form.get('Maori')
    english = request.form.get('English')
    cat_id = request.form.get('cat_id')
    definition = request.form.get('Definition')
    level = request.form.get('Level')
    editor_id = session.get("user_id")
    print(maori, english, cat_id, definition, level, editor_id)
    image = "noimage.png"
    # get word's data
    db.execute("INSERT INTO vocab_list(Maori, English, cat_id, Definition, Level, editor_id,images)"
               " VALUES (?, ?, ?,?, ?, ?,?)",
               (maori, english, cat_id, definition, level, editor_id, image))
    db.commit()
    return redirect('/list')


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
       maori=request.form.get('maori')
       english=request.form.get('english')
       return render_template('search_results.html', maori=maori, english=english)
    return render_template('search.html')


@app.route('/search_results')
def search_results():
    db=get_db()
    maori = request.args.get('maori')
    english = request.args.get('english')
    if maori and not english:
        results = db.execute('SELECT * FROM vocab_list WHERE Maori LIKE ?', ('%{}%'.format(maori),)).fetchall()
    elif english and not maori:
        results = db.execute('SELECT * FROM vocab_list WHERE English LIKE ?', ('%{}%'.format(english),)).fetchall()
    elif maori and english:
        results = db.execute('SELECT * FROM vocab_list WHERE Maori LIKE ? AND English LIKE ?',
                             ('%{}%'.format(maori), '%{}%'.format(english))).fetchall()
    else:
        results = []
    return render_template('search_results.html', results=results)

app.run(host='0.0.0.0', debug=True)
