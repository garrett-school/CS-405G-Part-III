import sys
from datetime import datetime

from mysql.connector import Error

from bin.db import connect_db

MENU = '''
After-School Club Management
1. Add meeting or event
2. Delete meeting or event
3. View students in a club for a year
4. View all clubs and advisors for a year
5. View club schedule for a year
6. Record or update club budget
7. Record expense for a club
8. Report club expense summary
9. Report total budget for a year
10. Assign faculty advisor for a club year
11. List clubs advised by faculty
12. Student joins a club
13. Student leaves a club
14. List members of a club
15. List clubs for a student
16. View student schedule for a date
0. Exit
'''


def fetch_all(cursor, query, params=None):
    cursor.execute(query, params or ())
    return cursor.fetchall()


def fetch_one(cursor, query, params=None):
    cursor.execute(query, params or ())
    return cursor.fetchone()


def select_club_year_id(cursor, club_name, year):
    result = fetch_one(
        cursor,
        'SELECT cy.club_year_id FROM club_year cy JOIN clubs c ON cy.club_id = c.club_id WHERE c.club_name = %s AND cy.year = %s',
        (club_name, year),
    )
    return result[0] if result else None


def select_student_id(cursor, first_name, last_name):
    result = fetch_one(
        cursor,
        'SELECT student_id FROM students WHERE first_name = %s AND last_name = %s',
        (first_name, last_name),
    )
    return result[0] if result else None


def select_faculty_id(cursor, first_name, last_name):
    result = fetch_one(
        cursor,
        'SELECT faculty_id FROM faculty WHERE first_name = %s AND last_name = %s',
        (first_name, last_name),
    )
    return result[0] if result else None


def add_activity(cursor):
    print('\nAdd meeting or event')
    club_name = input('Club name: ').strip()
    year = input('Year: ').strip()
    activity_type = input('Type (meeting/event): ').strip().lower()
    date_text = input('Date (YYYY-MM-DD): ').strip()
    start_text = input('Start time (HH:MM): ').strip()
    end_text = input('End time (HH:MM): ').strip()
    description = input('Description: ').strip()
    classroom = input('Classroom: ').strip()

    if activity_type not in ('meeting', 'event'):
        print('Invalid activity type.')
        return

    try:
        activity_date = datetime.strptime(date_text, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_text, '%H:%M').time()
        end_time = datetime.strptime(end_text, '%H:%M').time()
    except ValueError:
        print('Date or time format is invalid.')
        return

    club_year_id = select_club_year_id(cursor, club_name, year)
    if not club_year_id:
        print('Club or year not found. Please use an existing club/year combination.')
        return

    query = '''INSERT INTO activity (club_year_id, activity_type, activity_date, start_time, end_time, description, classroom)
               VALUES (%s, %s, %s, %s, %s, %s, %s)'''
    try:
        cursor.execute(query, (club_year_id, activity_type, activity_date, start_time, end_time, description, classroom))
        print('Activity added successfully.')
    except Error as err:
        print('Failed to add activity:', err)


def delete_activity(cursor):
    print('\nDelete meeting or event')
    rows = fetch_all(cursor, 'SELECT a.activity_id, c.club_name, cy.year, a.activity_type, a.activity_date, a.start_time, a.end_time, a.classroom, a.description FROM activity a JOIN club_year cy ON a.club_year_id = cy.club_year_id JOIN clubs c ON cy.club_id = c.club_id ORDER BY a.activity_date, a.start_time')
    if not rows:
        print('No activities found.')
        return
    for row in rows:
        activity_id, club_name, year, activity_type, activity_date, start_time, end_time, classroom, description = row
        print(f'{activity_id}: {club_name} ({year}) {activity_type} {activity_date} {start_time}-{end_time} in {classroom} - {description}')
    activity_id = input('Enter activity_id to delete: ').strip()
    if not activity_id.isdigit():
        print('Invalid ID.')
        return
    cursor.execute('DELETE FROM activity WHERE activity_id = %s', (activity_id,))
    if cursor.rowcount:
        print('Activity deleted.')
    else:
        print('Activity ID not found.')


