from flask import Flask, render_template, request, redirect, url_for, flash
from flask_session import Session
import json
import jwt
import pymysql
import pymysql.cursors
import os

connection = pymysql.connect(host='localhost', user='gautam', password='haha')
db = connection.cursor()

app = Flask(__name__)
users = json.load(open("data/users.json"))
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
	return render_template("login.html")

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
				if username != "admin":
					return redirect("/home", 301)
				else:
					return redirect("/admin", 301)
		else:
			return redirect("/login", 301)
		
@app.route("/requestsignup", methods = ['POST'])
def processsignuprequest():
	if request.method == 'POST':
		payload = {
			"username": request.form["username"],
			"password": request.form["password"]
		}
		# token = jwt.encode(payload, "_SECRET_KEY_EXISTENTIA_", algorithm = "HS256")
		# return token
		username = request.form["username"]
		password = request.form["password"]
		for user in users:
			if user["username"] == username:
				return redirect("/signup", 301)
		else:
			users.append({"username": username, "password": password})
			json.dump(users, open("data/users.json", "w"))
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
		file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename
		if file.filename == '':
			flash('No selected file')
			return redirect("/home", 301)
		if file:
			filename = file.filename
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			return os.path.join(app.config['UPLOAD_FOLDER'], filename)
	if request.method == "GET":
		return redirect("/home", 301)

if __name__ == "__main__":
	app.run(debug = True)