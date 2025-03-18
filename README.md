# Vectorizer SaaS Platform

A modern Django-based SaaS application that provides AI-powered image vectorization services using the Vectorizer.ai API. The platform features a sleek, modern interface with a sophisticated red/black/white color scheme and robust user authentication.

## Current Features

### Authentication & User Management
- **Auth0 Integration**
  - Secure user authentication
  - Google OAuth login support
  - User profile management
  - Session handling
  - Protected routes and endpoints

### Core Functionality
- **Image Vectorization**
  - Integration with Vectorizer.ai API
  - Support for various image formats
  - Real-time processing status updates
  - Download vectorized images

### User Interface
- **Modern Design**
  - Responsive layout
  - Red/Black/White color scheme
  - User-friendly navigation
  - Interactive dashboard
  - Loading states and animations

### Payment Integration
- **Stripe Integration**
  - Secure payment processing
  - Credit pack system
  - Transaction history
  - Subscription management

## Technical Stack

### Backend
- **Django 5.0+**
  - RESTful API endpoints
  - Secure authentication
  - Database management
  - File handling

### Frontend
- **Modern Web Technologies**
  - HTML5
  - CSS3 with custom styling
  - JavaScript for interactivity
  - Responsive design

### External Services
- **Auth0**
  - User authentication
  - Social login integration
  - Session management

- **Stripe**
  - Payment processing
  - Subscription handling
  - Transaction management

- **Vectorizer.ai**
  - Image vectorization
  - API integration
  - Processing management

## Project Structure

```
vectorizer_saas/
├── core/                 # Main application
│   ├── templates/       # HTML templates
│   │   ├── base.html   # Base template
│   │   ├── home.html   # Landing page
│   │   └── dashboard/  # Dashboard templates
│   ├── static/         # Static files
│   │   ├── css/       # Stylesheets
│   │   ├── js/        # JavaScript files
│   │   └── images/    # Image assets
│   ├── models.py      # Database models
│   ├── views.py       # View logic
│   └── urls.py        # URL routing
├── vectorizer_saas/    # Project settings
│   ├── settings.py    # Django settings
│   └── urls.py        # Main URL configuration
├── manage.py          # Django management
├── requirements.txt   # Python dependencies
└── .env              # Environment variables
```

## Setup Instructions

1. **Clone the Repository**
```bash
git clone https://github.com/beoncer/tovector_python.git
cd tovector_python
```

2. **Create and Activate Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Configuration**
```bash
cp .env.example .env
```

5. **Update Environment Variables**
Required variables in `.env`:
```
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Auth0 Settings
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
AUTH0_CALLBACK_URL=http://localhost:8000/callback

# Stripe Settings
STRIPE_PUBLIC_KEY=your-stripe-public-key
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=your-webhook-secret

# Vectorizer.ai Settings
VECTORIZER_API_ID=your-api-id
VECTORIZER_API_SECRET=your-api-secret
```

6. **Database Setup**
```bash
python manage.py migrate
```

7. **Run Development Server**
```bash
python manage.py runserver
```

## Development Guidelines

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add comments for complex logic
- Keep functions focused and small

### Git Workflow
- Create feature branches
- Write descriptive commit messages
- Review code before merging
- Keep commits atomic

### Testing
- Write unit tests for new features
- Test edge cases
- Maintain test coverage
- Run tests before committing

## Security Considerations

- Environment variables for sensitive data
- Secure authentication with Auth0
- Protected API endpoints
- Secure payment processing
- Regular security updates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is proprietary and confidential. All rights reserved.

## Support

For support, please contact the development team or create an issue in the repository. 