from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Dummy frontend-only data (no backend yet)
users = {}
habits_data = {}
moods_data = {}

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if email in users:
            flash("Email already registered!", "error")
        else:
            users[email] = {'username': username, 'password': password}
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users.get(email)
        if user and user['password'] == password:
            session['email'] = email
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials!", "error")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

@app.route('/habits', methods=['GET', 'POST'])
def habits():
    if 'email' not in session:
        return redirect(url_for('login'))
    user_email = session['email']
    if request.method == 'POST':
        habit_name = request.form['habit_name']
        habits_data.setdefault(user_email, []).append({'name': habit_name, 'completed': False})
    user_habits = habits_data.get(user_email, [])
    return render_template('habits.html', habits=user_habits)

@app.route('/mood', methods=['GET', 'POST'])
def mood():
    if 'email' not in session:
        return redirect(url_for('login'))
    user_email = session['email']
    if request.method == 'POST':
        mood_value = request.form['mood']
        moods_data.setdefault(user_email, []).append({'mood': mood_value, 'date': 'Today'})
    user_moods = moods_data.get(user_email, [])
    return render_template('mood.html', moods=user_moods)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
