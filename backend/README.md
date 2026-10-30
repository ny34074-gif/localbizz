# LocalBiz Backend

1. Import database/database.sql into MySQL.
2. Copy .env.example to .env and set your MySQL password.
3. Run:
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python app.py

API:
http://127.0.0.1:5000/api/health

The API supports registration/login, business listings and image upload,
search/filter, business details, reviews/ratings, contact messages,
business-owner data, and admin management.
