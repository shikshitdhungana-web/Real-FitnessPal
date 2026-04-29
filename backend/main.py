# ══════════════════════════════════════════════════════════════════
#  FitTrack Backend — FastAPI + SQLite
#  A simple REST API for the 12-week summer fitness tracker.
# ══════════════════════════════════════════════════════════════════
#
#  HOW TO INSTALL DEPENDENCIES
#  ─────────────────────────────
#  Open your terminal in this folder and run:
#
#      pip install -r requirements.txt
#
#  HOW TO RUN THE SERVER
#  ──────────────────────
#  After installing, start the server with:
#
#      uvicorn main:app --reload
#
#  The --reload flag makes the server restart automatically
#  whenever you save changes to main.py (handy during development).
#
#  Once running, you can visit:
#    • http://127.0.0.1:8000        → health check
#    • http://127.0.0.1:8000/docs   → interactive API docs (Swagger UI)
#
# ══════════════════════════════════════════════════════════════════

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel   # Pydantic validates the shape of incoming JSON
from typing import List, Optional
import sqlite3


# ──────────────────────────────────────────────────────────────────
#  CREATE THE FASTAPI APP
# ──────────────────────────────────────────────────────────────────

app = FastAPI(
    title="FitTrack API",
    description="Backend for the 12-Week Summer Fitness Tracker",
    version="1.0.0"
)


# ──────────────────────────────────────────────────────────────────
#  CORS SETUP
#  CORS (Cross-Origin Resource Sharing) tells the browser it's
#  allowed to make requests from your HTML file to this API.
#  Without this, the browser blocks the connection.
# ──────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Allow any origin (fine for local development).
                           # In production, replace "*" with your actual
                           # frontend URL, e.g. "https://mysite.com"
                           # NOTE: allow_credentials must NOT be True when
                           # allow_origins is "*" — browsers reject that combo.
    allow_methods=["*"],   # Allow GET, POST, DELETE, etc.
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────────
#  DATABASE SETUP
#  SQLite stores everything in a single file (workouts.db).
#  It's built into Python — no extra database server needed.
# ──────────────────────────────────────────────────────────────────

DATABASE = "workouts.db"   # The .db file will be created in this folder


