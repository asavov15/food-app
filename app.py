import sqlite3
from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import math

# Flask app setup
app = Flask(__name__)

# Secret key used for session cookies
app.secret_key = "dev-secret-change-later"

# Database helper - open a connection to the SQLite database and return it

def get_db():
    connection = sqlite3.connect("spots.db")
    connection.row_factory = sqlite3.Row
    return connection

# Registration (Harvard email required, username & email must be unique, password hashed)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")

        # Check that user provided Harvard email
        if not email or not email.endswith("@college.harvard.edu"):
            return render_template(
                "register.html",
                error="You must register with a Harvard college email address.",
            )

        # Basic check for username and password
        if not username or not password:
            return render_template("register.html", error="All fields are required.")

        db = get_db()

        # Check email is not already registered
        exists_email = db.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        if exists_email:
            db.close()
            return render_template("register.html", error="Email already registered.")

        # Check that username is not already taken
        exists_username = db.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if exists_username:
            db.close()
            return render_template("register.html", error="Username already taken.")

        # Hash the password
        hashed = generate_password_hash(password)

        # Insert the new user into the database
        db.execute(
            "INSERT INTO users (email, username, hash) VALUES (?, ?, ?)",
            (email, username, hashed),
        )
        db.commit()
        db.close()

        # After successfully registering, send the user to the login page
        return redirect(url_for("login"))

    # Show the registration form (GET)
    return render_template("register.html")

