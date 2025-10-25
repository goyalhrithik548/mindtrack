import os
from flask import (
    Flask, render_template, request, redirect, url_for, session, jsonify, abort
)
import pymongo
import bcrypt
# from dotenv import load_dotenv  # No longer needed for testing
from datetime import datetime, timezone
from bson.objectid import ObjectId

# Load environment variables from .env file
# load_dotenv() # Disabled for testing

# Initialize Flask app
app = Flask(__name__)

# Load configurations for testing
# WARNING: Hardcoding keys is insecure and only for quick testing.
# DO NOT use this in production. Replace with your actual values.
app.config["SECRET_KEY"] = "your-very-random-secret-key-for-testing"
app.config["MONGO_URI"] = "your_mongodb_atlas_connection_string_goes_here"

# Setup MongoDB connection
try:
    client = pymongo.MongoClient(app.config["MONGO_URI"])
    # Specify the database name
    db = client.mindtrack_db 
    users_collection = db.users
    habits_collection = db.habits
    entries_collection = db.entries
    
    # Test connection
    client.server_info()
    print("MongoDB connected successfully!")
except pymongo.errors.ConnectionFailure as e:
    print(f"Could not connect to MongoDB: {e}")
    # You might want to exit or handle this more gracefully
except Exception as e:
    print(f"An error occurred during MongoDB setup: {e}")

# --- Helper Function ---

def get_current_user_id():
    """Checks session and returns user_id if logged in."""
    if "user_id" not in session:
        return None
    return ObjectId(session["user_id"])

# --- User Authentication Routes ---

@app.route("/")
def index():
    """Serves the login page. Redirects to dashboard if already logged in."""
    if get_current_user_id():
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    """Handles user login."""
    email = request.form.get("email")
    password = request.form.get("password")

    if not email or not password:
        return render_template("index.html", error="Email and password are required.")

    user = users_collection.find_one({"email": email})

    if user and bcrypt.checkpw(password.encode('utf-8'), user["password"]):
        session["user_id"] = str(user["_id"])
        session["email"] = user["email"]
        return redirect(url_for("dashboard"))
    else:
        return render_template("index.html", error="Invalid email or password.")

@app.route("/register")
def register():
    """Serves the registration page."""
    if get_current_user_id():
        return redirect(url_for("dashboard"))
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def register_post():
    """Handles user registration."""
    email = request.form.get("email")
    password = request.form.get("password")

    if not email or not password:
        return render_template("register.html", error="Email and password are required.")

    if users_collection.find_one({"email": email}):
        return render_template("register.html", error="Email already exists.")

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    try:
        users_collection.insert_one({
            "email": email,
            "password": hashed_password,
            "created_at": datetime.now(timezone.utc)
        })
        return redirect(url_for("index"))
    except Exception as e:
        print(f"Error during registration: {e}")
        return render_template("register.html", error="An error occurred. Please try again.")

@app.route("/logout")
def logout():
    """Logs the user out."""
    session.clear()
    return redirect(url_for("index"))

# --- Main Application Routes ---

@app.route("/dashboard")
def dashboard():
    """Serves the main dashboard page."""
    user_id = get_current_user_id()
    if not user_id:
        return redirect(url_for("index"))

    try:
        user_habits = list(habits_collection.find({"user_id": user_id}))
        # Convert ObjectId to string for JSON serialization in the template
        for habit in user_habits:
            habit["_id"] = str(habit["_id"])
            
        return render_template(
            "dashboard.html", 
            email=session.get("email", "User"), 
            habits=user_habits
        )
    except Exception as e:
        print(f"Error fetching dashboard data: {e}")
        return render_template("dashboard.html", email=session.get("email"), habits=[], error="Could not load habits.")

# --- API Routes (for JavaScript) ---

