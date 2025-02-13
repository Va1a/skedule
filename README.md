# Skedule

An open source employee scheduling and shift management system built with Flask.

## Features

- 📅 Week-based schedule viewing and management
- 👥 Employee shift requests and assignments
- 📋 Shift templates for repeatable schedules
- 🔒 User authentication and role-based access
- 📱 Responsive web interface
- 🔄 Real-time schedule updates
- 📊 Employee roster management

## Getting Started

### Prerequisites

- Python 3.12+
- pip package manager

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/skedule.git
cd skedule
```

2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
```bash
# Create a .env file with the following variables
SKEDULE_SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///site.db  # Or your database URL
RECAPTCHA_SITE_KEY=your_recaptcha_site_key
RECAPTCHA_SECRET_KEY=your_recaptcha_secret_key
```

5. Initialize the database
```bash
python drop_create_db.py
```

6. (Optional) Create sample data
```bash
python create_dummy_data.py
```

7. Run the development server
```bash
python run.py
```

The application will be available at `http://localhost:8080`

## Project Structure

```
skedule/
├── admin/         # Administrative functionality
├── api/           # REST API endpoints
├── errors/        # Error handlers
├── main/          # Core scheduling views
├── static/        # CSS, JavaScript, and assets
├── templates/     # HTML templates
└── users/         # User authentication and management
```

## Testing

Run the test suite:
```bash
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is open source and available under the [GPL-3.0 License](LICENSE).

## Acknowledgments

- Built with Flask and SQLAlchemy
- Uses Bootstrap for responsive design
- Feather icons for UI elements