def view_students_in_club(cursor):
    print('\nView students in a club for a year')
    club_name = input('Club name: ').strip()
    year = input('Year: ').strip()
    query = '''SELECT s.first_name, s.last_name, s.grade, cm.joined_on
               FROM club_membership cm
               JOIN students s ON cm.student_id = s.student_id
               JOIN club_year cy ON cm.club_year_id = cy.club_year_id
               JOIN clubs c ON cy.club_id = c.club_id
               WHERE c.club_name = %s AND cy.year = %s
               ORDER BY s.last_name, s.first_name'''
    rows = fetch_all(cursor, query, (club_name, year))
    if rows:
        print(f'Club members for {club_name} ({year}):')
        for first_name, last_name, grade, joined_on in rows:
            print(f'- {first_name} {last_name}, grade {grade}, joined on {joined_on}')
    else:
        print('No members found or invalid club/year.')


def view_clubs_and_advisors(cursor):
    print('\nView all clubs and advisors for a year')
    year = input('Year: ').strip()
    query = '''SELECT c.club_name, CONCAT(f.first_name, ' ', f.last_name), cy.budget
               FROM club_year cy
               JOIN clubs c ON cy.club_id = c.club_id
               JOIN faculty f ON cy.advisor_id = f.faculty_id
               WHERE cy.year = %s
               ORDER BY c.club_name'''
    rows = fetch_all(cursor, query, (year,))
    if rows:
        for club_name, faculty_name, budget in rows:
            print(f'- {club_name}: Advisor {faculty_name}, budget ${budget:.2f}')
    else:
        print('No clubs found for that year.')


def view_club_schedule(cursor):
    print('\nView club schedule for a year')
    club_name = input('Club name: ').strip()
    year = input('Year: ').strip()
    query = '''SELECT a.activity_type, a.activity_date, a.start_time, a.end_time, a.classroom, a.description
               FROM activity a
               JOIN club_year cy ON a.club_year_id = cy.club_year_id
               JOIN clubs c ON cy.club_id = c.club_id
               WHERE c.club_name = %s AND cy.year = %s
               ORDER BY a.activity_date, a.start_time'''
    rows = fetch_all(cursor, query, (club_name, year))
    if rows:
        for activity_type, activity_date, start_time, end_time, classroom, description in rows:
            print(f'- {activity_date}: {activity_type} from {start_time} to {end_time} in {classroom} - {description}')
    else:
        print('No schedule found for that club in that year.')


def record_budget(cursor):
    print('\nRecord or update club budget')
    club_name = input('Club name: ').strip()
    year = input('Year: ').strip()
    amount = input('Budget amount: ').strip()
    try:
        budget = float(amount)
    except ValueError:
        print('Invalid amount.')
        return
    club_year_id = select_club_year_id(cursor, club_name, year)
    if club_year_id:
        cursor.execute('UPDATE club_year SET budget = %s WHERE club_year_id = %s', (budget, club_year_id))
        print('Budget updated.')
    else:
        advisor_name = input('Advisor first and last name: ').strip().split()
        if len(advisor_name) != 2:
            print('Provide first and last name for advisor.')
            return
        advisor_id = select_faculty_id(cursor, advisor_name[0], advisor_name[1])
        if not advisor_id:
            print('Advisor not found.')
            return
        cursor.execute('INSERT INTO club_year (club_id, year, advisor_id, budget) VALUES ((SELECT club_id FROM clubs WHERE club_name = %s), %s, %s, %s)',
                       (club_name, year, advisor_id, budget))
        print('Club/year record created and budget recorded.')


def record_expense(cursor):
    print('\nRecord expense for a club')
    club_name = input('Club name: ').strip()
    year = input('Year: ').strip()
    amount_text = input('Expense amount: ').strip()
    description = input('Description: ').strip()
    date_text = input('Expense date (YYYY-MM-DD): ').strip()

    try:
        amount = float(amount_text)
        expense_date = datetime.strptime(date_text, '%Y-%m-%d').date()
    except ValueError:
        print('Invalid amount or date format.')
        return

    club_year_id = select_club_year_id(cursor, club_name, year)
    if not club_year_id:
        print('Club/year not found.')
        return
    cursor.execute('INSERT INTO expenses (club_year_id, expense_date, amount, description) VALUES (%s, %s, %s, %s)',
                   (club_year_id, expense_date, amount, description))
    print('Expense recorded.')


