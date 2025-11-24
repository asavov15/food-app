import sqlite3
from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = "dev-secret-change-later"

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return "Username and password required", 400

        db = get_db()

        # check if username already exists
        existing = db.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if existing is not None:
            db.close()
            return "Username already taken", 400

        hash_value = generate_password_hash(
            password,
            method="pbkdf2:sha256",
            salt_length=16
            )

        db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)",
            (username, hash_value)
        )
        db.commit()
        db.close()

        return redirect(url_for("login"))

    # GET: show the form
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        db = get_db()
        user = db.execute(
            "SELECT id, username, hash FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        db.close()

        if user is None:
            return "Invalid username or password", 400

        if not check_password_hash(user["hash"], password):
            return "Invalid username or password", 400

        # log the user in
        session["user_id"] = user["id"]
        session["username"] = user["username"]

        return redirect(url_for("index"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

def get_db():
    connection = sqlite3.connect("spots.db")
    connection.row_factory = sqlite3.Row  # lets us use column names later
    return connection

@app.route("/")
def index():
    db = get_db()
    spots = db.execute(
        "SELECT id, name, category FROM spots ORDER BY id DESC LIMIT 5"
    ).fetchall()
    db.close()
    return render_template("index.html", spots=spots)

@app.route("/spots")
def spots():
    q = request.args.get("q")  # search keyword
    min_rating = request.args.get("min_rating")  # minimum average rating

    db = get_db()

    query = """
        SELECT
            spots.id,
            spots.name,
            spots.category,
            ROUND(AVG(reviews.rating), 1) AS avg_rating,
            COUNT(reviews.id) AS review_count
        FROM spots
        LEFT JOIN reviews ON reviews.spot_id = spots.id
    """

    conditions = []
    params = []

    if q:
        conditions.append("(spots.name LIKE ? OR spots.category LIKE ?)")
        like_term = f"%{q}%"
        params.extend([like_term, like_term])

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " GROUP BY spots.id"

    # Filter by minimum rating if provided
    if min_rating:
        query += " HAVING avg_rating >= ?"
        params.append(float(min_rating))

    query += " ORDER BY spots.name"

    spots = db.execute(query, params).fetchall()
    db.close()

    return render_template("spots.html", spots=spots)



@app.route("/spot/<int:spot_id>")
def spot_detail(spot_id):
    db = get_db()
    spot = db.execute(
        "SELECT id, name, category, latitude, longitude FROM spots WHERE id = ?",
        (spot_id,)
    ).fetchone()

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
        (spot_id,)
    ).fetchall()

    avg_row = db.execute(
    "SELECT ROUND(AVG(rating), 1) AS avg_rating, COUNT(*) AS review_count FROM reviews WHERE spot_id = ?",
        (spot_id,)
        ).fetchone()

    avg_rating = avg_row["avg_rating"]
    review_count = avg_row["review_count"]


    is_favorite = False
    if session.get("user_id") and spot is not None:
        fav = db.execute(
            "SELECT 1 FROM favorites WHERE user_id = ? AND spot_id = ?",
            (session["user_id"], spot_id)
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
    review_count=review_count
)


@app.route("/spot/<int:spot_id>/review", methods=["POST"])
def add_review(spot_id):
    # Require login
    if not session.get("user_id"):
        return redirect(url_for("login"))

    rating = request.form.get("rating")
    text = request.form.get("text")

    db = get_db()
    db.execute(
        "INSERT INTO reviews (spot_id, rating, text, user_id) VALUES (?, ?, ?, ?)",
        (spot_id, rating, text, session["user_id"])
    )
    db.commit()
    db.close()

    return redirect(f"/spot/{spot_id}")


@app.route("/add-spot", methods=["GET", "POST"])
def add_spot():
    if request.method == "POST":
        # Get data from the form
        name = request.form.get("name")
        category = request.form.get("category")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        # Simple validation: require a name
        if not name:
            return "Name is required", 400

        # Insert into database
        db = get_db()
        db.execute(
            "INSERT INTO spots (name, category, latitude, longitude) VALUES (?, ?, ?, ?)",
            (name, category, latitude, longitude)
        )
        db.commit()
        db.close()

        # Redirect to the spots list
        return redirect("/spots")

    # If GET request, just show the form
    return render_template("add_spot.html")

@app.route("/spot/<int:spot_id>/edit", methods=["GET", "POST"])
def edit_spot(spot_id):
    db = get_db()

    if request.method == "POST":
        # Get updated values from the form
        name = request.form.get("name")
        category = request.form.get("category")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        if not name:
            db.close()
            return "Name is required", 400

        db.execute(
            "UPDATE spots SET name = ?, category = ?, latitude = ?, longitude = ? WHERE id = ?",
            (name, category, latitude, longitude, spot_id)
        )
        db.commit()
        db.close()

        return redirect(f"/spot/{spot_id}")

    # If GET, just show the existing data in the form
    spot = db.execute(
        "SELECT id, name, category, latitude, longitude FROM spots WHERE id = ?",
        (spot_id,)
    ).fetchone()
    db.close()

    if spot is None:
        return "Spot not found", 404

    return render_template("edit_spot.html", spot=spot)


@app.route("/spot/<int:spot_id>/delete", methods=["POST"])
def delete_spot(spot_id):
    db = get_db()

    # Remove reviews for this spot first (to keep DB clean)
    db.execute("DELETE FROM reviews WHERE spot_id = ?", (spot_id,))

    # Then remove the spot itself
    db.execute("DELETE FROM spots WHERE id = ?", (spot_id,))

    db.commit()
    db.close()

    return redirect("/spots")

@app.route("/my-reviews")
def my_reviews():
    # Require login
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
        (session["user_id"],)
    ).fetchall()
    db.close()

    return render_template("my_reviews.html", reviews=reviews)

@app.route("/spot/<int:spot_id>/favorite", methods=["POST"])
def favorite_spot(spot_id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    db = get_db()
    db.execute(
        "INSERT OR IGNORE INTO favorites (user_id, spot_id) VALUES (?, ?)",
        (session["user_id"], spot_id)
    )
    db.commit()
    db.close()

    return redirect(f"/spot/{spot_id}")


@app.route("/spot/<int:spot_id>/unfavorite", methods=["POST"])
def unfavorite_spot(spot_id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    db = get_db()
    db.execute(
        "DELETE FROM favorites WHERE user_id = ? AND spot_id = ?",
        (session["user_id"], spot_id)
    )
    db.commit()
    db.close()

    return redirect(f"/spot/{spot_id}")

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
        (session["user_id"],)
    ).fetchall()
    db.close()

    return render_template("favorites.html", spots=spots)

if __name__ == "__main__":
    app.run(debug=True)
