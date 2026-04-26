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


def club_year_exists(cursor, club_name, school_year):
    result = fetch_one(
        cursor,
        'SELECT 1 FROM club_year WHERE club_name = %s AND school_year = %s',
        (club_name, school_year),
    )
    return result is not None


def select_student_id(cursor, student_name):
    result = fetch_one(
        cursor,
        'SELECT student_id FROM student WHERE student_name = %s',
        (student_name,),
    )
    return result[0] if result else None


def select_faculty_id(cursor, faculty_name):
    result = fetch_one(
        cursor,
        'SELECT faculty_id FROM faculty WHERE faculty_name = %s',
        (faculty_name,),
    )
    return result[0] if result else None


def add_activity(cursor):
    print('\nAdd meeting or event')
    club_name = input('Club name: ').strip()
    school_year = input('Year: ').strip()
    activity_type = input('Type (meeting/event): ').strip().lower()
    date_text = input('Date (YYYY-MM-DD): ').strip()
    start_text = input('Start time (HH:MM): ').strip()
    end_text = input('End time (HH:MM): ').strip()
    description = input('Description: ').strip()

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

    if not club_year_exists(cursor, club_name, school_year):
        print('Club or year not found. Please use an existing club/year combination.')
        return

    try:
        if activity_type == 'meeting':
            classroom = input('Classroom: ').strip()
            cursor.execute(
                'INSERT INTO meeting (club_name, school_year, meeting_date, start_time, end_time, description, classroom) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (club_name, school_year, activity_date, start_time, end_time, description, classroom),
            )
        else:
            cursor.execute(
                'INSERT INTO `event` (club_name, school_year, event_date, start_time, end_time, description) VALUES (%s, %s, %s, %s, %s, %s)',
                (club_name, school_year, activity_date, start_time, end_time, description),
            )
        print('Activity added successfully.')
    except Error as err:
        print('Failed to add activity:', err)


def delete_activity(cursor):
    print('\nDelete meeting or event')
    meetings = fetch_all(
        cursor,
        "SELECT meeting_id, club_name, school_year, 'meeting', meeting_date, start_time, end_time, classroom, description FROM meeting ORDER BY meeting_date, start_time",
    )
    events = fetch_all(
        cursor,
        "SELECT event_id, club_name, school_year, 'event', event_date, start_time, end_time, NULL, description FROM `event` ORDER BY event_date, start_time",
    )
    rows = [('M', *r) for r in meetings] + [('E', *r) for r in events]
    if not rows:
        print('No activities found.')
        return
    for prefix, row_id, club_name, school_year, activity_type, activity_date, start_time, end_time, classroom, description in rows:
        classroom_str = classroom if classroom else 'N/A'
        print(f'{prefix}{row_id}: {club_name} ({school_year}) {activity_type} {activity_date} {start_time}-{end_time} in {classroom_str} - {description}')
    activity_ref = input('Enter ID to delete (M# for meeting, E# for event, e.g. M1 or E2): ').strip().upper()
    if not activity_ref or activity_ref[0] not in ('M', 'E') or not activity_ref[1:].isdigit():
        print('Invalid ID.')
        return
    prefix = activity_ref[0]
    row_id = int(activity_ref[1:])
    if prefix == 'M':
        cursor.execute('DELETE FROM meeting WHERE meeting_id = %s', (row_id,))
    else:
        cursor.execute('DELETE FROM `event` WHERE event_id = %s', (row_id,))
    if cursor.rowcount:
        print('Activity deleted.')
    else:
        print('Activity ID not found.')


def view_students_in_club(cursor):
    print('\nView students in a club for a year')
    club_name = input('Club name: ').strip()
    school_year = input('Year: ').strip()
    query = '''SELECT s.student_name, s.grade
               FROM member m
               JOIN student s ON m.student_id = s.student_id
               WHERE m.club_name = %s AND m.school_year = %s
               ORDER BY s.student_name'''
    rows = fetch_all(cursor, query, (club_name, school_year))
    if rows:
        print(f'Club members for {club_name} ({school_year}):')
        for student_name, grade in rows:
            print(f'- {student_name}, grade {grade}')
    else:
        print('No members found or invalid club/year.')


def view_clubs_and_advisors(cursor):
    print('\nView all clubs and advisors for a year')
    school_year = input('Year: ').strip()
    query = '''SELECT cy.club_name, f.faculty_name, cy.budget_amount
               FROM club_year cy
               JOIN faculty f ON cy.faculty_id = f.faculty_id
               WHERE cy.school_year = %s
               ORDER BY cy.club_name'''
    rows = fetch_all(cursor, query, (school_year,))
    if rows:
        for club_name, faculty_name, budget_amount in rows:
            print(f'- {club_name}: Advisor {faculty_name}, budget ${budget_amount:.2f}')
    else:
        print('No clubs found for that year.')


