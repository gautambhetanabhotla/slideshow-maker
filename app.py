from flask import Flask, render_template, request, redirect, flash, make_response, url_for, jsonify
import json
import jwt
import pymysql
import pymysql.cursors
import os
import datetime
import hashlib
import cv2
from PIL import Image, TiffImagePlugin
import io
import sys
from PIL.ExifTags import TAGS
import shutil
import copy

dbusername = "root"
dbpassword = "password"

def hashed(s):
	pb = s.encode('utf-8')
	hash_object = hashlib.sha256(pb)
	hex_dig = hash_object.hexdigest()
	return hex_dig

def initialise_database():
	connection = pymysql.connect(host='localhost', user=dbusername, password=dbpassword)
	db = connection.cursor(pymysql.cursors.DictCursor)
	db.execute("CREATE DATABASE IF NOT EXISTS existentia")
	connection.commit()
	db.execute("USE existentia")
	connection.commit()
	db.execute("CREATE TABLE IF NOT EXISTS users(name VARCHAR(255), username VARCHAR(255), password VARCHAR(255), email VARCHAR(255), PRIMARY KEY(username))")
	connection.commit()
	db.execute("CREATE TABLE IF NOT EXISTS images(username VARCHAR(255), image_id INT, image LONGBLOB, metadata TEXT, FOREIGN KEY(username) REFERENCES users(username))")
	connection.commit()
	db.execute("CREATE TABLE IF NOT EXISTS audios(username VARCHAR(255), audio_id INT, audio LONGBLOB, metadata TEXT, FOREIGN KEY(username) REFERENCES users(username))")
	connection.commit()
	db.close()
	connection.close()

initialise_database()
app = Flask(__name__)

if os.path.exists("./uploads"):
	app.config['UPLOAD_FOLDER'] = "./uploads"
else:
	os.mkdir("./uploads")
	app.config['UPLOAD_FOLDER'] = "./uploads"

app.secret_key = "SECRET_KEY_EXISTENTIA"

users = []
images = []
audios = []

def getfromdatabase():
	global users, images, audios
	connection2 = pymysql.connect(host='localhost', user=dbusername, password=dbpassword)
	db2 = connection2.cursor(pymysql.cursors.DictCursor)
	db2.execute("USE existentia")
	connection2.commit()
	db2.execute("SELECT * FROM users")
	users = db2.fetchall()
	connection2.commit()
	db2.execute("SELECT username, image_id, metadata FROM images")
	images = db2.fetchall()
	connection2.commit()
	db2.execute("SELECT username, audio_id, metadata FROM audios")
	audios = db2.fetchall()
	connection2.commit()
	db2.close()
	connection2.close()

getfromdatabase()

username = ""

def erasedirectory(path):
	for file in os.listdir(path):
		os.remove(path + "/" + file)

@app.route("/")
def rootpage():
	return render_template("root.html")

@app.route("/login")
def login():
    global username
    # Check if JWT token is present in the request cookies
    token = request.cookies.get('jwt_token')
    if token:
        try:
            # Decode the JWT token
            decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            username = decoded_token['username']
            # Verify the user's credentials
            if username == 'admin':
                return redirect("/admin")
            else:
                for user in users:
                    if user["username"] == username:
                        return redirect("/home")	
                else:
                    username = ""
                    return render_template("login.html")
        except jwt.ExpiredSignatureError:
            # Token has expired
            return render_template("login.html")
        except jwt.InvalidTokenError:
            # Invalid token
            return "invalid token"
    # Redirect to login page if no token is present
    return render_template("login.html")

@app.route("/signup")
def signup():
    token = request.cookies.get('jwt_token')
    if token:
        response = make_response(render_template("signup.html"))
        response.delete_cookie('jwt_token')
        return response
    
    return render_template("signup.html")
@app.route("/home")
def home():
	if not os.path.exists("./static/renders"):
		os.mkdir("./static/renders")
	global username
	connection3 = pymysql.connect(host='localhost', user=dbusername, password=dbpassword)
	db3 = connection3.cursor(pymysql.cursors.DictCursor)
	db3.execute("USE existentia")
	connection3.commit()
	db3.execute("SELECT image_id FROM images WHERE username = %s", (username))
	userimages = db3.fetchall()
	connection3.commit()
	db3.close()
	connection3.close()
	numfiles = len(os.listdir("./static/renders"))
	
		
	if numfiles != 0 :
		for file in os.listdir("./static/renders"):
			if username == "":
				return "null username"
			if file.startswith(username):
				if(len(userimages) == numfiles):
					return render_template("home.html", source_file = os.listdir("./static/renders"),username=username)
				else:
					erasedirectory("./static/renders")
					return redirect("/home", 301)				
			os.remove(f"./static/renders/{file}")
	else:
		if username == "":
			return "null username"
		connection4 = pymysql.connect(host='localhost', user=dbusername, password=dbpassword)
		db4 = connection4.cursor(pymysql.cursors.DictCursor)
		db4.execute("USE existentia")
		connection4.commit()
		db4.execute("SELECT image, image_id from images WHERE username = %s", (username))
		pictures = db4.fetchall()
		connection4.commit()
		db4.close()
		connection4.close()
		for picture in pictures:
			img = Image.open(io.BytesIO(picture['image']))
			img.save(f"./static/renders/{username}_{picture['image_id']}.png")
	return render_template("home.html", source_file = os.listdir("./static/renders"))