def report_club_summary(cursor):
    print('\nReport club expense summary')
    club_name = input('Club name: ').strip()
    year = input('Year: ').strip()
    query = '''SELECT c.club_name, cy.year, cy.budget, IFNULL(SUM(e.amount), 0)
               FROM club_year cy
               JOIN clubs c ON cy.club_id = c.club_id
               LEFT JOIN expenses e ON cy.club_year_id = e.club_year_id
               WHERE c.club_name = %s AND cy.year = %s
               GROUP BY c.club_name, cy.year, cy.budget'''
    row = fetch_one(cursor, query, (club_name, year))
    if row:
        club_name, year, budget, total_expenses = row
        remaining = budget - total_expenses
        print(f'Club {club_name} ({year}) budget: ${budget:.2f}, expenses: ${total_expenses:.2f}, remaining: ${remaining:.2f}')
    else:
        print('Club/year record not found.')


def report_total_budget(cursor):
    print('\nReport total budget for a year')
    year = input('Year: ').strip()
    query = 'SELECT IFNULL(SUM(budget), 0) FROM club_year WHERE year = %s'
    total_budget = fetch_one(cursor, query, (year,))[0]
    print(f'Total budget across all clubs in {year}: ${total_budget:.2f}')


def assign_advisor(cursor):
    print('\nAssign faculty advisor for a club year')
    club_name = input('Club name: ').strip()
    year = input('Year: ').strip()
    advisor_first = input('Advisor first name: ').strip()
    advisor_last = input('Advisor last name: ').strip()
    advisor_id = select_faculty_id(cursor, advisor_first, advisor_last)
    club_year_id = select_club_year_id(cursor, club_name, year)
    if not advisor_id:
        print('Advisor not found.')
        return
    if not club_year_id:
        print('Club/year record not found. Create the club/year record first by recording the budget.')
        return
    cursor.execute('UPDATE club_year SET advisor_id = %s WHERE club_year_id = %s', (advisor_id, club_year_id))
    print('Advisor assigned.')


def list_clubs_by_faculty(cursor):
    print('\nList clubs advised by faculty')
    faculty_name = input('Faculty first and last name: ').strip().split()
    if len(faculty_name) != 2:
        print('Provide first and last name.')
        return
    faculty_id = select_faculty_id(cursor, faculty_name[0], faculty_name[1])
    if not faculty_id:
        print('Faculty not found.')
        return
    query = '''SELECT c.club_name, cy.year
               FROM club_year cy
               JOIN clubs c ON cy.club_id = c.club_id
               WHERE cy.advisor_id = %s
               ORDER BY cy.year, c.club_name'''
    rows = fetch_all(cursor, query, (faculty_id,))
    if rows:
        for club_name, year in rows:
            print(f'- {club_name} ({year})')
    else:
        print('No club assignments found for that faculty member.')


def student_join_club(cursor):
    print('\nStudent joins a club')
    student_first = input('Student first name: ').strip()
    student_last = input('Student last name: ').strip()
    club_name = input('Club name: ').strip()
    year = input('Year: ').strip()
    join_date_text = input('Join date (YYYY-MM-DD): ').strip()
    try:
        joined_on = datetime.strptime(join_date_text, '%Y-%m-%d').date()
    except ValueError:
        print('Invalid date format.')
        return
    student_id = select_student_id(cursor, student_first, student_last)
    club_year_id = select_club_year_id(cursor, club_name, year)
    if not student_id or not club_year_id:
        print('Student or club/year not found.')
        return
    try:
        cursor.execute('INSERT INTO club_membership (student_id, club_year_id, joined_on) VALUES (%s, %s, %s)',
                       (student_id, club_year_id, joined_on))
        print('Student added to club.')
    except Error as err:
        print('Failed to add membership:', err)


def student_leave_club(cursor):
    print('\nStudent leaves a club')
    student_first = input('Student first name: ').strip()
    student_last = input('Student last name: ').strip()
    club_name = input('Club name: ').strip()
    year = input('Year: ').strip()
    student_id = select_student_id(cursor, student_first, student_last)
    club_year_id = select_club_year_id(cursor, club_name, year)
    if not student_id or not club_year_id:
        print('Student or club/year not found.')
        return
    cursor.execute('DELETE FROM club_membership WHERE student_id = %s AND club_year_id = %s', (student_id, club_year_id))
    if cursor.rowcount:
        print('Student removed from club membership.')
    else:
        print('Membership record not found.')


