# FoodMitra
# 🍲 FoodMitra

FoodMitra is a web platform that connects **home cooks** with **customers** looking for fresh, home-made food. Cooks can list their dishes, and customers can browse nearby cooks, place orders, pay, and leave reviews.

## ✨ Features

**For Customers**
- Register and log in, with password reset
- Browse the menu with veg / non-veg dishes
- Find cooks near you (location-based)
- Place orders and pre-orders for a chosen date
- Pay online or choose Cash on Delivery
- Track order status
- Download order receipt (PDF)
- Rate and review cooks

**For Cooks**
- Create a cook profile with photo and kitchen type
- Post, edit and delete menu items
- Mark availability on or off
- Accept and manage incoming orders
- View earnings
- Cooks are verified by the admin before posting menus

**For Admin**
- Admin dashboard to manage users, cooks, orders and reviews

## 🛠️ Tech Stack

- **Backend:** Python, Django
- **Frontend:** HTML, CSS, JavaScript (Django templates)
- **Database:** SQLite
- **Other:** Razorpay, geocoding for locations, PDF generation

## 📁 Project Structure

```
FoodMitra/
├── accounts/    # Users, cook and customer profiles, dashboards
├── menu/        # Menu items and pre-orders
├── orders/      # Orders, payments, PDF receipts
├── reviews/     # Ratings and reviews
├── foodmitra/   # Project settings and URLs
├── templates/   # HTML pages
├── media/       # Uploaded images
└── manage.py
```

## 🚀 How to Run Locally

1. Clone the repository
```
   git clone https://github.com/Jyothi-Chikkannegowda/FoodMitra.git
   cd FoodMitra
```
2. Create and activate a virtual environment
```
   python -m venv venv
   venv\Scripts\activate
```
3. Install dependencies
```
   pip install -r requirements.txt
```
4. Set up the database
```
   python manage.py migrate
```
5. Create an admin account
```
   python manage.py createsuperuser
```
6. Start the server
```
   python manage.py runserver
```
7. Open http://127.0.0.1:8000 in your browser

## 👩‍💻 Author

**Jyothi Chikkannegowda**
GitHub: [@Jyothi-Chikkannegowda](https://github.com/Jyothi-Chikkannegowda)