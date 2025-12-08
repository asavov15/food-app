-- USERS TABLE --------------------------------------
-- Stores login accounts with Harvard email requirement
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,         -- must end @college.harvard.edu
    username TEXT UNIQUE NOT NULL,
    hash TEXT NOT NULL,                 -- password hash (Werkzeug)
    is_admin INTEGER DEFAULT 0          -- admin privileges for edit/delete
);

-- SPOTS TABLE --------------------------------------
-- Stores each restaurant/food place added by users
-- Includes boolean tag fields and geolocation
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

-- REVIEWS TABLE ------------------------------------
-- Stores user reviews for each spot
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

-- FAVORITES TABLE ----------------------------------
-- Many-to-many: which users bookmarked which spots
CREATE TABLE IF NOT EXISTS favorites (
    user_id INTEGER NOT NULL,
    spot_id INTEGER NOT NULL,
    UNIQUE(user_id, spot_id),           -- prevents duplicate favorites

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (spot_id) REFERENCES spots(id)
);
