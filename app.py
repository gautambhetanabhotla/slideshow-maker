from flask import Flask, render_template, request, redirect
import json
import hashlib

app = Flask(__name__)
users = json.load(open("data/users.json"))

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
def processrequest():
	if request.method == 'POST':
		username = request.form["username"]
		password = request.form["password"]
		for user in users:
			if user["username"] == username and user["password"] == password:
				return redirect("/home", 301)
		else:
			return redirect("/login", 301)
		
@app.route("/requestsignup", methods = ['POST'])
def processsignuprequest():
	if request.method == 'POST':
		username = request.form["username"]
		password = request.form["password"]
		for user in users:
			if user["username"] == username:
				return redirect("/signup", 301)
		else:
			users.append({"username": username, "password": password})
			json.dump(users, open("data/users.json", "w"))
			return redirect("/login", 301)

if __name__ == "__main__":
	app.run(debug = True)