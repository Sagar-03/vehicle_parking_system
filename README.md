# 🚗 Vehicle Parking App - V1

A multi-user Flask web application that allows **admins** to manage vehicle parking lots and **users** to reserve, park, and vacate 4-wheeler parking spots. This app supports role-based access (admin/user), provides parking analytics, and stores all data using SQLite with proper backend validations.

---

## 📚 Project Description

**Vehicle Parking App V1** is built as part of the *Modern Application Development I* curriculum. It simulates a real-world 4-wheeler parking management system with multiple lots and limited spots, managed by an admin and used by multiple authenticated users.

---

## 🛠️ Tech Stack & Frameworks Used

| Layer        | Technology         | Description                                                                 |
|--------------|--------------------|-----------------------------------------------------------------------------|
| **Backend**  | Flask              | Micro web framework to manage routing, forms, sessions, and server logic.  |
| **Templating**| Jinja2             | Enables dynamic HTML rendering with logic on the front-end.                |
| **Database** | SQLite (via SQLAlchemy or raw SQL) | Lightweight RDBMS; DB is created programmatically.               |
| **Frontend** | HTML, CSS, Bootstrap | For page layout, styling, responsiveness, and forms.                      |



---

## ✅ Core Functionalities

### 👤 Admin
- Pre-existing root admin (no registration).
- Create, edit, and delete parking lots.
- Automatically generate `N` parking spots in a lot.
- View all users, current parking status, and bookings.
- Dashboard analytics (e.g., occupancy per lot).

### 👥 User
- Register and login.
- Select a lot and auto-assign first available parking spot.
- Park a vehicle (mark as occupied) and vacate spot.
- See parking history and stats with timestamps.
- Cannot choose spot manually — assigned automatically.

---
---

## 🚀 How to Run the Project Locally

### ✅ Prerequisites

- Python 3.x installed
- `pip` (Python package manager)

---

### 📥 Step-by-Step Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/vehicle-parking-app.git
cd vehicle-parking-app

# 2. Create a virtual environment
python -m venv venv

# Activate it:
# For Windows:
venv\Scripts\activate

# For macOS/Linux:
source venv/bin/activate

# 3. Install all required dependencies
pip install -r requirements.txt

# 4. Run the application
python run.py

# App will be available at:
http://127.0.0.1:5000/


