# Ostrich Mobility Backend

Flask-based REST API for Ostrich Mobility management system.

## Features

- JWT Authentication
- Customer Management
- Product Management
- Sales & Dispatch Tracking
- Service Tickets
- Reports & Analytics

## Prerequisites

- Python 3.8+
- MySQL Database
- pip

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. Run the application:
```bash
python app.py
```

## Environment Variables

- `DB_HOST` - Database host
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password
- `DB_NAME` - Database name
- `DB_PORT` - Database port (default: 3306)
- `JWT_SECRET_KEY` - Secret key for JWT tokens
- `PORT` - Application port (default: 8002)

## Default Admin Credentials

- Username: `admin`
- Password: `admin123`

**⚠️ Change these credentials in production!**

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/logout` - User logout

### Customers
- `GET /api/v1/customers/` - List customers
- `POST /api/v1/customers/` - Create customer
- `PUT /api/v1/customers/<id>` - Update customer
- `DELETE /api/v1/customers/<id>` - Delete customer

### Products
- `GET /api/v1/products/` - List products
- `POST /api/v1/products/` - Create product
- `PUT /api/v1/products/<id>` - Update product
- `DELETE /api/v1/products/<id>` - Delete product

## Deployment

### Render

1. Create new Web Service
2. Connect your repository
3. Set environment variables
4. Deploy

## Security Notes

- All passwords are hashed using bcrypt/SHA256
- JWT tokens expire after 24 hours
- Rate limiting on login (5 attempts per 15 minutes)
- CORS configured for specific origins
- Input sanitization on all endpoints

## License

Proprietary - Ostrich Mobility
