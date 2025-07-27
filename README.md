# 🚗 Vehicle Parking System

A comprehensive multi-user Flask web application for managing vehicle parking facilities. This system allows **admins** to manage parking lots and **users** to reserve, park, and vacate 4-wheeler parking spots with real-time tracking and analytics.

## 📚 Project Description

**Vehicle Parking System** is a robust parking management solution built with Flask that simulates a real-world 4-wheeler parking scenario with multiple lots and limited spots. The system features:

- Role-based access control (Admin/User)
- Real-time parking spot management
- Vehicle registration and tracking
- Detailed booking history and analytics
- Secure authentication and session management

## 🛠️ Tech Stack & Frameworks

| Layer | Technology | Description |
|-------|------------|-------------|
| **Backend** | Flask | Python-based micro web framework handling routing, authentication, and server logic |
| **Database** | SQLite & SQLAlchemy ORM | Lightweight database with object-relational mapping for data persistence |
| **Frontend** | Bootstrap, HTML, CSS, JavaScript | Responsive UI with dynamic components for optimal user experience |
| **Security** | Flask-Login, CSRF Protection | Secure authentication and protection against cross-site request forgery |
| **Forms** | Flask-WTF | Form validation and processing with CSRF protection |
| **API** | RESTful endpoints | JSON-based API for data access and manipulation |

## ✅ Key Features

### 👤 Admin Portal
- **Dashboard**: Real-time analytics showing occupancy rates, revenue, and recent bookings
- **Parking Management**: Create, edit, and delete parking lots with customizable spot types (standard, disabled, electric)
- **Spot Management**: Automatically generate parking spots with customizable layouts (rows and columns)
- **User Management**: View and manage all system users
- **Analytics**: Visualize parking data with interactive charts and statistics
- **Manual Operations**: Ability to manually mark spots as occupied/available

### 👥 User Portal
- **Dashboard**: View active bookings, parking fee, and booking history
- **Vehicle Management**: Register multiple vehicles with details (model, license plate, type)
- **Booking System**: Select a parking lot and get automatically assigned to an available spot
- **Check-out System**: Release parking spots and view total parking duration and cost
- **Parking History**: Complete history of all parking transactions with timestamps and costs

## 🚀 Installation and Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git (optional, for cloning the repository)

### Step-by-Step Installation

```bash
# 1. Clone the repository
git clone https://github.com/Sagar-03/vehicle_parking_system.git
cd vehicle_parking_system

# For Windows:
venv\Scripts\activate
# For macOS/Linux:
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize the database
python recreate_db.py

# 4. Run the application
python app.py

# App will be available at:
http://127.0.0.1:5000/
```



## 📊 System Architecture

The application follows the MVC (Model-View-Controller) architecture:
- **Models**: SQLAlchemy models for User, Admin, ParkingLot, ParkingSpot, Vehicle, and Booking
- **Views**: Jinja2 templates with Bootstrap for responsive UI
- **Controllers**: Flask route blueprints (admin_routes.py, user_routes.py)

## 🔒 Security Features

- Password hashing for secure credential storage
- CSRF protection for all forms
- Session management with automatic timeout
- Role-based access control with custom decorators

## 📱 API Endpoints

The system includes several RESTful API endpoints:
- `/api/parking_data` - Get detailed booking information
- `/api/parking_stats` - Get parking statistics for specific periods
- `/api/parking_lots` - Get information about all parking lots

## 📝 Project Structure

```
vehicle_parking_system/
├── app.py                 # Application factory
├── config.py              # Configuration settings
├── extensions.py          # Flask extensions
├── models/                # Database models
├── routes/                # Application routes
│   ├── admin_routes.py    # Admin-specific routes
│   └── user_routes.py     # User-specific routes
├── static/                # CSS, JavaScript, and images
├── templates/             # Jinja2 HTML templates
└── instance/              # Instance-specific data (database)
```

## 🧪 Testing

Run tests using pytest:

```bash
pytest
```

## 📈 Future Enhancements

- Mobile application integration
- Payment gateway integration
- QR code-based check-in/check-out
- Automated license plate recognition
- Reservation system for advance booking

---

Developed as part of the Modern Application Development course project.