def view_club_schedule(cursor):
    print('\nView club schedule for a year')
    club_name = input('Club name: ').strip()
    school_year = input('Year: ').strip()
    query = '''SELECT 'meeting' AS activity_type, meeting_date AS activity_date, start_time, end_time, classroom, description
               FROM meeting
               WHERE club_name = %s AND school_year = %s
               UNION ALL
               SELECT 'event', event_date, start_time, end_time, NULL, description
               FROM `event`
               WHERE club_name = %s AND school_year = %s
               ORDER BY activity_date, start_time'''
    rows = fetch_all(cursor, query, (club_name, school_year, club_name, school_year))
    if rows:
        for activity_type, activity_date, start_time, end_time, classroom, description in rows:
            classroom_str = f' in {classroom}' if classroom else ''
            print(f'- {activity_date}: {activity_type} from {start_time} to {end_time}{classroom_str} - {description}')
    else:
        print('No schedule found for that club in that year.')


def record_budget(cursor):
    print('\nRecord or update club budget')
    club_name = input('Club name: ').strip()
    school_year = input('Year: ').strip()
    amount = input('Budget amount: ').strip()
    try:
        budget = float(amount)
    except ValueError:
        print('Invalid amount.')
        return
    if club_year_exists(cursor, club_name, school_year):
        cursor.execute('UPDATE club_year SET budget_amount = %s WHERE club_name = %s AND school_year = %s', (budget, club_name, school_year))
        print('Budget updated.')
    else:
        faculty_name = input('Faculty advisor name: ').strip()
        faculty_id = select_faculty_id(cursor, faculty_name)
        if not faculty_id:
            print('Advisor not found.')
            return
        cursor.execute(
            'INSERT INTO club_year (club_name, school_year, faculty_id, budget_amount) VALUES (%s, %s, %s, %s)',
            (club_name, school_year, faculty_id, budget),
        )
        print('Club/year record created and budget recorded.')


def record_expense(cursor):
    print('\nRecord expense for a club')
    club_name = input('Club name: ').strip()
    school_year = input('Year: ').strip()
    amount_text = input('Expense amount: ').strip()
    description = input('Description: ').strip()
    date_text = input('Expense date (YYYY-MM-DD): ').strip()

    try:
        amount = float(amount_text)
        expense_date = datetime.strptime(date_text, '%Y-%m-%d').date()
    except ValueError:
        print('Invalid amount or date format.')
        return

    if not club_year_exists(cursor, club_name, school_year):
        print('Club/year not found.')
        return
    cursor.execute(
        'INSERT INTO expense (club_name, school_year, expense_date, amount, description) VALUES (%s, %s, %s, %s, %s)',
        (club_name, school_year, expense_date, amount, description),
    )
    print('Expense recorded.')


def report_club_summary(cursor):
    print('\nReport club expense summary')
    club_name = input('Club name: ').strip()
    school_year = input('Year: ').strip()
    query = '''SELECT cy.club_name, cy.school_year, cy.budget_amount, IFNULL(SUM(e.amount), 0)
               FROM club_year cy
               LEFT JOIN expense e ON cy.club_name = e.club_name AND cy.school_year = e.school_year
               WHERE cy.club_name = %s AND cy.school_year = %s
               GROUP BY cy.club_name, cy.school_year, cy.budget_amount'''
    row = fetch_one(cursor, query, (club_name, school_year))
    if row:
        club_name, school_year, budget, total_expenses = row
        remaining = budget - total_expenses
        print(f'Club {club_name} ({school_year}) budget: ${budget:.2f}, expenses: ${total_expenses:.2f}, remaining: ${remaining:.2f}')
    else:
        print('Club/year record not found.')


def report_total_budget(cursor):
    print('\nReport total budget for a year')
    school_year = input('Year: ').strip()
    query = 'SELECT IFNULL(SUM(budget_amount), 0) FROM club_year WHERE school_year = %s'
    total_budget = fetch_one(cursor, query, (school_year,))[0]
    print(f'Total budget across all clubs in {school_year}: ${total_budget:.2f}')


def assign_advisor(cursor):
    print('\nAssign faculty advisor for a club year')
    club_name = input('Club name: ').strip()
    school_year = input('Year: ').strip()
    faculty_name = input('Faculty advisor name: ').strip()
    faculty_id = select_faculty_id(cursor, faculty_name)
    if not faculty_id:
        print('Advisor not found.')
        return
    if not club_year_exists(cursor, club_name, school_year):
        print('Club/year record not found. Create the club/year record first by recording the budget.')
        return
    cursor.execute('UPDATE club_year SET faculty_id = %s WHERE club_name = %s AND school_year = %s', (faculty_id, club_name, school_year))
    print('Advisor assigned.')


