import sqlite3

DB_NAME = "poi_cache.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def add_poi(name, raw_category, friendly_category, lat, lon, avg_dwell_time=60, rating=0):
    """
    Insert a POI into the poi_cache table.
    """
    conn = sqlite3.connect("poi_cache.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO poi_cache (name, raw_category, friendly_category, lat, lon, avg_dwell_time, rating)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, raw_category, friendly_category, lat, lon, avg_dwell_time, rating))

    conn.commit()
    conn.close()

def get_poi_by_name(name):
    """
    Fetch a POI by name (partial match allowed).
    Returns (id, name, friendly_category, lat, lon, avg_dwell_time, rating) or None.
    """
    conn = sqlite3.connect("poi_cache.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, friendly_category, lat, lon, avg_dwell_time, rating
        FROM poi_cache
        WHERE name LIKE ?
    """, (f"%{name}%",))
    row = cursor.fetchone()
    conn.close()
    return row

    
# -------------------------------
# USER PREFERENCES FUNCTIONS
# -------------------------------
def add_user_pref(user_id, poi_id, priority=3, time_spent=60):
    """
    Store user preference for a POI.
    priority: 1 (high) → 5 (low)
    time_spent: expected minutes at POI
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO UserPrefs (user_id, poi_id, priority, time_spent)
        VALUES (?, ?, ?, ?)
    """, (user_id, poi_id, priority, time_spent))
    conn.commit()
    conn.close()

def get_user_prefs(user_id):
    """
    Fetch preferences for a given user.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT UP.poi_id, P.name, UP.priority, UP.time_spent
        FROM UserPrefs UP
        JOIN POIs P ON UP.poi_id = P.id
        WHERE user_id = ?
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# -------------------------------
# HISTORY FUNCTIONS
# -------------------------------
def log_visit(user_id, poi_id, actual_time):
    """
    Log an actual visit by the user.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO History (user_id, poi_id, actual_time)
        VALUES (?, ?, ?)
    """, (user_id, poi_id, actual_time))
    conn.commit()
    conn.close()

def get_user_history(user_id):
    """
    Fetch all POIs visited by a user.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT H.poi_id, P.name, H.actual_time, H.visit_time
        FROM History H
        JOIN POIs P ON H.poi_id = P.id
        WHERE user_id = ?
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows
