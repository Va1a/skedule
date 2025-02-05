# Skedule Project Knowledge

## Overview
Open source scheduling & employee management tool built with Flask. Provides shift management, templating, and employee scheduling capabilities.

## Architecture
- Flask-based web application
- SQLAlchemy ORM for database management
- Blueprint structure for route organization:
  - main: Core scheduling views
  - admin: Schedule configuration and templates
  - api: RESTful endpoints
  - users: Authentication and user management

## Key Features
- Shift scheduling with min/max employee constraints
- Shift templates for repeatable schedules
- Employee shift requests and assignments
- Week-based schedule viewing and management
- Admin controls for schedule configuration

## Database Models
- User: Employee information and authentication
- Day: Container for shifts on a specific date
- Shift: Individual work periods with constraints
- Template: Reusable shift patterns
- Assignment: Links users to shifts with metadata

## Time Handling
- All times stored in US/Pacific timezone
- Times formatted as HHMM (24-hour)
- Dates handled as Python datetime objects

## Security
- BCrypt password hashing
- Flask-Login for session management
- Protected admin routes
- API endpoints require authentication

## Environment Variables
Required:
- SKEDULE_SECRET_KEY: Flask secret key
- DATABASE_URL: Database connection string (falls back to SQLite)
- RECAPTCHA_SITE_KEY: Google ReCAPTCHA public key
- RECAPTCHA_SECRET_KEY: Google ReCAPTCHA private key