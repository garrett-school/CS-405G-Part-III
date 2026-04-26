#!/usr/bin/env python3

from datetime import datetime
from decimal import Decimal, InvalidOperation
from getpass import getpass
import os
import sys

import mysql.connector
from mysql.connector import Error

# This is the default host for the UK CS MySQL server (program asks for the database name and password at startup)
# If using the UK CS server, the MySQL username should be the same as the database name
# If a different username or host is needed, set MYSQL_USER or MYSQL_HOST before running
DEFAULT_HOST = os.environ.get("MYSQL_HOST", "mysql.cs.uky.edu")

# Menu of options for user to explore
MENU = """
After-School Club Management System
1. View all clubs and advisors for a school year
2. View students in a club for a school year
3. View meetings and events for a club
4. View financial report for a club
5. View total budget for a school year
6. Add a meeting
7. Add an event
8. Record an expense
9. Student joins a club
10. Student leaves a club
11. View all clubs for a student
12. View student schedule on a date
13. Assign or update advisor for a club-year
14. Record or update budget for a club-year
15. Delete a meeting
16. Delete an event
17. View all clubs advised by a faculty member
0. Exit
"""

# Connect to database with database name and password
def connect_db():
    print("Database connection setup")
    print("For the UK CS server, enter your assigned database name. This is usually your linkblue ID.")

    database = input("Database name: ").strip()
    if database == "":
        print("A database name is required.")
        sys.exit(1)

    # On the UK CS MySQL server, the username should be the same as the assigned database name. 
    host = DEFAULT_HOST
    user = os.environ.get("MYSQL_USER", database)
    password = getpass("MySQL password: ")

    config = {
        "host": host,
        "user": user,
        "password": password,
        "database": database,
        "raise_on_warnings": True,
    }

    try:
        return mysql.connector.connect(**config)
    except Error as err:
        print("Failed to connect to the database:", err)
        print("Host used:", host)
        print("User used:", user)
        print("Database used:", database)
        sys.exit(1)

# Run a query and retrieve all corresponding rows
def fetch_all(cursor, query, params=None):
    cursor.execute(query, params or ())
    return cursor.fetchall()

# Run a query and retrieve the first found row
def fetch_one(cursor, query, params=None):
    cursor.execute(query, params or ())
    return cursor.fetchone()

# Read a date provided by the user
def input_date(prompt):
    value = input(prompt).strip()
    return datetime.strptime(value, "%Y-%m-%d").date()

# Read a time provided by the user
def input_time(prompt):
    value = input(prompt).strip()
    return datetime.strptime(value, "%H:%M").time()

# Read a dollar amount from the user (for budget or expense)
def input_money(prompt):
    value = input(prompt).strip()
    amount = Decimal(value)
    if amount < 0:
        raise ValueError("Amount cannot be negative.")
    return amount


# Report rows from database to user
def print_rows(rows, headers):
    # If empty, report no records to show
    if not rows:
        print("No records found.")
        return
    
    # Adjust for visual purposes
    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(str(value)))

    # Report data cleanly
    header_line = " | ".join(headers[index].ljust(widths[index]) for index in range(len(headers)))
    separator = "-+-".join("-" * width for width in widths)
    print(header_line)
    print(separator)
    for row in rows:
        print(" | ".join(str(row[index]).ljust(widths[index]) for index in range(len(row))))


# Allow user to view the clubs and corresponding advisors for a chosen year
def view_clubs_and_advisors(cursor):
    school_year = input("School year: ").strip()
    query = """
        SELECT a.club_name, f.faculty_name, f.email
        FROM advises a
        JOIN faculty f ON a.faculty_id = f.faculty_id
        WHERE a.school_year = %s
        ORDER BY a.club_name
    """
    rows = fetch_all(cursor, query, (school_year,))
    print_rows(rows, ["Club", "Advisor", "Email"])

# Allow user to view the students for a chosen club + year
def view_students_in_club(cursor):
    club_name = input("Club name: ").strip()
    school_year = input("School year: ").strip()
    query = """
        SELECT s.student_id, s.student_name, s.student_grade
        FROM member m
        JOIN student s ON m.student_id = s.student_id
        WHERE m.club_name = %s AND m.school_year = %s
        ORDER BY s.student_name
    """
    rows = fetch_all(cursor, query, (club_name, school_year))
    print_rows(rows, ["Student ID", "Student", "Grade"])

# Allow user to see all meetings and events of a chosen club in a chosen year
def view_club_schedule(cursor):
    club_name = input("Club name: ").strip()
    school_year = input("School year: ").strip()
    query = """
        SELECT activity_id, activity_type, activity_date, start_time, end_time, classroom, details

        FROM club_schedule
        WHERE club_name = %s AND school_year = %s
        ORDER BY activity_date, start_time, activity_type
    """
    rows = fetch_all(cursor, query, (club_name, school_year))
    print_rows(rows, ["ID", "Type", "Date", "Start", "End", "Classroom", "Description"])


