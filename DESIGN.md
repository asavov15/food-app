HarvardEats is a Flask web application that allows Harvard students to find anad give reviews to spots near campus. The goal was to create a simple and intuitive platform for users to browse restaurants through the map and their preferences. The design document is mean to explain the choices in for each aspect such as database, HTML, routing, and other architectural aspects. 

Looking first at the architectural aspects it follows a standard pattern using Flask. It starts with the client loading the HTML, CSS, and Javascript which lets Flask run the routes that were made in python to gather the information from the SQLite database and complete all logic. From there Jinja templates render the HTML allowing users to view it. 

The backend was made using Python and Flask as that is what we learned in class but also functions as a simple yet effective approach to design. The database was done in SQLite because it does not need a serve and is lightweight. The frontend was done with the standard HTML using Jinja to help with templates for each page for layout. From there CSS was used to adjust features on all pages to make it more aesthetically pleasing. We had to learn new version control information to allow for hosting and collaborative working. Using PythonAnywhere you can host a server through a domain given to you. To use this you upload your code and access it through Github by pushing and pulling from there. 

The database was made in the following way. 

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,         -- must end @college.harvard.edu
    username TEXT UNIQUE NOT NULL,
    hash TEXT NOT NULL,                 -- password hash (Werkzeug)
    is_admin INTEGER DEFAULT 0          -- admin privileges for edit/delete
);

CREATE TABLE IF NOT EXISTS spots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    latitude REAL,
    longitude REAL,

    -- Food classification tags (1 = true)
    late_night INTEGER DEFAULT 0,
    fine_dining INTEGER DEFAULT 0,
    health_conscious INTEGER DEFAULT 0,
    affordable INTEGER DEFAULT 0,
    sweet_treat INTEGER DEFAULT 0,
    close INTEGER DEFAULT 0            -- computed via distance to Harvard Yard
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    spot_id INTEGER NOT NULL,
    user_id INTEGER,
    rating INTEGER NOT NULL,            -- 1–5 rating
    text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (spot_id) REFERENCES spots(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS favorites (
    user_id INTEGER NOT NULL,
    spot_id INTEGER NOT NULL,
    UNIQUE(user_id, spot_id),           -- prevents duplicate favorites

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (spot_id) REFERENCES spots(id)
);

There are certain features that differ from a basic database with values. The password is hashed using a security feature we saw in the Finance Pset. There is a flag in the users that if to determine if the user has admin priveleges since not all users should have access to deleting to spots. The tags are stored in boolean columns which allows for less complicated filtering. The favorites table uses a different design which allows for joining the information rather than storing it as a new entry. The reviews table looks at both the user and the spot to allow for tracking the history for each account. 

For the authentication and authorization of each user there can only be one user registered to a required @college.harvard.edu account. The passwords are hashed using Werkzeug to not store the actual information. The sessions are stored through the users id, username and checks to see if they are an admin. This flag is set through SQL manually to avoid people having access when they are not meant to. 

The application is mainly drive by the routes. The /register route validates the email checking the uniqueness and hashing the password. It then sends the user to the log in page because it forces the user to remember their login. The code uses the database and gathers information from it getting one at a time and giving error messages if something goes wrong. 

The /login gathers the data from the database and checks it to what the user enters which is given through the form. It then starts the session cookies for the user. 

The homepage is based on the basic layout template and displays the top 5 spots my getting their average rating and displaying their information. 

The /spots requires the user to be logged in and checks to see if the user input any filters. From there it queries for the spots and checks if they have the tags and groups the spots making it simpler display. 

The /spot/id route displays the information that was gathered when the user clicked the specific spot. It loads the reviews from the table and checks if the user has it in their favorite spots. 

The /add_spot inserts into the database based on the fields from the form allowing tags to be placed as well. 

The /spot/id/review gets the rating and text from the form and inserts it into the reviews table. 

The /spots/id/edit allows the user only if they are an admin to view this option. From there it gets the current information and allows the user to edit it and updates the table. 

The /spots/id/delete only works if the user is an admin. It first deletes the reviews because they would otherwise be lost. It then deletes the row in the table with the id from the route. 

The /my-reviews shows all the reviews from the user by joining the spots and the reviews on the users id. 

The /favorites route displays the users favorite spots by joining on the id of the spot and what is stored in the favorite. 

A unique aspect is the query building design. The /spots constructs the SQL dynamically based on the conditions which maintains the security because the parameters are not with the SQL statements. The filters are then done based on these requests. 


Tagging logic is done by storing the information as an integer of zero or one. This has boolean columbs instead of separate tags table to simplify filtering and reduce the join complexity. 

The frontend and UI is done using the layout.html as the main template. The style is done using CSS to format it following a minimalist approach. The buttons are upgraded to .btn-primary and .button-outline with the review cards again designed for readability. The map is integrated using Leaflet.js. The /spots route uses the spot_data as a JSON object and the javascript is able to render the markers creating a popup for each one. Clicking on the popup presents a link to the detail page. 

The deployment decisino was made looking for simplicity and ease. PythonAnywhere can run the server while GitHub handles the version control and the update that are pulled. 