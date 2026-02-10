import sqlite3

DB_NAME = "poi_cache.db"

def test_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Create a new session for user 'user1'
    cursor.execute("""
    INSERT INTO Sessions (user_id, total_pois, total_time, notes)
    VALUES (?, ?, ?, ?)
    """, ("user1", 2, 180, "Weekend test session"))
    session_id = cursor.lastrowid
    print(f"🆕 New Session ID: {session_id}")

    # 2. Insert a User Preference (assuming Cubbon Park POI exists with id=1)
    cursor.execute("""
    INSERT INTO UserPrefs (user_id, poi_id, priority, time_spent)
    VALUES (?, ?, ?, ?)
    """, ("user1", 1, 1, 90))
    pref_id = cursor.lastrowid
    print(f"⭐ User Preference ID: {pref_id}")

    # 3. Insert into History (user visited Cubbon Park in this session)
    cursor.execute("""
    INSERT INTO History (user_id, poi_id, session_id, planned_time, actual_time, feedback)
    VALUES (?, ?, ?, ?, ?, ?)
    """, ("user123", 1, session_id, 60, 75, "Great visit"))  

    history_id = cursor.lastrowid
    print(f"📌 History Entry ID: {history_id}")

    conn.commit()

    # Fetch back to confirm
    cursor.execute("SELECT * FROM Sessions WHERE id=?", (session_id,))
    print("Session Row:", cursor.fetchone())

    cursor.execute("SELECT * FROM UserPrefs WHERE id=?", (pref_id,))
    print("UserPref Row:", cursor.fetchone())

    cursor.execute("SELECT * FROM History WHERE id=?", (history_id,))
    print("History Row:", cursor.fetchone())

    conn.close()
    print("✅ Test completed successfully!")

if __name__ == "__main__":
    test_database()