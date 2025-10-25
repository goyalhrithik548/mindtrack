from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson import ObjectId
from huggingface_hub import InferenceClient
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ------------------ MongoDB Setup ------------------
client = MongoClient("mongodb+srv://anantkhandelwal3_db_user:ORkE0ClXSeG2XYtl@cluster0.e5jjufr.mongodb.net/?appName=Cluster0")
db = client.mindtrack
users_col = db.users
habits_col = db.habits
moods_col = db.moods
goals_col = db.goals

# ------------------ Hugging Face Setup ------------------
os.environ["HF_TOKEN"] = "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"
HF_MODEL = "meta-llama/Llama-3.1-8B-Instruct"
hf_client = InferenceClient()

def call_hf_model(prompt):
    try:
        response = hf_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model=HF_MODEL,
            max_tokens=120,
            temperature=0.8,
        )
        if response.choices:
            return response.choices[0].message.content.strip()
        else:
            return "Keep going! You're doing great!"
    except Exception:
        return "Keep going! You're doing great!"

def get_personalized_quote(user_email):
    user = users_col.find_one({"email": user_email})
    if not user:
        return "Welcome to MindTrack! Let's start building positive habits!"
    
    username = user.get("username", "friend")

    latest_habits_cursor = habits_col.find({"user_email": user_email}).sort("created_at", -1).limit(5)
    latest_habits = list(latest_habits_cursor)
    habit_names = [h['habit_name'] for h in latest_habits]
    habits_string = ", ".join(habit_names) if habit_names else "no current habits"

    today_str = datetime.now().strftime("%Y-%m-%d")
    mood_doc = moods_col.find_one({"user_email": user_email, "date": today_str})
    mood_type = mood_doc.get("mood", "neutral") if mood_doc else "neutral"

    prompt = (
        f"You are a motivational coach. Generate a short 1–3 line personalized quote for {username}. "
        f"They are currently focusing on habits such as {habits_string}. "
        f"Their current mood is {mood_type}. Make it inspiring, positive, and natural."
    )

    return call_hf_model(prompt)

def get_motivation(user_email):
    return get_personalized_quote(user_email)

# ------------------ Static Data ------------------
POPULAR_HABITS = [
    "Drink Water", "Meditate", "Read Book",
    "Walk 5000 steps", "Journal", "Sleep Early"
]

# ------------------ Helper Functions ------------------
def suggest_habits(user_email):
    user_habits = [h['habit_name'] for h in habits_col.find({"user_email": user_email})]
    suggestions = [h for h in POPULAR_HABITS if h not in user_habits]
    return suggestions[:3]

def weekly_streak(habit):
    today = datetime.now().date()
    streak = 0
    for i in range(7):
        day = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        if day in habit.get("completed_dates", []):
            streak += 1
    return streak

# ------------------ Routes ------------------
@app.route('/')
def home():
    return redirect(url_for('login'))

# ---------- Registration ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if users_col.find_one({"email": email}):
            flash("Email already registered", "error")
        else:
            users_col.insert_one({
                "username": username,
                "email": email,
                "password": password,
                "friends": []
            })
            flash("Registered successfully!", "success")
            return redirect(url_for('login'))
    return render_template('register.html')

# ---------- Login ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users_col.find_one({"email": email, "password": password})

        if user:
            session['email'] = email
            session['username'] = user['username']
            return redirect(url_for('mood_input'))  # <-- reroute to mood input first
        else:
            flash("Invalid credentials", "error")
    return render_template('login.html')

# ---------- Mood Input ----------
@app.route('/mood', methods=['GET', 'POST'])
def mood_input():
    if 'email' not in session:
        return redirect(url_for('login'))

    moods_options = [
        {"emoji":"😄","text":"Happy"},
        {"emoji":"😢","text":"Sad"},
        {"emoji":"😡","text":"Angry"},
        {"emoji":"😌","text":"Relaxed"},
        {"emoji":"😴","text":"Sleepy"},
        {"emoji":"🤯","text":"Stressed"},
        {"emoji":"😐","text":"Neutral"}
    ]

    if request.method == 'POST':
        mood = request.form['mood']
        allowed_emojis = [m['emoji'] for m in moods_options]
        if mood not in allowed_emojis:
            flash("Invalid mood selected!", "error")
            return redirect(url_for('mood_input'))

        moods_col.insert_one({
            "user_email": session['email'],
            "mood": mood,
            "date": datetime.now().strftime("%Y-%m-%d")
        })
        return redirect(url_for('dashboard'))

    return render_template('mood_input.html', moods_options=moods_options)