def list_clubs_by_faculty(cursor):
    print('\nList clubs advised by faculty')
    faculty_name = input('Faculty name: ').strip()
    faculty_id = select_faculty_id(cursor, faculty_name)
    if not faculty_id:
        print('Faculty not found.')
        return
    query = '''SELECT cy.club_name, cy.school_year
               FROM club_year cy
               WHERE cy.faculty_id = %s
               ORDER BY cy.school_year, cy.club_name'''
    rows = fetch_all(cursor, query, (faculty_id,))
    if rows:
        for club_name, school_year in rows:
            print(f'- {club_name} ({school_year})')
    else:
        print('No club assignments found for that faculty member.')


def student_join_club(cursor):
    print('\nStudent joins a club')
    student_name = input('Student name: ').strip()
    club_name = input('Club name: ').strip()
    school_year = input('Year: ').strip()
    student_id = select_student_id(cursor, student_name)
    if not student_id:
        print('Student not found.')
        return
    if not club_year_exists(cursor, club_name, school_year):
        print('Club/year not found.')
        return
    try:
        cursor.execute(
            'INSERT INTO member (club_name, school_year, student_id) VALUES (%s, %s, %s)',
            (club_name, school_year, student_id),
        )
        print('Student added to club.')
    except Error as err:
        print('Failed to add membership:', err)


def student_leave_club(cursor):
    print('\nStudent leaves a club')
    student_name = input('Student name: ').strip()
    club_name = input('Club name: ').strip()
    school_year = input('Year: ').strip()
    student_id = select_student_id(cursor, student_name)
    if not student_id:
        print('Student not found.')
        return
    cursor.execute('DELETE FROM member WHERE student_id = %s AND club_name = %s AND school_year = %s', (student_id, club_name, school_year))
    if cursor.rowcount:
        print('Student removed from club membership.')
    else:
        print('Membership record not found.')


def list_members_of_club(cursor):
    print('\nList members of a club')
    club_name = input('Club name: ').strip()
    school_year = input('Year: ').strip()
    query = '''SELECT s.student_name, s.grade
               FROM member m
               JOIN student s ON m.student_id = s.student_id
               WHERE m.club_name = %s AND m.school_year = %s
               ORDER BY s.student_name'''
    rows = fetch_all(cursor, query, (club_name, school_year))
    if rows:
        for student_name, grade in rows:
            print(f'- {student_name}, grade {grade}')
    else:
        print('No members found for that club/year.')


def list_clubs_for_student(cursor):
    print('\nList clubs for a student')
    student_name = input('Student name: ').strip()
    student_id = select_student_id(cursor, student_name)
    if not student_id:
        print('Student not found.')
        return
    query = '''SELECT m.club_name, m.school_year
               FROM member m
               WHERE m.student_id = %s
               ORDER BY m.school_year, m.club_name'''
    rows = fetch_all(cursor, query, (student_id,))
    if rows:
        for club_name, school_year in rows:
            print(f'- {club_name} ({school_year})')
    else:
        print('No club memberships found for that student.')


def view_student_schedule(cursor):
    print('\nView student schedule for a date')
    student_name = input('Student name: ').strip()
    date_text = input('Date (YYYY-MM-DD): ').strip()
    try:
        schedule_date = datetime.strptime(date_text, '%Y-%m-%d').date()
    except ValueError:
        print('Invalid date format.')
        return
    student_id = select_student_id(cursor, student_name)
    if not student_id:
        print('Student not found.')
        return
    query = '''SELECT m.club_name, 'meeting' AS activity_type, mt.start_time, mt.end_time, mt.classroom, mt.description
               FROM member m
               JOIN meeting mt ON m.club_name = mt.club_name AND m.school_year = mt.school_year
               WHERE m.student_id = %s AND mt.meeting_date = %s
               UNION ALL
               SELECT m.club_name, 'event', e.start_time, e.end_time, NULL, e.description
               FROM member m
               JOIN `event` e ON m.club_name = e.club_name AND m.school_year = e.school_year
               WHERE m.student_id = %s AND e.event_date = %s
               ORDER BY start_time'''
    rows = fetch_all(cursor, query, (student_id, schedule_date, student_id, schedule_date))
    if rows:
        print(f'Activities for {student_name} on {schedule_date}:')
        for club_name, activity_type, start_time, end_time, classroom, description in rows:
            classroom_str = f' in {classroom}' if classroom else ''
            print(f'- {club_name}: {activity_type} {start_time}-{end_time}{classroom_str} - {description}')
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
