# Users Blueprint Knowledge

## Purpose
Handles user authentication and account management.

## Features
- User registration with external ID
- Email/password authentication
- Session management
- Logout handling

## Routes
- /register: New user registration
- /login: User authentication
- /logout: Session termination

## Security
- Passwords hashed with BCrypt
- Remember-me functionality
- Next-page redirect after login