# Vectorization SaaS

A Django-based SaaS application for vectorizing images using the Vectorizer.ai API.

## Features

- Auth0 Authentication
- Stripe Payment Integration
- Credit Pack System
- Vectorizer.ai API Integration
- Modern UI with Red/Black/White Theme

## Setup Instructions

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create .env file:
```bash
cp .env.example .env
```

4. Update .env with your credentials:
- AUTH0_DOMAIN
- AUTH0_CLIENT_ID
- AUTH0_CLIENT_SECRET
- STRIPE_PUBLIC_KEY
- STRIPE_SECRET_KEY
- VECTORIZER_API_ID
- VECTORIZER_API_SECRET

5. Run migrations:
```bash
python manage.py migrate
```

6. Start development server:
```bash
python manage.py runserver
```

## Project Structure

```
vectorizer_saas/
├── core/                 # Main application
│   ├── templates/       # HTML templates
│   ├── static/         # CSS, JS, images
│   ├── models.py       # Database models
│   └── views.py        # View logic
├── manage.py
├── requirements.txt
└── .env
```

## Development

- Python 3.8+
- Django 5.0+
- Modern browser with JavaScript enabled 