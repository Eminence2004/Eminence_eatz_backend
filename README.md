# Eminence Eatz Backend

Backend API for the **Eminence Eatz food ordering platform**, built with Django and Django REST Framework.

## Repository

https://github.com/Eminence2004/Eminence_eatz_backend.git

## Tech Stack

* Django
* Django REST Framework
* SQLite (`db.sqlite3`)
* Firebase (notifications)

## Project Setup

### 1. Clone the Repository

```
git clone https://github.com/Eminence2004/Eminence_eatz_backend.git
cd Eminence_eatz_backend
```

### 2. Create Virtual Environment

```
python -m venv venv
```

Activate the environment:

**Windows**

```
venv\Scripts\activate
```

**Mac/Linux**

```
source venv/bin/activate
```

### 3. Install Dependencies

```
pip install -r requirements.txt
```

### 4. Run Database Migrations

```
python manage.py migrate
```

### 5. Start the Development Server

```
python manage.py runserver
```

The API will run at:

```
http://127.0.0.1:8000/
```

## Database

The project currently uses **SQLite** with the file:

```
db.sqlite3
```

For production deployment, PostgreSQL is recommended.

## Features

* Food ordering backend API
* Order management
* RESTful endpoints
* Firebase integration for notifications

## Author

**Daniel Kyeremateng Amartey**

GitHub: https://github.com/Eminence2004
