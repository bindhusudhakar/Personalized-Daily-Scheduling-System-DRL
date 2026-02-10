# database_setup.py
import sqlite3

# Connect (creates new DB if it doesn’t exist)
DB_NAME = "poi_cache.db"
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# ----------------------------
# 1. POIs Table (main reference)
# ----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS poi_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    raw_category TEXT,         -- From Google API
    friendly_category TEXT,    -- User-friendly label
    lat REAL,
    lon REAL,
    avg_dwell_time INTEGER,    -- minutes
    rating REAL,
    last_fetched TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

# ----------------------------
# 2. User Preferences Table
# ----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS UserPrefs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    poi_id INTEGER,
    priority INTEGER,         -- 1 (high) to 5 (low)
    time_spent INTEGER,       -- minutes
    FOREIGN KEY (poi_id) REFERENCES poi_cache(id)
);
""")

# ----------------------------
# 3. History Table (track visits)
# ----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS History (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    poi_id INTEGER,
    visited_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id INTEGER,
    planned_time INTEGER,     -- minutes
    actual_time INTEGER,      -- minutes
    feedback TEXT,
    FOREIGN KEY (poi_id) REFERENCES poi_cache(id)
);
""")

# ----------------------------
# 4. Sessions Table (per schedule plan)
# ----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS Sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    mode_of_transport TEXT,   -- driving/walking/transit/etc
    total_time INTEGER,       -- planned total duration
    is_completed INTEGER DEFAULT 0
);
""")

# ----------------------------
# 5. Ratings Table (optional user ratings)
# ----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS Ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    poi_id INTEGER,
    rating INTEGER CHECK(rating >=1 AND rating <=5),
    review TEXT,
    rated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (poi_id) REFERENCES poi_cache(id)
);
""")

conn.commit()
conn.close()

print("✅ Database and tables created successfully!")