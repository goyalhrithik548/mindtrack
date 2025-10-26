# 🧠 MindTrack – AI-Powered Mood Tracking App

## 🔹 Introduction

**MindTrack** is an AI-integrated mood tracking platform built using **Flask** and **MongoDB** to help users monitor and analyze their emotional well-being.
Users can securely log in, record their daily moods, write personal notes, and visualize emotional patterns through an interactive dashboard.

This project focuses on creating a user-friendly, privacy-first interface that encourages emotional self-awareness and personal growth.

---

## 🧩 Problem Statement

In today’s fast-paced world, people experience emotional ups and downs but rarely take time to reflect or track how they feel.
Without such self-awareness, it becomes difficult to identify triggers, manage stress, or maintain mental balance.

**MindTrack** addresses this by:

* Allowing users to **log and daily moods** easily.
* Providing **visual insights** through charts and dashboards.
* Displaying **motivational quotes** using the Hugging Face API every time a user logs in, tailored to their mood.
* Ensuring all data is **securely stored** using encrypted databases and GitHub Secrets.

---

## 🛠️ Tools Used and How Each Was Used

| Tool                                                 | Purpose / Usage                                                                                               |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **Python (Flask)**                                   | Acts as the backend server handling authentication, routing, and communication between frontend and database. |
| **MongoDB**                                          | Stores user data such as login details, mood levels, and personal notes in a NoSQL format.                    |
| **HTML / CSS / JavaScript**                          | Used to design and enhance the web interface for mood input and dashboard visualization.                      |
| **GitHub**                                           | For version control, code collaboration, and project management.                                              |
| **Browser**                                          | Used to test APIs and validate backend routes during development.                                             |
| **Render / Localhost**                               | For hosting and running the Flask backend online or locally.                                                  |

---

## 📁 Folder Structure

```
mindtrack/
│
├── Backend/
│   └── Flask Backend.py               # Optional separate backend logic file
│
├── frontend/
│   ├── static/
│   │   └── style.css                  # Contains all CSS styles for frontend
│   │
│   ├── templates/
│   │   ├── login.html                 # Login page
│   │   ├── register.html              # User registration page
│   │   ├── dashboard.html             # Main dashboard showing mood data
│   │   ├── mood.html                  # Mood tracking form
│   │   ├── mood_input.html            # Input interface for daily notes
│   │   ├── calender.html              # Calendar view for mood logs
│   │   ├── habits.html                # Habit tracking module
│   │   ├── goals.html                 # Goal setting and progress tracker
│   │
│   ├── app.py                         # Flask app entry point (backend + routing)
│   ├── requirements.txt               # Required libraries and dependencies
│
├── .gitignore                         # Ignored files/folders (like venv, __pycache__)
└── README.md                          # Project documentation
```

---

## 🚀 Project Workflow

1. **User Registration & Login**

   * Users register using an email and password.
   * Credentials are stored securely in MongoDB.
   * Flask manages sessions for authenticated users.

2. **Mood Entry and Update**

   * User selects their current mood based on emojis.
   * Users can update their mood multiple times everytime they login.
   * Data is saved in MongoDB with the date and mood score.

3. **Goals & Habit Tracking**

   * Users can set personal goals and mark progress.
   * Users can track habits daily and update them after logging in.
   * All entries are linked to the user in MongoDB.
  
4. **Motivational Quote**

   * Hugging Face API fetches a motivational quote every time the user logs in.
   * Quotes are optionally tailored based on the user’s current mood to boost positivity.

5. **Data Storage**

   * Each mood entry is linked to the user’s email in the database.
   * Example document:

     ```json
     {
       "user_email": "example@gmail.com",
       "date": "2025-10-26",
       "mood_level": "Happy",
     }
     ```

6. **Dashboard Visualization**

   * Flask retrieves user mood data from MongoDB.
   * Frontend displays graphs/charts to show trends (weekly, monthly).
  
7. **Result**

   * Deployed Link - https://hack-x026.onrender.com/dashboard
   * Demo Video - 


8. **Future Enhancements**

   * Personalized recommendations or affirmations based on mood history.
   * Allow sharing progress with friends for social motivation. 
   * Add lightweight AI (optional API) to suggest “new habits to try” based on user history.
   * Mobile app version using Flutter or React Native.

---

## 👨‍💻 Team Name - "404 Not Founders"

* **Hrithik Goyal** – Backend & Database Integration
* **Nikhil Mahesh** – Frontend Design & GitHub Management
* **Anant Khandelwal** – API Testing & Dashboard Visualization