# Allow the user to see the budget and expenses for a chosen club in a chosen year
def view_financial_report(cursor):
    club_name = input("Club name: ").strip()
    school_year = input("School year: ").strip()
    query = """
        SELECT club_name, school_year, budget_amount, total_expenses, remaining_budget
        FROM club_financial_report
        WHERE club_name = %s AND school_year = %s
    """
    rows = fetch_all(cursor, query, (club_name, school_year))
    print_rows(rows, ["Club", "Year", "Budget", "Expenses", "Remaining"])

# Allow user to see the total budget across all clubs in a chosen school year
def view_total_budget(cursor):
    school_year = input("School year: ").strip()
    query = "SELECT SUM(budget_amount) FROM budget WHERE school_year = %s"
    total = fetch_one(cursor, query, (school_year,))[0]
    # Handle case of no budget existing
    if total is None:
        total = 0
    print(f"Total budget for {school_year}: ${total:.2f}")



# Allow user to add a new meeting at a certain time for a club in a year
def add_meeting(cursor):
    club_name = input("Club name: ").strip()
    school_year = input("School year: ").strip()
    meeting_date = input_date("Meeting date (YYYY-MM-DD): ")
    start_time = input_time("Start time (HH:MM): ")
    end_time = input_time("End time (HH:MM): ")
    description = input("Description: ").strip()
    classroom = input("Classroom: ").strip()

    query = """
        INSERT INTO meeting
            (meeting_date, start_time, end_time, details, classroom, school_year, club_name)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (meeting_date, start_time, end_time, description, classroom, school_year, club_name))
    print("Meeting added. Overlapping meetings are rejected by database triggers.")

# Allow user to add a new event at a certain time for a club in a year
def add_event(cursor):
    club_name = input("Club name: ").strip()
    school_year = input("School year: ").strip()
    event_date = input_date("Event date (YYYY-MM-DD): ")
    start_time = input_time("Start time (HH:MM): ")
    end_time = input_time("End time (HH:MM): ")
    description = input("Description: ").strip()

    query = """
        INSERT INTO club_event
            (event_date, start_time, end_time, details, school_year, club_name)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (event_date, start_time, end_time, description, school_year, club_name))
    print("Event added.")