def list_members_of_club(cursor):
    print('\nList members of a club')
    club_name = input('Club name: ').strip()
    year = input('Year: ').strip()
    query = '''SELECT s.first_name, s.last_name, s.grade, cm.joined_on
               FROM club_membership cm
               JOIN students s ON cm.student_id = s.student_id
               JOIN club_year cy ON cm.club_year_id = cy.club_year_id
               JOIN clubs c ON cy.club_id = c.club_id
               WHERE c.club_name = %s AND cy.year = %s
               ORDER BY s.last_name, s.first_name'''
    rows = fetch_all(cursor, query, (club_name, year))
    if rows:
        for first_name, last_name, grade, joined_on in rows:
            print(f'- {first_name} {last_name}, grade {grade}, joined on {joined_on}')
    else:
        print('No members found for that club/year.')


def list_clubs_for_student(cursor):
    print('\nList clubs for a student')
    student_first = input('Student first name: ').strip()
    student_last = input('Student last name: ').strip()
    student_id = select_student_id(cursor, student_first, student_last)
    if not student_id:
        print('Student not found.')
        return
    query = '''SELECT c.club_name, cy.year, cm.joined_on
               FROM club_membership cm
               JOIN club_year cy ON cm.club_year_id = cy.club_year_id
               JOIN clubs c ON cy.club_id = c.club_id
               WHERE cm.student_id = %s
               ORDER BY cy.year, c.club_name'''
    rows = fetch_all(cursor, query, (student_id,))
    if rows:
        for club_name, year, joined_on in rows:
            print(f'- {club_name} ({year}), joined on {joined_on}')
    else:
        print('No club memberships found for that student.')


def view_student_schedule(cursor):
    print('\nView student schedule for a date')
    student_first = input('Student first name: ').strip()
    student_last = input('Student last name: ').strip()
    date_text = input('Date (YYYY-MM-DD): ').strip()
    try:
        schedule_date = datetime.strptime(date_text, '%Y-%m-%d').date()
    except ValueError:
        print('Invalid date format.')
        return
    student_id = select_student_id(cursor, student_first, student_last)
    if not student_id:
        print('Student not found.')
        return
    query = '''SELECT c.club_name, a.activity_type, a.start_time, a.end_time, a.classroom, a.description
               FROM club_membership cm
               JOIN activity a ON cm.club_year_id = a.club_year_id
               JOIN club_year cy ON a.club_year_id = cy.club_year_id
               JOIN clubs c ON cy.club_id = c.club_id
               WHERE cm.student_id = %s AND a.activity_date = %s
               ORDER BY a.start_time'''
    rows = fetch_all(cursor, query, (student_id, schedule_date))
    if rows:
        print(f'Activities for {student_first} {student_last} on {schedule_date}:')
        for club_name, activity_type, start_time, end_time, classroom, description in rows:
            print(f'- {club_name}: {activity_type} {start_time}-{end_time} in {classroom} - {description}')
    else:
        print('No scheduled activities found for that student on this date.')


def main():
    connection = connect_db()
    cursor = connection.cursor()
    while True:
        print(MENU)
        choice = input('Select an option: ').strip()
        if choice == '0':
            break
        try:
            if choice == '1':
                add_activity(cursor)
            elif choice == '2':
                delete_activity(cursor)
            elif choice == '3':
                view_students_in_club(cursor)
            elif choice == '4':
                view_clubs_and_advisors(cursor)
            elif choice == '5':
                view_club_schedule(cursor)
            elif choice == '6':
                record_budget(cursor)
            elif choice == '7':
                record_expense(cursor)
            elif choice == '8':
                report_club_summary(cursor)
            elif choice == '9':
                report_total_budget(cursor)
            elif choice == '10':
                assign_advisor(cursor)
            elif choice == '11':
                list_clubs_by_faculty(cursor)
            elif choice == '12':
                student_join_club(cursor)
            elif choice == '13':
                student_leave_club(cursor)
            elif choice == '14':
                list_members_of_club(cursor)
            elif choice == '15':
                list_clubs_for_student(cursor)
            elif choice == '16':
                view_student_schedule(cursor)
            else:
                print('Unknown option.')
            connection.commit()
        except Error as err:
            connection.rollback()
            print('Database error:', err)
    cursor.close()
    connection.close()
    print('Goodbye.')
