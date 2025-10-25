from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.secret_key = "supersecretkey"

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/") #change here for mongodb connection
db = client.mindtrack
users_col = db.users
habits_col = db.habits
moods_col = db.moods
goals_col = db.goals

# Motivational messages
MOTIVATIONS = [
    "Keep going! You're doing great!",
    "Consistency is key. Keep it up!",
    "Every small step counts!",
    "Today is another chance to improve!"
]

# Popular habit suggestions
POPULAR_HABITS = ["Drink Water", "Meditate", "Read Book", "Walk 5000 steps", "Journal", "Sleep Early"]

# ---------- Helper Functions ----------
def get_motivation():
    return random.choice(MOTIVATIONS)

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

# ---------- Routes ----------
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if users_col.find_one({"email": email}):
            flash("Email already registered", "error")
        else:
            users_col.insert_one({"username": username, "email": email, "password": password, "friends":[]})
            flash("Registered successfully!", "success")
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        email = request.form['email']
        password = request.form['password']
        user = users_col.find_one({"email": email, "password": password})
        if user:
            session['email'] = email
            session['username'] = user['username']
            return redirect(url_for('mood_input'))
        else:
            flash("Invalid credentials", "error")
    return render_template('login.html')

@app.route('/mood', methods=['GET','POST'])
def mood_input():
    if 'email' not in session:
        return redirect(url_for('login'))
    if request.method=='POST':
        mood = request.form['mood']
        moods_col.insert_one({
            "user_email": session['email'],
            "mood": mood,
            "date": datetime.now().strftime("%Y-%m-%d")
        })
        return redirect(url_for('dashboard'))
    return render_template('mood_input.html')

@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    email = session['email']
    username = session['username']

    today_mood = moods_col.find({"user_email": email}).sort("date",-1).limit(1)
    today_mood = today_mood[0]['mood'] if today_mood.count() > 0 else "Not set"

    habits = list(habits_col.find({"user_email": email}))
    goals = list(goals_col.find({"user_email": email}))

    streaks = {h['habit_name']: weekly_streak(h) for h in habits}
    motivation = get_motivation()
    suggestions = suggest_habits(email)

    return render_template('dashboard.html',
                           username=username,
                           mood=today_mood,
                           habits=habits,
                           goals=goals,
                           streaks=streaks,
                           motivation=motivation,
                           suggestions=suggestions)

@app.route('/habits', methods=['GET','POST'])
def habits():
    if 'email' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        habit_name = request.form['habit_name']
        habits_col.insert_one({
            "user_email": session['email'],
            "habit_name": habit_name,
            "created_at": datetime.now(),
            "completed_dates": []
        })
    user_habits = list(habits_col.find({"user_email": session['email']}))
    return render_template('habits.html', habits=user_habits)

@app.route('/goals', methods=['GET','POST'])
def goals():
    if 'email' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        goal = request.form['goal']
        goals_col.insert_one({
            "user_email": session['email'],
            "goal": goal,
            "completed": False
        })
    user_goals = list(goals_col.find({"user_email": session['email']}))
    return render_template('goals.html', goals=user_goals)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
