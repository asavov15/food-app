import json
import sqlite3
import os

DB_PATH = "spots.db"
OSM_JSON_PATH = "harvard_spots.json"  # path to the file you downloaded


def classify_category(tags):
    """Map OSM amenity tags to your app's category field."""
    amenity = tags.get("amenity", "")
    if amenity == "cafe":
        return "Cafe"
    if amenity == "fast_food":
        return "Fast Food"
    if amenity == "ice_cream":
        return "Dessert"
    if amenity in ("pub", "bar"):
        return "Bar"
    return "Restaurant"


def main():
    print("Current working directory:", os.getcwd())
    print("Looking for JSON at:", OSM_JSON_PATH)
    if not os.path.exists(OSM_JSON_PATH):
        print("ERROR: JSON file not found.")
        return

    # Load OSM data
    print("Loading JSON...")
    with open(OSM_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    elements = data.get("elements", [])
    print("Total elements in JSON:", len(elements))

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    inserted = 0

    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue  # skip things without a name

        # Get lat/lon
        if el["type"] == "node":
            lat = el.get("lat")
            lon = el.get("lon")
        else:
            center = el.get("center")
            if not center:
                continue
            lat = center.get("lat")
            lon = center.get("lon")

        if lat is None or lon is None:
            continue

        category = classify_category(tags)

        cur.execute(
            """
            INSERT INTO spots (name, category, latitude, longitude)
            VALUES (?, ?, ? ,?)
            """,
            (name, category, lat, lon),
        )
        inserted += 1

    conn.commit()
    conn.close()

    print(f"Inserted {inserted} spots")


if __name__ == "__main__":
    main()
