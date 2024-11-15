from flask import Flask, render_template, request, url_for, flash, redirect, session
import pymysql.cursors
import re
from werkzeug.security import generate_password_hash, check_password_hash
from scrapper import scrape_job_offers

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'db'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'job_scraper'
app.config['SECRET_KEY'] = 'secret key'


# Initialisation de la connexion MySQL
def get_db_connection():
    conn = pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB'],
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == 'POST':
        email = request.form["email"]
        password = request.form["password"]
        confirmpassword = request.form["confirmpassword"]
        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        users = cursor.fetchone()
        if users:
            flash("Ce compte existe déjà !", 'info')
            return redirect(url_for('home') + '?signup=fail')
        elif not re.match(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash("Email invalide !", 'info')
            return redirect(url_for('home') + '?signup=fail')
        elif password != confirmpassword:
            flash("Les mots de passe ne correspondent pas !", 'info')
            return redirect(url_for('home') + '?signup=fail')
        else:
            cursor.execute('INSERT INTO Users (email, passwd) VALUES (%s, %s)', (email, hashed_password))
            conn.commit()
            conn.close()
            flash("Votre compte a été enregistré avec succès !", 'info')
            return redirect(url_for('home') + '?signup=success')

    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        user = request.form["identifiant"]
        password = request.form["password"]
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Users WHERE email = %s', user)
        users = cursor.fetchone()
        if users:
            user_pswd = users['passwd']
            if check_password_hash(user_pswd, password):
                session['loggedin'] = True
                session['Id'] = users['id']
                session['email'] = users['email']
                return redirect(url_for('accueil'))
            else:
                flash("Mot de passe incorrect !", 'info')
                return redirect(url_for('home') + '?login=fail')
        else:
            flash("Identifiant incorrect !", 'info')
            return redirect(url_for('home') + '?login=fail')
    return redirect(url_for('home'))


@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("home.html")


@app.route("/accueil", methods=["GET", "POST"])
def accueil():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM job_offers')
    jobs = cursor.fetchall()
    conn.close()
    return render_template("accueil.html", jobs=jobs)


@app.route('/scrape')
def scrape():
    scrape_job_offers()
    return "Scraping job has been executed."


@app.route("/logout")
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('email', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
