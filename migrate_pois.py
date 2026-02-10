import sqlite3

DB_NAME = "poi_cache.db"

def migrate_pois():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Fetch all rows from POIs
    cursor.execute("SELECT name, category, lat, lon, avg_dwell_time, rating FROM POIs;")
    rows = cursor.fetchall()

    print(f"Found {len(rows)} rows in POIs...")

    for row in rows:
        name, category, lat, lon, avg_dwell_time, rating = row

        # Insert into poi_cache
        cursor.execute("""
            INSERT INTO poi_cache (name, raw_category, friendly_category, lat, lon, avg_dwell_time, rating)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, category, category, lat, lon, avg_dwell_time, rating))

    conn.commit()
    conn.close()
    print("✅ Migration complete! All POIs copied into poi_cache.")

if __name__ == "__main__":
    migrate_pois()
