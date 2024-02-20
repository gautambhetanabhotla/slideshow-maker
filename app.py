from flask import Flask, render_template, request, redirect, url_for, flash,make_response,jsonify
from flask_session import Session
import json
import jwt
import pymysql
import pymysql.cursors
import os
import datetime

connection = pymysql.connect(host='localhost', user='root', password='Aryamah@12')
db = connection.cursor()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

users = json.load(open("data/users.json"))
if os.path.exists("./uploads"):
	app.config['UPLOAD_FOLDER'] = "./uploads"
else:
	os.mkdir("./uploads")
	app.config['UPLOAD_FOLDER'] = "./uploads"


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
    return redirect("/login", 301)
	

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
		for user in users:
			if user["username"] == username:
				flash("An account with this username already exists. Please choose a different username.")
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