# 🏋️ FitTrack – Fitness Tracking Web App

FitTrack is a simple full-stack fitness tracking application that helps you log workouts, track progress, and stay consistent with your training plan.

---

## 🚀 Features

* 📅 12-week workout planner
* 💪 Track exercises, sets, reps, and weights
* 📝 Add notes for each exercise
* ⚡ Auto-save (no manual save button needed)
* 💾 Local storage backup
* 🌐 Backend API with database storage

---

## 🧠 How It Works

```
Frontend (HTML/JS)
        ↓
Backend API (FastAPI)
        ↓
SQLite Database
```

* The frontend collects workout data
* The backend saves it into a database
* Data can be retrieved anytime

---

## 🛠️ Tech Stack

**Frontend**

* HTML
* CSS
* JavaScript

**Backend**

* Python
* FastAPI
* SQLite

---

## 📂 Project Structure

```
Real-FitnessPal/
│
├── frontend/
│   └── index.html
│
├── backend/
│   ├── main.py
│   └── requirements.txt
│
└── README.md
```

---

## ⚙️ Setup Instructions

### 1. Clone the repository

```
git clone https://github.com/YOUR_USERNAME/Real-FitnessPal.git
cd Real-FitnessPal
```

---

### 2. Install backend dependencies

```
cd backend
pip install -r requirements.txt
```

---

### 3. Run backend server

```
uvicorn main:app --reload
```

Backend will run on:

```
http://127.0.0.1:8000
```

---

### 4. Open frontend

Open:

```
frontend/index.html
```

Or use VS Code Live Server.

---

## 🧪 Testing the API

Go to:

```
http://127.0.0.1:8000/docs
```

You can:

* Save workouts
* View saved data
* Delete workouts

---

## 📱 Future Improvements

* 🌍 Deploy backend (Render / Railway)
* 📲 Mobile-friendly UI improvements
* 🔐 User login system
* 📊 Progress analytics and charts

---

## 🙌 Author

Built by **Shikshit Dhungana**

---

## 💡 Notes

* Backend must be running for saving to database
* Data is also stored locally as backup
* Designed for learning full-stack development

---
