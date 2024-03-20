from flask import Flask, render_template, request, redirect, flash, make_response, url_for, jsonify
import json
import jwt
import os
import datetime
import hashlib
from PIL import Image, TiffImagePlugin
import io
from PIL.ExifTags import TAGS
import shutil
from moviepy.editor import *
from moviepy.video.fx.all import fadein, fadeout
import numpy as np
from sqlalchemy import text, create_engine

engine = create_engine("cockroachdb://gautam:OgK0JBPMybWsoHdwFPPQfQ@existentia-8949.8nk.gcp-asia-southeast1.cockroachlabs.cloud:26257/existentia?sslmode=verify-full&sslrootcert=root.crt")

def hashed(s):
	pb = s.encode('utf-8')
	hash_object = hashlib.sha256(pb)
	hex_dig = hash_object.hexdigest()
	return hex_dig

def initialise_database():
    with engine.connect() as db:
        db.execute(text("CREATE TABLE IF NOT EXISTS users(name VARCHAR(255), username VARCHAR(255), password VARCHAR(255), email VARCHAR(255), PRIMARY KEY(username))"))
        db.commit()
        db.execute(text("CREATE TABLE IF NOT EXISTS images(username VARCHAR(255), image_id SERIAL, image BYTEA, metadata TEXT, FOREIGN KEY(username) REFERENCES users(username))"))
        db.commit()
        db.execute(text("CREATE TABLE IF NOT EXISTS audios(username VARCHAR(255), audio_id SERIAL, audio BYTEA, metadata TEXT, FOREIGN KEY(username) REFERENCES users(username))"))
        db.commit()
        x = db.execute(text("SELECT * FROM users WHERE username = 'admin'")).mappings().all()
        if len(x) == 0:
            db.execute(text("INSERT INTO users VALUES('Administrator', 'admin', :p, 'administrator@existentia.com')"), {"p": hashed("admin")})
        db.commit()

initialise_database()

app = Flask(__name__)

if os.path.exists("./uploads"):
	app.config['UPLOAD_FOLDER'] = "./uploads"
else:
	os.mkdir("./uploads")
	app.config['UPLOAD_FOLDER'] = "./uploads"
 
if not os.path.exists("./static/videos"):
	os.mkdir("./static/videos")
     
if not os.path.exists("./static/images"):
    os.mkdir("./static/images")

if not os.path.exists("./static/renders"):
    os.mkdir("./static/renders")

app.secret_key = "SECRET_KEY_EXISTENTIA"

users = []
images = []
audios = []

def getfromdatabase():  
    global users, images, audios
    with engine.connect() as db:
        db.commit()
        users = db.execute(text("SELECT * FROM users")).mappings().all()
        db.commit()
        images = db.execute(text("SELECT username, image_id, metadata FROM images")).mappings().all()
        db.commit()
        audios = db.execute(text("SELECT username, audio_id, metadata FROM audios")).mappings().all()
        db.commit()

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
    with engine.connect() as db:
        db.commit()
        userimages = db.execute(text("SELECT image_id FROM images WHERE username = :u"), {"u": username}).mappings().all()
        db.commit()
    numfiles = len(os.listdir("./static/renders"))	
    if numfiles != 0 :
        for file in os.listdir("./static/renders"):
            if file.startswith(username):
                if(len(userimages) == numfiles):

                    return render_template("home.html", source_file = os.listdir("./static/renders"),username=username, num_images = len(os.listdir("./static/renders")))

                else:
                    erasedirectory("./static/renders")
                    return redirect("/home", 301)				
            os.remove(f"./static/renders/{file}")
    else:
        if username == "":
            return "null username"
        with engine.connect() as db:
            pictures = db.execute(text("SELECT image, image_id from images WHERE username = :u"), {"u": username}).mappings().all()
            db.commit()
        for picture in pictures:
            img = Image.open(io.BytesIO(picture['image']))
            img.save(f"./static/renders/{username}_{picture['image_id']}.png")

    return render_template("home.html", source_file = os.listdir("./static/renders"), username = username, num_images = len(os.listdir("./static/renders")))


@app.route("/requestlogin", methods = ['POST'])
def processloginrequest():
    if request.method == 'POST':
        global username
        username = request.form["username"]
        print(username)
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
            with engine.connect() as db:
                db.execute(text("INSERT INTO users VALUES(:n, :u, :p, :e)"), {"n": name, "u": username, "p": hashed(password), "e": email})
                db.commit()
                users = db.execute(text("SELECT * FROM users")).mappings().all()
                db.commit()
            return redirect("/login", 301)

