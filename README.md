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
- User authentication is now token-based (more specifically, JSON Web tokens).
- User, image and audio data is stored in a local MySQL database, on the hosting server.
- The hosting which was supposed to be done on flask was implemented during milestone 1 itself.