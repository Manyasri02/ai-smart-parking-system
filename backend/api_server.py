from fastapi import FastAPI, HTTPException
from backend.database import get_db_connection
from backend.schemas.parking_lot import ParkingLotCreate,ParkingLotUpdate
from backend.llm_client import build_prompt,generate_text
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from backend.osm_fetch import fetch_parking_data,fetch_osm_parkings
from math import radians, cos, sin, sqrt, atan2
import random

class ParkingRequest(BaseModel):
    parking_data: List[Dict[str, Any]]

class RecommendRequest(BaseModel):
    lat: float
    lon: float

def generate_llm_reason(parking_data: dict) -> str:
    # TEMP fallback logic
    return "Recommended based on availability and distance"


app = FastAPI(title="AI Smart Parking Optimization System")

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parking_lots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            total_slots INTEGER NOT NULL,
            available_slots INTEGER NOT NULL
        )
    """)

    conn.commit()
    conn.close()


create_tables()

@app.post("/parking-lots/")
def create_parking_lot(parking_lot: ParkingLotCreate):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO parking_lots (name, location, total_slots, available_slots)
        VALUES (?, ?, ?, ?)
        """,
        (
            parking_lot.name,
            parking_lot.location,
            parking_lot.total_slots,
            parking_lot.total_slots
        )
    )

    conn.commit()
    conn.close()

    return {"message": "Parking lot created successfully"}


@app.get("/parking-lots/")
def get_all_parking_lots():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM parking_lots")
    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]


@app.get("/parking-lots/{parking_lot_id}")
def get_parking_lot_by_id(parking_lot_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM parking_lots WHERE id = ?",
        (parking_lot_id,)
    )
    row = cursor.fetchone()

    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Parking lot not found")

    return dict(row)

@app.put("/parking-lots/{parking_lot_id}")
def update_parking_lot(parking_lot_id: int, parking_lot: ParkingLotUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if parking lot exists
    cursor.execute(
        "SELECT * FROM parking_lots WHERE id = ?",
        (parking_lot_id,)
    )
    existing = cursor.fetchone()

    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Parking lot not found")

    cursor.execute(
        """
        UPDATE parking_lots
        SET name = ?, location = ?, total_slots = ?, available_slots = ?
        WHERE id = ?
        """,
        (
            parking_lot.name,
            parking_lot.location,
            parking_lot.total_slots,
            parking_lot.total_slots,  # reset available slots
            parking_lot_id
        )
    )

    conn.commit()
    conn.close()

    return {"message": "Parking lot updated successfully"}



@app.delete("/parking-lots/{parking_lot_id}")
def delete_parking_lot(parking_lot_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM parking_lots WHERE id = ?",
        (parking_lot_id,)
    )
    existing = cursor.fetchone()

    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Parking lot not found")

    cursor.execute(
        "DELETE FROM parking_lots WHERE id = ?",
        (parking_lot_id,)
    )

    conn.commit()
    conn.close()

    return {"message": "Parking lot deleted successfully"}


@app.post("/recommend")
def recommend(lat: float, lon: float):

    # 1️⃣ Fetch & store nearby parking
    fetch_parking_data(lat, lon)

    # 2️⃣ Read parking lots from DB
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM parking_lots
        ORDER BY available_slots DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="No parking found")

    parking_lots = [dict(row) for row in rows]

    # 3️⃣ LLM reasoning
    prompt = build_prompt(parking_lots)
    llm_result = generate_text(prompt)

    # 4️⃣ Fallback if LLM fails
    if not llm_result:
        best = parking_lots[0]
        return {
            "recommended_parking": best,
            "reason": "Rule-based fallback (highest availability)"
        }

    selected_id = llm_result["id"]
    reason = llm_result["reason"]

    selected = next(
        (p for p in parking_lots if p["id"] == selected_id),
        parking_lots[0]
    )

    return {
        "recommended_parking": selected,
        "reason": reason
    }




def simulate_live_availability():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, total_slots FROM parking_lots")
    rows = cursor.fetchall()

    for row in rows:
        new_available = random.randint(0, row["total_slots"])

        cursor.execute("""
            UPDATE parking_lots
            SET available_slots = ?
            WHERE id = ?
        """, (new_available, row["id"]))

    conn.commit()
    conn.close()

@app.get("/nearby-parking")
def get_nearby_parking(lat: float, lon: float):
    """
    Fetch nearby parking based on user location,
    store in DB, simulate live availability,
    and return nearby parking list
    """

    # 1️⃣ Fetch fresh parking from OSM using user location
    fetch_parking_data(lat, lon)

    # 2️⃣ Simulate real-time availability
    simulate_live_availability()

    # 3️⃣ Get parking from DB
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM parking_lots
        ORDER BY available_slots DESC
        LIMIT 20
    """)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return []

    return [dict(row) for row in rows]