@app.route("/admin")
def admin():
    global users, images, audios
    nums = []
    for i in range(len(users)):
        nums.append(0)
    for index, user in enumerate(users):
        for image in images:
            if image["username"] == user["username"]:
                nums[index] += 1
    return render_template("admin.html", userlist = users, numimages = nums)
    # return [users, images, audios]

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
    global username
    if username == "":
        return "null username"
    image_folder = './static/images'
    image_files = [f for f in os.listdir(image_folder) if os.path.isfile(os.path.join(image_folder, f))]
    return render_template('video.html', image_files=image_files)

img_durations = []

@app.route("/ready_to_preview", methods=['POST', 'GET'])
def videopreview():
    global username
    
    durations = {}
    global img_durations
    img_durations.clear()
    if request.method == 'POST':
        selected_song = request.form.get('song')
        selected_transition=request.form.get('transition')
        selected_resolution = request.form.get('resolution') 
        if selected_song =="0":
            audiofpath = './static/music/Happy_birthday_to_you_MIDI(chosic.com).mp3'
        elif selected_song:
            audiofpath = selected_song.strip()
        
        if selected_transition:
            selected_transition.strip()
        for key, value in request.form.items():
            if key.startswith('duration_'):
                durations[key.split('_')[-1]] = float(value) if value else 2.0  # Default duration is 2 seconds if not specified
                img_durations.append(durations[key.split('_')[-1]])
    image_folder = './static/images'
    image_files = [f for f in os.listdir(image_folder) if os.path.isfile(os.path.join(image_folder, f))]
    path = './static/images'
    output = './static/videos'
    nameof_video = '/final.mp4'
    outputpath = output + nameof_video
    imageslist = os.listdir(path)
    if not imageslist:
        return render_template('video.html', video_html="<h1>No images found!</h1>")
    j = 0
    for i in imageslist:
        i = path + '/' + i
        imageslist[j] = i
        j += 1
    image_arrays_resized = []
    for image_path in image_files:
        try:
            img = Image.open(os.path.join(path, image_path))
            
            if selected_resolution == '1':
                resized_img = img.resize((426,240))
            elif selected_resolution == '2':
                resized_img = img.resize((854,480))
            elif selected_resolution == '3':
                resized_img = img.resize((1280,720))
            elif selected_resolution == '4':
                resized_img = img.resize((1920,1080))
            
            if resized_img.mode == 'RGBA':
                resized_img = resized_img.convert('RGB')
            image_arrays_resized.append(np.array(resized_img))
        except (FileNotFoundError, IOError) as e:
            print(f"Error loading image: {image_path} ")
    transition_duration = 0.3
    clips_with_transitions = []
    if not img_durations:
        return f"Error: No image durations specified."
    if selected_transition=="crossfade":
        for i in range(len(image_arrays_resized)):
            clip = ImageClip(image_arrays_resized[i], duration=img_durations[i])
            if i > 0:
                clip = fadein(clip, duration=transition_duration)
            if i < len(image_arrays_resized) - 1:
                clip = fadeout(clip, duration=transition_duration)
            clips_with_transitions.append(clip)
    elif selected_transition=="fade_in":
        for i in range(len(image_arrays_resized)):
            clip = ImageClip(image_arrays_resized[i], duration=img_durations[i])
            if i > 0:
                clip = fadein(clip, duration=transition_duration)
            clips_with_transitions.append(clip)
    elif selected_transition=="fade_out":
        if(len(image_arrays_resized)==1):
            clip = ImageClip(image_arrays_resized[0], duration=img_durations[0])
            clip = fadeout(clip, duration=transition_duration)
            clips_with_transitions.append(clip)
        else:
            for i in range(len(image_arrays_resized)):
                clip = ImageClip(image_arrays_resized[i], duration=img_durations[i])
                if i < len(image_arrays_resized) - 1:
                    clip = fadeout(clip, duration=transition_duration)
                clips_with_transitions.append(clip)

    elif selected_transition == "slidein":
        clips_with_transitions = []
        if len(image_arrays_resized) > 1:
            for i in range(0, len(image_arrays_resized)):
                clip = ImageClip(image_arrays_resized[i], duration=img_durations[i])
                clips_with_transitions.append(CompositeVideoClip([clip.fx(transfx.slide_in, duration=transition_duration, side="left").fx(transfx.crossfadeout, duration=transition_duration)]))
        else:
            clip=ImageClip(image_arrays_resized[0],duration=img_durations[0])
            clips_with_transitions.append(CompositeVideoClip([clip.fx(transfx.slide_in,duration=transition_duration, side="left")]))
    elif selected_transition == "slideout":
        clips_with_transitions = []
        if len(image_arrays_resized) > 1:
            for i in range(0, len(image_arrays_resized)):
                clip = ImageClip(image_arrays_resized[i], duration=img_durations[i])
                clips_with_transitions.append(CompositeVideoClip([clip.fx(transfx.slide_out, duration=transition_duration, side="left").fx(transfx.crossfadein, duration=transition_duration)]))
        else:
            clip=ImageClip(image_arrays_resized[0],duration=img_durations[0])
            clips_with_transitions.append(CompositeVideoClip([clip.fx(transfx.slide_out,duration=transition_duration, side="left")]))   
    final_clip = concatenate_videoclips(clips_with_transitions,method="compose")
    audio_bg = AudioFileClip(audiofpath)
    video_dur=final_clip.duration
    audio_dur=audio_bg.duration
    if(audio_dur>video_dur):
        audio_dur=video_dur

        audio_bg.duration=audio_dur
        
        final_clip=final_clip.set_audio(audio_bg)
    else:
        num_loops = int(video_dur / audio_dur)
        audio_clips = [audio_bg] * num_loops 
        leftover_duration = video_dur - (num_loops * audio_dur) 
        if leftover_duration > 0:  
            partial_audio_clip = audio_bg.subclip(0, leftover_duration)
            audio_clips.append(partial_audio_clip)
        looped_audio = concatenate_audioclips(audio_clips)
        final_clip = final_clip.set_audio(looped_audio)

    
    final_clip.write_videofile(outputpath, fps=24, remove_temp=True)
  
    video_html = f'''
    <div class="video_preview">
    <h2 class="mt-5">Video preview</h2>
    <div class="embed-responsive embed-responsive-16by9">
        <video width="600" height="400" controls>
            <source src="{url_for('static', filename='videos/final.mp4')}" type="video/mp4">
            Your browser does not support the video tag.
        </video>
    </div>
    <div>
    <h2 class="mb-3">Download Video</h2>
    <div class="container text-center">
        <a href="./static/videos/final.mp4" download>
            <button class="btn btn-outline-light btn-lg" >Download</button>
        </a>
    </div>
    <br>
    <br>
    <br>
    '''

    return render_template('video.html', video_html=video_html, image_files=image_files)