# ---------- Dashboard ----------
@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    email = session['email']
    username = session['username']

    latest_mood_doc = moods_col.find_one({"user_email": email}, sort=[("date", -1)])
    today_mood = latest_mood_doc['mood'] if latest_mood_doc else "😐"

    habits = list(habits_col.find({"user_email": email}))
    goals = list(goals_col.find({"user_email": email}))

    streaks = {h['habit_name']: weekly_streak(h) for h in habits}
    motivation = get_motivation(email)
    suggestions = suggest_habits(email)

    events = []
    for m in moods_col.find({"user_email": email}):
        events.append({
            "title": f"Mood: {m.get('mood', '😐')}",
            "start": m.get("date"),
            "color": "#4caf50" if m.get("mood") == "😄" else "#f39c12"
        })
    for h in habits:
        for d in h.get("completed_dates", []):
            events.append({
                "title": f"Habit: {h['habit_name']}",
                "start": d,
                "color": "#3498db"
            })
    for g in goals:
        if g.get("completed"):
            events.append({
                "title": f"Goal Completed: {g['goal']}",
                "start": datetime.now().strftime("%Y-%m-%d"),
                "color": "#9c27b0"
            })

    return render_template(
        'dashboard.html',
        username=username,
        mood=today_mood,
        habits=habits,
        goals=goals,
        streaks=streaks,
        motivation=motivation,
        suggestions=suggestions,
        events=events
    )

# ---------- Habits ----------
@app.route('/habits', methods=['GET', 'POST'])
def habits():
    if 'email' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        habit_name = request.form['habit_name']
        duration = int(request.form.get('duration', 1))
        habits_col.insert_one({
            "user_email": session['email'],
            "habit_name": habit_name,
            "duration": duration,
            "created_at": datetime.now(),
            "completed_dates": [],
            "completed": False
        })
    user_habits = list(habits_col.find({"user_email": session['email']}))
    return render_template('habits.html', habits=user_habits)

@app.route('/complete_habit/<habit_id>')
def complete_habit(habit_id):
    if 'email' not in session:
        return redirect(url_for('login'))

    habits_col.update_one(
        {"_id": ObjectId(habit_id), "user_email": session['email']},
        {"$set": {"completed": True}}
    )
    flash("Habit marked as completed!", "success")
    return redirect(url_for('habits'))

@app.route('/remove_habit/<habit_id>')
def remove_habit(habit_id):
    if 'email' not in session:
        return redirect(url_for('login'))

    habits_col.delete_one(
        {"_id": ObjectId(habit_id), "user_email": session['email']}
    )
    flash("Habit removed successfully!", "info")
    return redirect(url_for('habits'))

# ---------- Goals ----------
@app.route('/goals', methods=['GET', 'POST'])
def goals():
    if 'email' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        goal = request.form['goal']
        duration = int(request.form.get('duration', 1))
        goals_col.insert_one({
            "user_email": session['email'],
            "goal": goal,
            "duration": duration,
            "completed": False
        })

    user_goals = list(goals_col.find({"user_email": session['email']}))
    return render_template('goals.html', goals=user_goals)

@app.route('/complete_goal/<goal_id>')
def complete_goal(goal_id):
    if 'email' not in session:
        return redirect(url_for('login'))

    goals_col.update_one(
        {"_id": ObjectId(goal_id), "user_email": session['email']},
        {"$set": {"completed": True}}
    )
    flash("Goal marked as completed!", "success")
    return redirect(url_for('goals'))

@app.route('/remove_goal/<goal_id>')
def remove_goal(goal_id):
    if 'email' not in session:
        return redirect(url_for('login'))

    goals_col.delete_one(
        {"_id": ObjectId(goal_id), "user_email": session['email']}
    )
    flash("Goal removed successfully!", "info")
    return redirect(url_for('goals'))

# ---------- Logout ----------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------- Run App ----------
if __name__ == "__main__":
    app.run(debug=True)