@app.route("/api/habits", methods=["POST"])
def add_habit():
    """API endpoint to add a new habit."""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.json
    habit_name = data.get("name")

    if not habit_name:
        return jsonify({"success": False, "error": "Habit name is required."}), 400

    try:
        result = habits_collection.insert_one({
            "user_id": user_id,
            "name": habit_name,
            "created_at": datetime.now(timezone.utc)
        })
        new_habit = {
            "_id": str(result.inserted_id),
            "name": habit_name
        }
        return jsonify({"success": True, "habit": new_habit}), 201
    except Exception as e:
        print(f"Error adding habit: {e}")
        return jsonify({"success": False, "error": "Could not add habit."}), 500

@app.route("/api/habits/<string:habit_id>", methods=["DELETE"])
def delete_habit(habit_id):
    """API endpoint to delete a habit and its entries."""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    try:
        habit_obj_id = ObjectId(habit_id)
        
        # Ensure the habit belongs to the user before deleting
        delete_result = habits_collection.delete_one({
            "_id": habit_obj_id,
            "user_id": user_id
        })
        
        if delete_result.deleted_count == 0:
            return jsonify({"success": False, "error": "Habit not found or not authorized."}), 404

        # Delete all associated entries
        entries_collection.delete_many({
            "habit_id": habit_obj_id,
            "user_id": user_id
        })
        
        return jsonify({"success": True}), 200
    except Exception as e:
        print(f"Error deleting habit: {e}")
        return jsonify({"success": False, "error": "An error occurred."}), 500

@app.route("/api/entries/toggle", methods=["POST"])
def toggle_entry():
    """API endpoint to add or remove a habit entry for a specific date."""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.json
    habit_id = data.get("habit_id")
    date = data.get("date") # Expected format: "YYYY-MM-DD"

    if not habit_id or not date:
        return jsonify({"success": False, "error": "Missing habit_id or date."}), 400

    try:
        habit_obj_id = ObjectId(habit_id)
        
        # Check if habit belongs to user (optional but good for security)
        if not habits_collection.find_one({"_id": habit_obj_id, "user_id": user_id}):
            return jsonify({"success": False, "error": "Habit not found."}), 404

        entry_query = {
            "user_id": user_id,
            "habit_id": habit_obj_id,
            "date": date
        }
        
        existing_entry = entries_collection.find_one(entry_query)
        
        if existing_entry:
            # Entry exists, so delete it (un-check)
            entries_collection.delete_one(entry_query)
            return jsonify({"success": True, "checked": False})
        else:
            # Entry doesn't exist, so create it (check)
            entries_collection.insert_one({
                **entry_query,
                "completed": True,
                "created_at": datetime.now(timezone.utc)
            })
            return jsonify({"success": True, "checked": True})

    except Exception as e:
        print(f"Error toggling entry: {e}")
        return jsonify({"success": False, "error": "An error occurred."}), 500

@app.route("/api/entries", methods=["GET"])
def get_entries():
    """API endpoint to get all entries for the logged-in user."""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    
    try:
        entries = list(entries_collection.find({"user_id": user_id}))
        
        # Prepare data for FullCalendar
        calendar_events = []
        habits = {str(h["_id"]): h["name"] for h in habits_collection.find({"user_id": user_id})}

        for entry in entries:
            habit_id_str = str(entry["habit_id"])
            calendar_events.append({
                "id": str(entry["_id"]),
                "title": habits.get(habit_id_str, "Habit"), # Get habit name
                "start": entry["date"],
                "allDay": True,
                "extendedProps": {
                    "habit_id": habit_id_str
                }
            })
        
        # Also send back raw entries for today's checklist
        today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        todays_entries_list = [
            str(e["habit_id"]) for e in entries if e["date"] == today_str
        ]

        return jsonify({
            "success": True, 
            "events": calendar_events,
            "todays_entries": todays_entries_list
        })
    except Exception as e:
        print(f"Error getting entries: {e}")
        return jsonify({"success": False, "error": "An error occurred."}), 500


# --- Main execution ---

if __name__ == "__main__":
    app.run(debug=True, port=5000)