# Login & logout

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        db = get_db()
        user = db.execute(
            "SELECT id, username, hash, is_admin FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        db.close()

        # If there is no user with that username, show error
        if user is None:
            return "Invalid username or password", 400

        # Check that the entered password matches the stored hash
        if not check_password_hash(user["hash"], password):
            return "Invalid username or password", 400

        # Save user info in the session 
        session["user_id"] = user["id"]
        session["username"] = user["username"]

        session["is_admin"] = user["is_admin"]

        # Redirect to homepage after login
        return redirect(url_for("index"))

    # Show the login form (GET)
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# Home page showing top rated spots

@app.route("/")
def index():
    db = get_db()
    spots = db.execute(
        """
        SELECT
            spots.id,
            spots.name,
            spots.category,
            ROUND(AVG(reviews.rating), 1) AS avg_rating,
            COUNT(reviews.id) AS review_count
        FROM spots
        LEFT JOIN reviews ON reviews.spot_id = spots.id
        GROUP BY spots.id
        HAVING review_count > 0
        ORDER BY avg_rating DESC, review_count DESC
        LIMIT 5
        """
    ).fetchall()

    db.close()
    return render_template("index.html", spots=spots)


# Spots list and map (includes filters for text query, min rating, and tags)

@app.route("/spots")
def spots():
   
    # Require login
    if not session.get("user_id"):
        return redirect(url_for("login"))

    # Query parameters from the URL (search box)
    q = request.args.get("q")          
    min_rating = request.args.get("min_rating") 

    # Tag filters (checkboxes)
    late_night = request.args.get("late_night")
    fine_dining = request.args.get("fine_dining")
    health_conscious = request.args.get("health_conscious")
    affordable = request.args.get("affordable")
    sweet_treat = request.args.get("sweet_treat")
    close_tag = request.args.get("close")

    db = get_db()

    # Base query selects spots and aggregated rating info
    query = """
        SELECT
            spots.id,
            spots.name,
            spots.category,
            spots.latitude,
            spots.longitude,
            spots.late_night,
            spots.fine_dining,
            spots.health_conscious,
            spots.affordable,
            spots.sweet_treat,
            spots.close,
            ROUND(AVG(reviews.rating), 1) AS avg_rating,
            COUNT(reviews.id) AS review_count
        FROM spots
        LEFT JOIN reviews ON reviews.spot_id = spots.id
    """

    conditions = []
    params = []

    # Text search - matches name or category using LIKE
    if q:
        conditions.append("(spots.name LIKE ? OR spots.category LIKE ?)")
        like_term = f"%{q}%"
        params.extend([like_term, like_term])

    # Tag filters - each checked box means we restrict to spots where that flag is 1
    if late_night:
        conditions.append("spots.late_night = 1")
    if fine_dining:
        conditions.append("spots.fine_dining = 1")
    if health_conscious:
        conditions.append("spots.health_conscious = 1")
    if affordable:
        conditions.append("spots.affordable = 1")
    if sweet_treat:
        conditions.append("spots.sweet_treat = 1")
    if close_tag:
        conditions.append("spots.close = 1")

    # If there are any filters, add a WHERE clause
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    # Group by spot so we can use AVG and COUNT on reviews
    query += " GROUP BY spots.id"

    # Minimum rating filter is a HAVING on the aggregated avg_rating
    if min_rating:
        query += " HAVING avg_rating >= ?"
        params.append(float(min_rating))

    # Order alphabetically by spot name
    query += " ORDER BY spots.name"

    rows = db.execute(query, params).fetchall()
    db.close()

    # Build data for the map (JSON sent to the front end)
    spot_data = []
    for s in rows:
        spot_data.append({
            "id": s["id"],
            "name": s["name"],
            "category": s["category"],
            "latitude": s["latitude"],
            "longitude": s["longitude"],
            "avg_rating": s["avg_rating"],
            "review_count": s["review_count"],
            "late_night": s["late_night"],
            "fine_dining": s["fine_dining"],
            "health_conscious": s["health_conscious"],
            "affordable": s["affordable"],
            "sweet_treat": s["sweet_treat"],
            "close": s["close"],
        })

    return render_template("spots.html", spots=rows, spot_data=spot_data)


# Spot detail page - list basic info and ratings and reviews

@app.route("/spot/<int:spot_id>")
def spot_detail(spot_id):
    
    # Require login
    if not session.get("user_id"):
        return redirect(url_for("login"))

    db = get_db()
    # Load the spot, including tag flags
    spot = db.execute(
        """
        SELECT
            id,
            name,
            category,
            latitude,
            longitude,
            late_night,
            fine_dining,
            health_conscious,
            affordable,
            sweet_treat,
            close
        FROM spots
        WHERE id = ?
        """,
        (spot_id,),
    ).fetchone()

    # Load all reviews for this spot with the review author's username
    reviews = db.execute(
        """
        SELECT reviews.rating,
               reviews.text,
               users.username
        FROM reviews
        LEFT JOIN users ON reviews.user_id = users.id
        WHERE reviews.spot_id = ?
        ORDER BY reviews.id DESC
        """,
        (spot_id,),
    ).fetchall()

    # Calculate average rating and total review count for the spot
    avg_row = db.execute(
        """
        SELECT ROUND(AVG(rating), 1) AS avg_rating,
               COUNT(*) AS review_count
        FROM reviews
        WHERE spot_id = ?
        """,
        (spot_id,),
    ).fetchone()

    avg_rating = avg_row["avg_rating"]
    review_count = avg_row["review_count"]

    # Check if the current user has this spot in favorites
    is_favorite = False
    if session.get("user_id") and spot is not None:
        fav = db.execute(
            "SELECT 1 FROM favorites WHERE user_id = ? AND spot_id = ?",
            (session["user_id"], spot_id),
        ).fetchone()
        is_favorite = fav is not None

    db.close()

    if spot is None:
        return "Spot not found", 404

    return render_template(
        "spot_detail.html",
        spot=spot,
        reviews=reviews,
        is_favorite=is_favorite,
        avg_rating=avg_rating,
        review_count=review_count,
    )

# Add review for a spot

@app.route("/spot/<int:spot_id>/review", methods=["POST"])
def add_review(spot_id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    rating = request.form.get("rating")
    text = request.form.get("text")

    db = get_db()
    db.execute(
        "INSERT INTO reviews (spot_id, rating, text, user_id) VALUES (?, ?, ?, ?)",
        (spot_id, rating, text, session["user_id"]),
    )
    db.commit()
    db.close()

    return redirect(f"/spot/{spot_id}")

# Add a new spot

@app.route("/add-spot", methods=["GET", "POST"])
def add_spot():
   
    if not session.get("user_id"):
        return redirect(url_for("login"))

    if request.method == "POST":
        # Get data from the form
        name = request.form.get("name")
        category = request.form.get("category")
        latitude_raw = request.form.get("latitude")
        longitude_raw = request.form.get("longitude")

        # Require a name for the spot
        if not name:
            return "Name is required", 400

        # Convert latitude and longitude to float
        lat = float(latitude_raw) if latitude_raw else None
        lon = float(longitude_raw) if longitude_raw else None

        # Tag flags from checkboxes (presence of key in form means checked)
        late_night = 1 if request.form.get("late_night") else 0
        fine_dining = 1 if request.form.get("fine_dining") else 0
        health_conscious = 1 if request.form.get("health_conscious") else 0
        affordable = 1 if request.form.get("affordable") else 0
        sweet_treat = 1 if request.form.get("sweet_treat") else 0

        # Insert the new spot into the database
        db = get_db()
        db.execute(
            """
            INSERT INTO spots
                (name, category, latitude, longitude,
                 late_night, fine_dining, health_conscious,
                 affordable, sweet_treat, close)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                category,
                lat,
                lon,
                late_night,
                fine_dining,
                health_conscious,
                affordable,
                sweet_treat,
                close_flag,
            ),
        )
        db.commit()
        db.close()

        # Redirect back to the full spots list
        return redirect("/spots")

    # Show the add spot form (GET)
    return render_template("add_spot.html")


# Edit and delete spots (admin only)

@app.route("/spot/<int:spot_id>/edit", methods=["GET", "POST"])
def edit_spot(spot_id):
   
    if not session.get("is_admin"):
        return "Access denied", 403

    db = get_db()

    if request.method == "POST":
        name = request.form.get("name")
        category = request.form.get("category")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        # Checkbox logic for tag flags
        late_night = 1 if request.form.get("late_night") else 0
        fine_dining = 1 if request.form.get("fine_dining") else 0
        health_conscious = 1 if request.form.get("health_conscious") else 0
        affordable = 1 if request.form.get("affordable") else 0
        sweet_treat = 1 if request.form.get("sweet_treat") else 0
        close_tag = 1 if request.form.get("close") else 0

        if not name:
            db.close()
            return "Name is required", 400

        # Update the spot with the new data
        db.execute(
            """
            UPDATE spots
            SET name = ?, category = ?, latitude = ?, longitude = ?,
                late_night = ?, fine_dining = ?, health_conscious = ?,
                affordable = ?, sweet_treat = ?, close = ?
            WHERE id = ?
            """,
            (
                name,
                category,
                latitude,
                longitude,
                late_night,
                fine_dining,
                health_conscious,
                affordable,
                sweet_treat,
                close_tag,
                spot_id,
            ),
        )
        db.commit()
        db.close()

        return redirect(f"/spot/{spot_id}")

    # Load the existing spot data into the form (GET)
    spot = db.execute(
        "SELECT id, name, category, latitude, longitude FROM spots WHERE id = ?",
        (spot_id,),
    ).fetchone()
    db.close()

    if spot is None:
        return "Spot not found", 404

    return render_template("edit_spot.html", spot=spot)


# Delete spot
@app.route("/spot/<int:spot_id>/delete", methods=["POST"])
def delete_spot(spot_id):
    
    if not session.get("is_admin"):
        return "Access denied", 403

    db = get_db()

    # Remove reviews for this spot first
    db.execute("DELETE FROM reviews WHERE spot_id = ?", (spot_id,))

    # Remove the spot itself
    db.execute("DELETE FROM spots WHERE id = ?", (spot_id,))

    db.commit()
    db.close()

    return redirect("/spots")


# My Reviews

@app.route("/my-reviews")
def my_reviews():

    if not session.get("user_id"):
        return redirect(url_for("login"))

    db = get_db()
    reviews = db.execute(
        """
        SELECT
            reviews.id,
            reviews.rating,
            reviews.text,
            reviews.created_at,
            spots.id AS spot_id,
            spots.name AS spot_name
        FROM reviews
        JOIN spots ON reviews.spot_id = spots.id
        WHERE reviews.user_id = ?
        ORDER BY reviews.created_at DESC
        """,
        (session["user_id"],),
    ).fetchall()
    db.close()

    return render_template("my_reviews.html", reviews=reviews)


# Create favorite spot

@app.route("/spot/<int:spot_id>/favorite", methods=["POST"])
def favorite_spot(spot_id):
    
    if not session.get("user_id"):
        return redirect(url_for("login"))

    db = get_db()
    db.execute(
        "INSERT OR IGNORE INTO favorites (user_id, spot_id) VALUES (?, ?)",
        (session["user_id"], spot_id),
    )
    db.commit()
    db.close()

    return redirect(f"/spot/{spot_id}")

# Unfavorite a spot

@app.route("/spot/<int:spot_id>/unfavorite", methods=["POST"])
def unfavorite_spot(spot_id):
    
    if not session.get("user_id"):
        return redirect(url_for("login"))

    db = get_db()
    db.execute(
        "DELETE FROM favorites WHERE user_id = ? AND spot_id = ?",
        (session["user_id"], spot_id),
    )
    db.commit()
    db.close()

    return redirect(f"/spot/{spot_id}")

# Show favorites

@app.route("/favorites")
def favorites():

    if not session.get("user_id"):
        return redirect(url_for("login"))

    db = get_db()
    spots = db.execute(
        """
        SELECT spots.id, spots.name, spots.category
        FROM favorites
        JOIN spots ON favorites.spot_id = spots.id
        WHERE favorites.user_id = ?
        ORDER BY spots.name
        """,
        (session["user_id"],),
    ).fetchall()
    db.close()

    return render_template("favorites.html", spots=spots)


# Local development entry point

if __name__ == "__main__":
    # debug=True enables hot reload and better error messages in development
    app.run(debug=True)