@app.route("/profile")
def profile():
    with engine.connect() as db:
        det = db.execute(text("SELECT name, email FROM users WHERE username = :u"), {"u": username}).mappings().first()
    return render_template("profile.html", username = username, name = det["name"], mail = det["email"])

@app.route("/uploadimages", methods = ["POST"])
def uploadimages():
    global images, username
    if request.method == 'POST':
        # return redirect("/decoy", 301)
        if 'file' not in request.files:
            flash('No file part')
            return redirect("/home", 301)
        files = request.files.getlist("file")
        # return str(len(files))
        if len(files) == 0:
            flash('No selected file')
            return redirect("/home", 301)
        for file in files:
            if file.filename == '':
                continue
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
                # "layers": img.n_frames, 
                "transparent_color": img.info.get("transparency"),    
            }
            metadata_json = json.dumps(metadata)
            with engine.connect() as db:
                db.execute(text("INSERT INTO images(username, image, metadata) VALUES(:u, :b, :m)"), {"u": username, "b": blob, "m": metadata_json})
                db.commit()
                images = db.execute(text("SELECT username, image_id, metadata FROM images")).mappings().all()
                db.commit()
        return redirect("/home", 301)

@app.route("/logout")
def logout_and_delete():
    image_folder = 'static/images'
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
    erasedirectory("./static/images")
    # Reset the global variable
    global username
    username = ""
    return response

@app.route("/decoy")
def dekoi():
    return render_template("decoy.html")
  
if __name__ == "_main_":
    app.run(port = os.environ["PORT"], host = '0.0.0.0')
