HarvardEats

HarvardEats is a web app that allows Harvard students to discover, review and find their favorite spots around Harvard Square. The app is made by Harvard students for Harvard students because each rating is provided and tailored for life on campus. 

Features

Havard only access system: to access the other features the user must register with a "@college.harvard.edu" email

User Accounts: users have an account to access their own favorite spots, write reviews, and for general access. Passwords are hashed using Werkzeug. 

Reviews: Users can leave reviews and ratings on the restaurants. They can also view other ratings to figure out where to go. 

Favorites: Users can select their favorite restaurants to appear in a personal list

Interactive Map: There is a map centered on Harvard Yard that displays markers that have popups with each restaurants information and link to its details

Filters: Spots are given tags depending on their qualities like proximity to Harvard, affordability etc. 

Homepage: The homepage displays the top rated spots first.

Administrator Mode: With a specific login there is an admin mode that allows that user to edit and manage each spot and review. This can be done by adding directly 

Tech Stack:
Backend is done through Flask and Python
The database is stored through SQLite
Authentication is with Werkzeug password hashing and session logins
Frontend is dont using HTML, Jinja, and CSS
The map is from Leaflet and OpenStreetMap tiles
The hosting of ther server is through PythonAnywhere 
The version control is through GitHub

To run the project localy first clone the repository from github using the following lines inputting your own username

git clone https://github.com/yourusernameharvard-eats.git

Then create and activate your own virtual environment using the following lines depending on the device. 

python3 -m venv venv
source venv/bin/activate   # Mac
venv\Scripts\activate      # Windows

Then install all of the requirements

pip install -r requirements.txt

Then run the app!
python app.py

If you want to view the app online follow this link. 
https://alexsavov.pythonanywhere.com/

To fully access the features create an admin account through SQL with the following line. 

UPDATE users SET is_admin = 1 WHERE username = 'your_admin_username';

The python version 3.9.6

User Manual

To begin the user should open the website and click register to create an account. To do this they should enter a Harvard email ending in @college.harvard.edu and choose a username and password. This would reject any none Harvard email. Then you will need to log in with the information that you just created. From there you have access to all of the website. On the homepage there is a list of the highest rated spots that is automatically updated when the reviews change. First to view the features click on on Spots to see the map. From there you can search of filter for a restaurant that you are looking for. You may also use the map to click on a spot to view more detials. If you find a spot that you like that is a little further from the Yard but is worth entering you can add your own spot by entering its name, location, and any relevant tags. The main feature however is to leave a review. After visiting a spot pull up the website and and search for the spot you just went to. From there enter a rating and a review. These appear instantly with your username and rating. To view all of your reviews go to your reviews page. If you really likea a spot you can add it to your favorites and view it any time from the favorites tab. If you are logged into an admin account you can edit the page chaning the name, category, coordinates and tags. it also allows you to delete a spot or a review. If your friend wants to log into their own account you can log out and repeat the process. 