# Allow user to add a new expense for a club in a year with given details
def record_expense(cursor):
    club_name = input("Club name: ").strip()
    school_year = input("School year: ").strip()
    expense_date = input_date("Expense date (YYYY-MM-DD): ")
    amount = input_money("Amount: ")
    description = input("Description: ").strip()

    query = """
        INSERT INTO expense (expense_date, amount, details, school_year, club_name)
        VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(query, (expense_date, amount, description, school_year, club_name))
    print("Expense recorded.")


# Allow user to add a student to a club in a certain year
def student_joins_club(cursor):
    student_id = int(input("Student ID: ").strip())
    club_name = input("Club name: ").strip()
    school_year = input("School year: ").strip()
    query = "INSERT INTO member (student_id, club_name, school_year) VALUES (%s, %s, %s)"
    cursor.execute(query, (student_id, club_name, school_year))
    print("Student membership added.")


# Allow user to remove a student from a club in a certain year
def student_leaves_club(cursor):
    student_id = int(input("Student ID: ").strip())
    club_name = input("Club name: ").strip()
    school_year = input("School year: ").strip()
    query = "DELETE FROM member WHERE student_id = %s AND club_name = %s AND school_year = %s"
    cursor.execute(query, (student_id, club_name, school_year))
    if cursor.rowcount == 0:
        print("No matching membership was found.")
    else:
        print("Student membership removed.")


# Display all club memberships for a student with the given ID
def view_student_clubs(cursor):
    student_id = int(input("Student ID: ").strip())
    query = """
        SELECT s.student_name, m.club_name, m.school_year
        FROM member m
        JOIN student s ON m.student_id = s.student_id
        WHERE m.student_id = %s
        ORDER BY m.school_year, m.club_name
    """
    rows = fetch_all(cursor, query, (student_id,))
    print_rows(rows, ["Student", "Club", "Year"])


# View all meetings and events for all the clubs a student with the given ID is in
def view_student_schedule(cursor):
    student_id = int(input("Student ID: ").strip())
    schedule_date = input_date("Date (YYYY-MM-DD): ")
    query = """
        SELECT cs.club_name, cs.school_year, cs.activity_type, cs.start_time, cs.end_time, cs.classroom, cs.details

        FROM member m
        JOIN club_schedule cs
          ON m.club_name = cs.club_name
         AND m.school_year = cs.school_year
        WHERE m.student_id = %s AND cs.activity_date = %s
        ORDER BY cs.start_time, cs.club_name, cs.activity_type
    """
    rows = fetch_all(cursor, query, (student_id, schedule_date))
    print_rows(rows, ["Club", "Year", "Type", "Start", "End", "Classroom", "Description"])


# Allow user to assign an advisor to a club in a specified year
def assign_advisor(cursor):
    club_name = input("Club name: ").strip()
    school_year = input("School year: ").strip()
    faculty_id = int(input("Faculty ID: ").strip())

    # Check if there is already an advisor
    exists = fetch_one(
        cursor,
        "SELECT COUNT(*) FROM advises WHERE club_name = %s AND school_year = %s",
        (club_name, school_year),
    )[0]

    # If there is an advisor, update for new advisor assignment
    if exists:
        cursor.execute(
            "UPDATE advises SET faculty_id = %s WHERE club_name = %s AND school_year = %s",
            (faculty_id, club_name, school_year),
        )
        print("Advisor updated.")

    # Otherwise, insert the new advisor as the club advisor for this year
    else:
        cursor.execute(
            "INSERT INTO advises (club_name, school_year, faculty_id) VALUES (%s, %s, %s)",
            (club_name, school_year, faculty_id),
        )
        print("Advisor assigned.")


# Allow the user to enter the budget for a club-year record
def record_budget(cursor):
    club_name = input("Club name: ").strip()
    school_year = input("School year: ").strip()
    budget_amount = input_money("Budget amount: ")

    # See if budget record exists for this club-year pair
    exists = fetch_one(
        cursor,
        "SELECT COUNT(*) FROM budget WHERE club_name = %s AND school_year = %s",
        (club_name, school_year),
    )[0]

    # If there is a budget, update record
    if exists:
        cursor.execute(
            "UPDATE budget SET budget_amount = %s WHERE club_name = %s AND school_year = %s",
            (budget_amount, club_name, school_year),
        )
        print("Budget updated.")

    # Otherwise, insert new budget for club-year pair
    else:
        cursor.execute(
            "INSERT INTO budget (club_name, school_year, budget_amount) VALUES (%s, %s, %s)",
            (club_name, school_year, budget_amount),
        )
        print("Budget recorded.")


# Allow the user to delete a meeting with the corresponding meeting ID
def delete_meeting(cursor):
    meeting_id = int(input("Meeting ID to delete: ").strip())
    query = "DELETE FROM meeting WHERE meeting_id = %s"
    cursor.execute(query, (meeting_id,))

    # See if this record exists, and report to user
    if cursor.rowcount == 0:
        print("No meeting with that ID was found.")
    else:
        print("Meeting deleted.")


# Allow the user to delete an event with the corresponding event ID
def delete_event(cursor):
    event_id = int(input("Event ID to delete: ").strip())
    query = "DELETE FROM club_event WHERE event_id = %s"
    cursor.execute(query, (event_id,))

    # See if this record exists, and report to user
    if cursor.rowcount == 0:
        print("No event with that ID was found.")
    else:
        print("Event deleted.")


# Allow the user to input a faculty ID to see which clubs they advise or have advised in past years
def view_clubs_by_faculty(cursor):
    faculty_id = int(input("Faculty ID: ").strip())
    query = """
        SELECT f.faculty_name, a.club_name, a.school_year
        FROM advises a
        JOIN faculty f ON a.faculty_id = f.faculty_id
        WHERE a.faculty_id = %s
        ORDER BY a.school_year, a.club_name
    """
    # Fetch all records for this faculty member advising clubs, and report all rows
    rows = fetch_all(cursor, query, (faculty_id,))
    print_rows(rows, ["Advisor", "Club", "Year"])


# Main function: Connect to database and allow user to explore options
def main():
    connection = connect_db()
    cursor = connection.cursor()

    # List of all actions user can take to explore database
    actions = {
        "1": view_clubs_and_advisors,
        "2": view_students_in_club,
        "3": view_club_schedule,
        "4": view_financial_report,
        "5": view_total_budget,
        "6": add_meeting,
        "7": add_event,
        "8": record_expense,
        "9": student_joins_club,
        "10": student_leaves_club,
        "11": view_student_clubs,
        "12": view_student_schedule,
        "13": assign_advisor,
        "14": record_budget,
        "15": delete_meeting,
        "16": delete_event,
        "17": view_clubs_by_faculty,
    }

    # Until the user enters 0 to quit, allow them to explore database with given options
    while True:
        print(MENU)
        choice = input("Select an option: ").strip()
        if choice == "0":
            # Quit if user enters "0"
            break

        # If action not in list, then try again
        action = actions.get(choice)
        if action is None:
            print("Unknown option.")
            continue

        # Based on user's input, proceed (perform action, allow reentry, or trigger error)
        try:
            action(cursor)
            connection.commit()
        except (ValueError, InvalidOperation):
            connection.rollback()
            print("Invalid input. Please check the required format and try again.")
        except Error as err:
            connection.rollback()
            print("Database error:", err)

    # End the connection, as the user has quit
    cursor.close()
    connection.close()
    print("Goodbye.")


if __name__ == "__main__":
    main()
