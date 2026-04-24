# After-School Club Management System

Team members: [Add all group members' names here]

This Part 3 implementation provides a MySQL database schema and a Python command-line application to manage after-school clubs, advisors, students, meetings, events, budgets, and expenses.

## Files

- `sql/schema.sql`: Creates the database, tables, constraints, triggers, and inserts sample data.
- `config/config.json`: MySQL connection settings in JSON format.
- `bin/db.py`: Database connection helper functions.
- `bin/app.py`: Python application logic for managing the club system.
- `main.py`: Root entry point for the application.
- `requirements.txt`: Python dependency list.

## Prerequisites

- MySQL 8.0 or later
- Python 3.10+ installed
- `mysql-connector-python` Python package

## Setup

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Create the database and sample data:

```bash
mysql -u root -p
CREATE DATABASE afterschool_clubs;
USE afterschool_clubs;
SOURCE ./sql/schema.sql;
```

3. Update `config/config.json` with your MySQL credentials.

## Running the Application

Run the Python application from the project directory:

```bash
python main.py
```

The application provides a command menu for:

- adding and deleting meetings/events
- recording budgets and expenses
- managing advisors and student memberships
- viewing club members, advisors, schedules, and financial reports
- checking scheduling conflicts

## Notes

- Scheduling conflict checks are enforced by MySQL triggers in the `activity` table.
- Sample data includes clubs, faculty advisors, students, yearly budgets, activities, and expenses for 2024 and 2025.