def get_db():
    """Open and return a database connection.
    row_factory = sqlite3.Row lets us access columns by name
    (e.g. row["week"]) instead of by index (row[0]).
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the workouts table if it doesn't already exist.
    This runs once when the server starts.
    """
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS workouts (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            week          INTEGER NOT NULL,
            day           INTEGER NOT NULL,
            exercise_name TEXT    NOT NULL,
            set_number    INTEGER NOT NULL,
            weight        REAL,
            reps          INTEGER,
            notes         TEXT,
            created_at    TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


# Run the setup immediately when the server starts
init_db()


# ──────────────────────────────────────────────────────────────────
#  DATA MODELS  (Pydantic)
#  These classes describe the shape of the JSON the API accepts.
#  FastAPI uses them to validate incoming requests automatically.
#
#  The POST /workouts body should look like:
#
#  {
#    "week": 1,
#    "day": 2,
#    "exercises": [
#      {
#        "exercise_name": "Lat Pulldown",
#        "notes": "felt strong",
#        "sets": [
#          { "set_number": 1, "weight": 50.0, "reps": 10 },
#          { "set_number": 2, "weight": 55.0, "reps": 8  }
#        ]
#      }
#    ]
#  }
# ──────────────────────────────────────────────────────────────────

class SetData(BaseModel):
    set_number: int
    weight:     Optional[float] = None   # None means the field is optional
    reps:       Optional[int]   = None


class ExerciseData(BaseModel):
    exercise_name: str
    sets:          List[SetData]
    notes:         Optional[str] = ""    # defaults to empty string if omitted


class WorkoutPayload(BaseModel):
    week:      int
    day:       int
    exercises: List[ExerciseData]


# ──────────────────────────────────────────────────────────────────
#  ENDPOINTS
# ──────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    """Health check — confirms the server is running."""
    return {"message": "FitTrack backend is running! 🏋️"}


# ── POST /workouts ─────────────────────────────────────────────────
@app.post("/workouts", status_code=201)
def save_workout(payload: WorkoutPayload):
    """Save (or overwrite) workout data for a given week and day.

    Strategy: delete any existing rows for that week+day first,
    then insert all the new rows. This is simpler than checking
    which rows changed.
    """
    conn = get_db()
    try:
        # Step 1 — wipe old data for this week/day
        conn.execute(
            "DELETE FROM workouts WHERE week = ? AND day = ?",
            (payload.week, payload.day)
        )

        # Step 2 — insert each set for each exercise
        for exercise in payload.exercises:
            for s in exercise.sets:
                conn.execute(
                    """INSERT INTO workouts
                           (week, day, exercise_name, set_number, weight, reps, notes)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        payload.week,
                        payload.day,
                        exercise.exercise_name,
                        s.set_number,
                        s.weight,
                        s.reps,
                        exercise.notes,
                    )
                )

        conn.commit()
        return {
            "message": f"Saved workout for Week {payload.week}, Day {payload.day}",
            "week": payload.week,
            "day": payload.day,
        }

    except Exception as e:
        conn.rollback()   # undo any partial changes if something went wrong
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()      # always close the connection, even if an error occurred


# ── GET /workouts ──────────────────────────────────────────────────
@app.get("/workouts")
def get_all_workouts():
    """Return every row in the database, ordered by week → day → exercise."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM workouts ORDER BY week, day, exercise_name, set_number"
    ).fetchall()
    conn.close()

    return {"workouts": [dict(row) for row in rows]}


# ── GET /workouts/{week}/{day} ─────────────────────────────────────
@app.get("/workouts/{week}/{day}")
def get_workout(week: int, day: int):
    """Return workouts for a specific week and day.

    The response is grouped by exercise, matching the structure the
    frontend already uses in localStorage, so it's easy to plug in:

    {
      "week": 1,
      "day": 2,
      "exercises": {
        "Lat Pulldown": {
          "notes": "felt strong",
          "sets": [
            { "set_number": 1, "weight": 50.0, "reps": 10 }
          ]
        }
      }
    }
    """
    conn = get_db()
    rows = conn.execute(
        """SELECT * FROM workouts
           WHERE week = ? AND day = ?
           ORDER BY exercise_name, set_number""",
        (week, day)
    ).fetchall()
    conn.close()

    # Return an empty structure if nothing is saved yet
    if not rows:
        return {"week": week, "day": day, "exercises": {}}

    # Group flat database rows into nested exercise → sets structure
    exercises = {}
    for row in rows:
        name = row["exercise_name"]
        if name not in exercises:
            exercises[name] = {"notes": row["notes"] or "", "sets": []}
        exercises[name]["sets"].append({
            "set_number": row["set_number"],
            "weight":     row["weight"],
            "reps":       row["reps"],
        })

    return {"week": week, "day": day, "exercises": exercises}


# ── DELETE /workouts/{week}/{day} ──────────────────────────────────
@app.delete("/workouts/{week}/{day}")
def delete_workout(week: int, day: int):
    """Delete all workout data for a specific week and day."""
    conn = get_db()
    result = conn.execute(
        "DELETE FROM workouts WHERE week = ? AND day = ?",
        (week, day)
    )
    conn.commit()
    deleted = result.rowcount   # how many rows were actually removed
    conn.close()

    if deleted == 0:
        return {"message": f"No data found for Week {week}, Day {day}"}

    return {"message": f"Deleted {deleted} sets for Week {week}, Day {day}"}


# ══════════════════════════════════════════════════════════════════
#  EXAMPLE: HOW TO CONNECT YOUR FRONTEND (JavaScript / fetch)
#
#  Copy-paste these functions into your index.html <script> block.
#  Replace the localStorage calls with these to use the real backend.
# ══════════════════════════════════════════════════════════════════

"""
// The base URL of your running backend
const API = "http://127.0.0.1:8000";


// ── SAVE a workout to the backend ─────────────────────────────────
// Call this instead of (or alongside) localStorage.setItem().
//
// "data" should be the same object you store in localStorage:
// {
//   "Lat Pulldown": { sets: [{weight:"50", reps:"10"}], notes:"" },
//   ...
// }

async function saveToBackend(week, day, data) {
  // Convert the frontend's localStorage format into the API format
  const exercises = Object.entries(data).map(([exercise_name, value]) => ({
    exercise_name,
    notes: value.notes || "",
    sets: value.sets.map((s, i) => ({
      set_number: i + 1,
      weight: parseFloat(s.weight) || null,
      reps:   parseInt(s.reps)    || null,
    }))
  }));

  try {
    const response = await fetch(`${API}/workouts`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ week, day, exercises }),
    });

    if (!response.ok) throw new Error(`Server error: ${response.status}`);

    const result = await response.json();
    console.log("Saved to backend:", result.message);

  } catch (err) {
    console.error("Could not save to backend:", err);
  }
}


// ── LOAD a workout from the backend ───────────────────────────────
// Call this when the user selects a week/day to load their data.

async function loadFromBackend(week, day) {
  try {
    const response = await fetch(`${API}/workouts/${week}/${day}`);

    if (!response.ok) throw new Error(`Server error: ${response.status}`);

    const result = await response.json();

    // result.exercises is already in the same shape as localStorage data
    // so you can pass it straight to renderExercises() after setting it.
    return result.exercises;  // {} if nothing saved yet

  } catch (err) {
    console.error("Could not load from backend:", err);
    return {};
  }
}


// ── DELETE a workout from the backend ─────────────────────────────
// Call this from your "Clear Workout" button.

async function deleteFromBackend(week, day) {
  try {
    const response = await fetch(`${API}/workouts/${week}/${day}`, {
      method: "DELETE",
    });

    if (!response.ok) throw new Error(`Server error: ${response.status}`);

    const result = await response.json();
    console.log(result.message);

  } catch (err) {
    console.error("Could not delete from backend:", err);
  }
}


// ── USAGE EXAMPLES ────────────────────────────────────────────────

// Save current workout:
//   saveToBackend(currentWeek, currentDay, currentData);

// Load on week/day change:
//   const data = await loadFromBackend(currentWeek, currentDay);
//   renderExercises(data);   // pass loaded data into your render function

// Clear workout:
//   await deleteFromBackend(currentWeek, currentDay);
"""