@app.route("/requestlogin", methods = ['POST'])
def processloginrequest():
    if request.method == 'POST':
        global username
        username = request.form["username"]
        password = request.form["password"]
        for user in users:
            if user["username"] == username and user["password"] == hashed(password):
                token = jwt.encode({'username': username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
                resp = make_response(redirect("/home" if username != "admin" else "/admin", 301))
                resp.set_cookie('jwt_token', token)
                return resp
        else:
            return redirect("/login", 301)
	
@app.route("/requestsignup", methods = ['POST'])
def processsignuprequest():
	global users
	if request.method == 'POST':
		username = request.form["username"]
		password = request.form["password"]
		email = request.form["email"]
		name = request.form["name"]
		for user in users:
			if user["username"] == username:
				flash("An account with this username already exists. Please choose a different username.")
				return render_template("signup.html")
		else:
			connection5 = pymysql.connect(host='localhost', user=dbusername, password='password')
			db5 = connection5.cursor(pymysql.cursors.DictCursor)
			db5.execute("USE existentia")
			connection5.commit()
			db5.execute("INSERT INTO users VALUES(%s, %s, %s, %s)", (name, username, hashed(password), email))
			connection5.commit()
			db5.execute("SELECT * FROM users")
			users = db5.fetchall()
			connection5.commit()
			db5.close()
			connection5.close()
			return redirect("/login", 301)

@app.route("/admin")
def admin():
	global users, images, audios
	return [users, images, audios]

@app.route('/move_files', methods=['POST'])
def move_files():
    data = request.get_json()
    files = data.get('files', [])
    destination_folder = './static/images'  # Specify the destination folder
    
    for file_name in files:
        source_path = os.path.join('./static/renders', file_name)  # Specify the source folder
        destination_path = os.path.join(destination_folder, file_name)
        shutil.move(source_path, destination_path)
    
    return jsonify({'message': 'Files moved successfully'})

@app.route("/video", methods = ['POST', 'GET'])
def video():
    image_folder = './static/images'
    image_files = [f for f in os.listdir(image_folder) if os.path.isfile(os.path.join(image_folder, f))]
    return render_template('video.html', image_files=image_files)
    

@app.route("/profile")
def profile():
    connection6 = pymysql.connect(host='localhost', user=dbusername, password=dbpassword)
    db6 = connection6.cursor(pymysql.cursors.DictCursor)
    db6.execute("USE existentia")
    connection6.commit()
    db6.execute("SELECT name FROM users WHERE username=%s",(username))
    Name=db6.fetchone()
    connection6.commit()
    db6.execute("SELECT email FROM users WHERE username=%s",(username))
    Mail=db6.fetchone()
    connection6.commit()
    db6.close()
    connection6.close()
    return render_template("profile.html",username=username,name=Name["name"],mail=Mail["email"])

@app.route("/uploadimages", methods = ["POST"])
def uploadimages():
    global images, username
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect("/home", 301)
        
        files = request.files.getlist("file")
        
        if len(files) == 0:
            flash('No selected file')
            return redirect("/home", 301)
        
        for file in files:
            if file.filename == '':
                flash('No selected file')
                return redirect("/home", 301)
            
            blob = file.read()
            
            
            img = Image.open(io.BytesIO(blob))
            metadata = {
    "width": img.width,
    "height": img.height,
    "format": img.format,
    "mode": img.mode,  
    "dpi": img.info.get("dpi"), 
    "compression": img.info.get("compression"), 
    "exif": img.info.get("exif"),
    "icc_profile": img.info.get("icc_profile"), 
    "transparency": img.info.get("transparency"), 
    "color_palette": img.palette, 
    "layers": img.n_frames, 
    "transparent_color": img.info.get("transparency"), 
    
}

            metadata_json = json.dumps(metadata)
            
            
            connection = pymysql.connect(host='localhost', user=dbusername, password=dbpassword)
            if not connection.open:
                return "null connection"
            
            db = connection.cursor(pymysql.cursors.DictCursor)
            db.execute("USE existentia")
            db.execute("INSERT INTO images VALUES(%s, %s, %s, %s)", (username, int(len(images)) + 1, blob, metadata_json))
            connection.commit()
            
           
            db.execute("SELECT username, image_id, metadata FROM images")
            images = db.fetchall()
            connection.commit()
            
            db.close()
            connection.close()
        
        return redirect("/home", 301)

@app.route("/logout")
def logout_and_delete():
    image_folder = 'static/images'
    
    # Delete all files in the images folder
    for filename in os.listdir(image_folder):
        file_path = os.path.join(image_folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")
    
    # Delete the JWT token cookie
    response = redirect("/")
    response.delete_cookie('jwt_token')
    
    # Delete all files in the renders folder
    erasedirectory("./static/renders")
    
    # Reset the global variable
    global username
    username = ""
    
    return response

@app.route("/deleteimages", methods = ["POST", "GET"])
def deleteimages():
	global username
	if request.method == 'POST':
		return "post request"
	elif request.method == 'GET':
		return jsonify(request)
	else:
		return str(request.method)

if __name__ == "__main__":
	app.run(debug = True)