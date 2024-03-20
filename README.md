[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-24ddc0f5d75046c5622901739e7c5dd533143b0c8e959d652212380cedb1ea36.svg)](https://classroom.github.com/a/M9yOg1uw)

<br>

# Milestone 1
- As of the milestone 1 deadline, the website features a login page, a signup page and a home page, featuring user authentication.
- Passwords are currently stored as plain text. This will be changed in the future.
- The home page features the actual functionality of the website. Users can drag and drop image files onto the browser.
- The web application is currently running on flask.
- User data is stored in `users.json`.
- The admin page is not a separate html file, but on logging in as admin, you will be able to see all user details.

<br>

# Milestone 2
- Passwords are stored in the database in SHSA256 hashed format.
- User authentication is now token-based (JSON Web tokens).
- User, image and audio data is stored in a local MySQL database.
- The hosting which was supposed to be done on flask was implemented during milestone 1 itself.

<br>

# Milestone 3
- User, image and audio data is now stored on an online PostgreSQL database.
- The web app is now hosted on Render.
- On selecting images, you will be redirected to a page where you can add audio to the video, set individual durations of each of the images, and choose a transition effect between the images.
- On clicking the "Upload" button on the home page, you will have to manually reload the page for the results to show. Clicking the button multiple times before refreshing will upload the same set of images multiple times.
