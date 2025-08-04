# Library Service Project
A library service project where you can borrow books and send notifications to the Telegram chat about each borrowing.

# Installation

- git clone https://github.com/mtiunov/library-service-project.git
- cd library-service-project_api
- python -m venv venv
- venv\Scripts\activate for MacOS/Linux: source venv/bin/activate
- pip install -r requirements.txt
- python manage.py migrate 
- python manage.py runserver

# Features

- JWT Authentication
- Admin panel (/admin/)
- Managing Books
- Creating Borrowings
- Filtering Borrowings using different parameters
- Cover all custom logic with tests

# Database Structure

You can also register a new user. After receiving the authentication token, 
all endpoints provided by the API will be available to you.