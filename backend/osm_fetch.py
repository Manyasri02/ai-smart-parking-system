print("✅ OSM FETCH FILE LOADED")

import requests
from backend.database import get_db_connection

OVERPASS_URL = "https://overpass-api.de/api/interpreter"



# FETCH RAW PARKING FROM OSM

def fetch_osm_parkings(lat, lon, radius=500):

    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="parking"](around:{radius},{lat},{lon});
      way["amenity"="parking"](around:{radius},{lat},{lon});
      relation["amenity"="parking"](around:{radius},{lat},{lon});
    );
    out center tags;
    """

    try:
        response = requests.post(
            OVERPASS_URL,
            data=query,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        return data.get("elements", [])

    except requests.exceptions.Timeout:
        print("❌ OSM timeout — retrying with smaller radius...")
        return fetch_osm_parkings(lat, lon, radius=300)

    except Exception as e:
        print("❌ OSM fetch error:", e)
        return []



# --------------------------------------------------
# INSERT PARKING INTO DATABASE
# --------------------------------------------------

def fetch_parking_data(lat: float, lon: float, radius: int = 5000):
    """
    Fetch parking near user and store into database
    """

    elements = fetch_osm_parkings(lat, lon, radius)

    if not elements:
        print("⚠ No parking data received from OSM")
        return []

    conn = get_db_connection()
    cursor = conn.cursor()

    inserted = []

    for element in elements:
        tags = element.get("tags", {})

        # -----------------------------
        # 📛 Parking name generation
        # -----------------------------
        parking_type = tags.get("parking", "public")
        capacity = tags.get("capacity")

        if tags.get("name"):
            name = tags["name"]

        elif capacity:
            name = f"{parking_type.title()} Parking ({capacity} slots)"

        else:
            name = f"{parking_type.title()} Parking Area"

        # -----------------------------
        # 📍 Coordinates
        # -----------------------------
        plat = element.get("lat") or element.get("center", {}).get("lat")
        plon = element.get("lon") or element.get("center", {}).get("lon")

        if plat is None or plon is None:
            continue

        # Round coordinates to avoid duplicate precision mismatch
        location = f"{round(plat,6)},{round(plon,6)}"

        # -----------------------------
        # 🚗 Capacity estimation
        # -----------------------------
        try:
            total_slots = int(capacity) if capacity else 50
        except:
            total_slots = 50

        available_slots = int(total_slots * 0.6)  # simulated

        # -----------------------------
        # ✅ Update existing parking or insert new
        # -----------------------------
        cursor.execute(
            "SELECT id FROM parking_lots WHERE location = ?",
            (location,)
        )
        existing = cursor.fetchone()

        if existing:
            # Update existing record
            cursor.execute("""
                UPDATE parking_lots
                SET name = ?, total_slots = ?, available_slots = ?
                WHERE location = ?
            """, (
                name,
                total_slots,
                available_slots,
                location
            ))
        else:
            # Insert new parking
            cursor.execute("""
                INSERT INTO parking_lots
                (name, location, total_slots, available_slots)
                VALUES (?, ?, ?, ?)
            """, (
                name,
                location,
                total_slots,
                available_slots
            ))

        inserted.append({
            "name": name,
            "location": location,
            "total_slots": total_slots,
            "available_slots": available_slots
        })

    conn.commit()
    conn.close()

    print(f"✅ Inserted {len(inserted)} new parking records")
    return inserted
