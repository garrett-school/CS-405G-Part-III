# CS405 Project: Middle-School Club Management System

Team members: Brett Carson, Jacob Schuetter, Garrett Strange, and Alex Vela

This project is a MySQL database and Python command-line application for managing a middle school's after-school clubs. It stores info about clubs, faculty advisors, students, memberships, meetings, events, budgets, and expenses.

## Files

- `schema.sql`: Creates the database tables, constraints, views, triggers, and some sample data for testing

- `app.py`: Python program for viewing and managing the club data.

- `README.md`: General information, setup, and running instructions

## Required Software and Libraries

- MySQL 
- Python 3
- `mysql-connector-python`

Install the Python library with:

```bash
python3 -m pip install mysql-connector-python
```

## Database Setup

schema.sql is database-name neutral, so select the database name when running it. 
You can use either the UK CS MySQL server or your own local MySQL installation

### Option A: UK CS MySQL Server

Run:

```bash
mysql -h mysql.cs.uky.edu -u YOUR_USERNAME -p YOUR_DATABASE_NAME < schema.sql
```

### Option B: Local MySQL

First, create a database with statement:

```bash
mysql -u root -p
```

Next, in MySQL, use statement:

```sql
CREATE DATABASE IF NOT EXISTS afterschool_club;
exit;
```

Then, load the schema with statement:

```bash
mysql -u root -p afterschool_club < schema.sql
```


## Running the Python Program

Run the program from the folder containing `app.py` with statement:

```bash
python3 app.py
```

The program will ask for the database name and MySQL password.

By default, the program uses:

- host: `mysql.cs.uky.edu`
- username: same as the database name

To use a different MySQL host or username, set these environment variables before running.

Example (if using local MySQL):

```bash
MYSQL_HOST=localhost MYSQL_USER=root python3 app.py
```

Then fill in the following:

```text
Database name: afterschool_club
MySQL password: your local MySQL password
```

Then, you can navigate through the menu in the Python program to view and manage the database data.


## Application Functionality

The Python program provides a menu that supports basic database operations, including:

- view all clubs and advisors for a school year
- view students in a club for a school year
- view meetings and events for a club
- view a club's budget, total expenses, and remaining budget
- view total budget across all clubs for a school year
- add meetings and events
- delete meetings and events
- record expenses
- add or remove student memberships
- view all clubs for a student
- view a student's schedule on a specific date
- assign or update a faculty advisor for a club-year
- view all clubs advised by a faculty member
- record or update a budget for a club-year


## Important Database Constraints

The database enforces the major project constraints, including:

- each club has a unique club name
- each faculty member and student has a unique ID
- each active club-year has exactly one advisor through advises(club_name, school_year, faculty_id)
- year-specific records such as meetings, events, memberships, and budgets must reference a valid club-year advisor assignment
- budgets and expenses must be nonnegative
- meeting and event start times must be before end times
- expenses must reference an existing budget for that club-year
- triggers prevent double-booking of classrooms for meetings
- triggers reject overlapping meetings or events for the same club on the same date
- triggers reject a meeting that overlaps with an event for the same club on the same date, and vice versa
- triggers prevent a club’s total expenses from exceeding its yearly budget
- triggers prevent lowering a club’s budget below expenses already recorded for that year
