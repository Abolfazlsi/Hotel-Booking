# 🏨 Hotel Booking

A full-stack hotel booking web application built with **Django**.

The project provides a complete hotel reservation flow, including room discovery, availability checking, guest information, online payment, booking management, reviews, and a customized admin panel.

It is also configured with a production-oriented stack using **Docker, PostgreSQL, Redis, Gunicorn, and Nginx**.

---

## ✨ Features

- 🔐 Phone number authentication with OTP
- 👤 Custom User model and user profiles
- 🏨 Hotel room listing and detailed room pages
- 🔎 Room search and filtering
- 📅 Jalali (Persian) date support
- 🚫 Room availability and booking conflict validation
- 👥 Guest information management
- 💰 Automatic reservation price calculation
- 💳 ZarinPal online payment integration
- 🧾 Booking and transaction management
- ⭐ Room ratings and reviews
- 📩 Contact form
- 🛠️ Customized Django Admin
- ⚡ Redis for OTP, caching and sessions
- 🐘 PostgreSQL support
- 🐳 Docker & Docker Compose
- 🌐 Nginx + Gunicorn production setup
- 🧪 Automated tests

---

## 🛠️ Tech Stack

**Backend**
- Python
- Django 5.2

**Database & Infrastructure**
- PostgreSQL
- SQLite (development)
- Redis
- Docker / Docker Compose
- Nginx
- Gunicorn

**Other**
- ZarinPal Payment Gateway
- Jalali Date

---

## 📸 Main Flow

```text
Browse Rooms
     ↓
Search & Filter
     ↓
Select Dates
     ↓
Check Availability
     ↓
Enter Guest Information
     ↓
Calculate Price
     ↓
ZarinPal Payment
     ↓
Payment Verification
     ↓
Booking Confirmation
```

---

## 🚀 Getting Started

### Requirements

- Python 3.12+
- Git
- Docker & Docker Compose

---

### 🐳 Run with Docker

Clone the repository:

```bash
https://github.com/Abolfazlsi/Hotel-Booking.git
cd Hotel-Booking
```

Create a `.env` file in the project root:

```env
DJANGO_ENV=production
SECRET_KEY=your-secret-key
REDIS_URL=redis://redis:6379/0
```

Build and start the project:

```bash
docker compose up --build
```

Then open:

```text
http://localhost
```

---

### 💻 Run Locally

Create and activate a virtual environment:

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS**

```bash
python3 -m venv venv
source venv/bin/activate
```

Create a `.env` file in the project root:

```env
DJANGO_ENV=development
SECRET_KEY=your-secret-key
REDIS_URL=redis://redis:6379/0
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python manage.py migrate
```

Create an admin user:

```bash
python manage.py createsuperuser
```

Start the development server:

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000
```

> Redis is required for the OTP/cache/session functionality. It can be started locally or through Docker.

---

## 🔑 Admin Panel

After creating a superuser, access:

```text
http://127.0.0.1:8000/admin/
```

The admin panel allows management of:

- Users
- Rooms
- Room Images
- Services
- Reviews
- Bookings
- Guests
- Transactions
- Contact Messages

---

## 🧠 Backend Highlights

This project goes beyond basic CRUD and includes real-world backend concepts such as:

- Custom authentication with OTP
- Reservation conflict detection
- Database transactions with `transaction.atomic()`
- Row-level locking with `select_for_update()`
- Redis-based temporary OTP storage
- Redis-backed sessions and caching
- Server-side payment verification
- Server-side reservation price calculation
- Dockerized production environment

---

## 📁 Project Structure

```text
├── accounts/        # Authentication & users
├── hotels/          # Rooms, services & reviews
├── reservations/    # Bookings, guests & payments
├── pages/           # Contact and other pages
├── core/            # Project configuration
├── templates/       # Django templates
├── static/          # Static assets
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
├── requirements.txt
└── manage.py
```

---

## ⚠️ Development Note

The OTP flow is fully implemented, but the current project uses a development OTP sender that prints the generated code instead of sending it through a real SMS provider.

For production, it can be connected to an SMS service.

---

## 👨‍💻 Author

**Abolfazl**

GitHub:  
https://github.com/Abolfazlsi

---

⭐ If you find this project useful, feel free to explore the source code.
