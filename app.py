from flask import Flask, render_template, request, redirect, url_for, flash,make_response,jsonify
from flask_session import Session
import json
import jwt
import pymysql
import pymysql.cursors
import os
import datetime
import hashlib

def hashed(s):
	pb = s.encode('utf-8')
	hash_object = hashlib.sha256(pb)
	hex_dig = hash_object.hexdigest()
	return hex_dig

connection = pymysql.connect(host='localhost', user='ravi', password='password')
db = connection.cursor(pymysql.cursors.DictCursor)
db.execute("CREATE DATABASE IF NOT EXISTS existentia")
db.execute("USE existentia")
db.execute("CREATE TABLE IF NOT EXISTS users(name VARCHAR(255), username VARCHAR(255), password VARCHAR(255), email VARCHAR(255), PRIMARY KEY(username))")
db.execute("CREATE TABLE IF NOT EXISTS images(username VARCHAR(255), image_id INT, image BLOB, FOREIGN KEY(username) REFERENCES users(username))")
db.execute("CREATE TABLE IF NOT EXISTS audios(audio BLOB, username VARCHAR(255), FOREIGN KEY(username) REFERENCES users(username))")
connection.commit()

app = Flask(__name__)
db.execute("SELECT * FROM users")
users = db.fetchall()
if os.path.exists("./uploads"):
	app.config['UPLOAD_FOLDER'] = "./uploads"
else:
	os.mkdir("./uploads")
	app.config['UPLOAD_FOLDER'] = "./uploads"

app.secret_key = "SECRET_KEY_EXISTENTIA"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/")
def rootpage():
    
    
	return render_template("root.html")

@app.route("/login")
def login():
        # Check if JWT token is present in the request cookies
    token = request.cookies.get('jwt_token')

    if token:
        try:
            # Decode the JWT token
            decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            username = decoded_token['username']

            # Verify the user's credentials
            for user in users:
                if user["username"] == username:
                    return redirect("/home")

            # If user not found, redirect to login page
            return render_template("login.html")

        except jwt.ExpiredSignatureError:
            # Token has expired
            return render_template("login.html")
        except jwt.InvalidTokenError:
            # Invalid token
            return render_template("login.html")

    # Redirect to login page if no token is present
    return render_template("/login", 301)
	

@app.route("/signup")
def signup():
	return render_template("signup.html")

@app.route("/home")
def home():
		return render_template("home.html")

@app.route("/requestlogin", methods = ['POST'])
def processloginrequest():
	if request.method == 'POST':
		username = request.form["username"]
		password = request.form["password"]
		
	

		for user in users:
			if user["username"] == username and user["password"] == password:
				token = jwt.encode({'username': username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
				resp = make_response(redirect("/home" if username != "admin" else "/admin", 301))
				resp.set_cookie('jwt_token', token)
				return resp


	
@app.route("/requestsignup", methods = ['POST'])
def processsignuprequest():
	if request.method == 'POST':
		username = request.form["username"]
		password = request.form["password"]
		email = request.form["email"]
		name = request.form["name"]
		for user in users:
			if user["username"] == username:
				flash("An account with this username already exists. Please choose a different username.")
				return render_template("/signup", 301)
		else:
			db.execute("INSERT INTO users VALUES(%s, %s, %s, %s)", (name, username, hashed(password), email))
			connection.commit()
			return redirect("/login", 301)

@app.route("/admin")
def admin():
	return users

@app.route("/video")
def video():
		return render_template("video.html")

@app.route("/upload", methods = ["POST", "GET"])
def upload():
	if request.method == 'POST':
		if 'file' not in request.files:
			flash('No file part')
			return redirect("/home", 301)
		files = request.files.getlist("file")
		for file in files:
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        # If the user does not select a file, the browser submits an
        # empty file without a filename
		if file.filename == '':
			flash('No selected file')
			return render_template("/home", 301)
		if file:
			filename = file.filename
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			return os.path.join(app.config['UPLOAD_FOLDER'], filename)
	if request.method == "GET":
		return render_template("/home", 301)

if __name__ == "__main__":
	app.run(debug = True)