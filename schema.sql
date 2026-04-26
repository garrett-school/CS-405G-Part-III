-- CS 405G Project Part III
--   run with: mysql -u root -p afterschool_club < schema.sql
--    or with: mysql -h mysql.cs.uky.edu -u YOUR_LINKBLUE -p YOUR_LINKBLUE < schema.sql

/*
 Drop tables if they already exist (disable then reenable foreign key checks to avoid circular reference problem)
*/
SET FOREIGN_KEY_CHECKS = 0;

DROP VIEW IF EXISTS club_financial_report;
DROP VIEW IF EXISTS club_schedule;

DROP TABLE IF EXISTS expense;
DROP TABLE IF EXISTS club_event;
DROP TABLE IF EXISTS meeting;
DROP TABLE IF EXISTS member;
DROP TABLE IF EXISTS budget;
DROP TABLE IF EXISTS advises;
DROP TABLE IF EXISTS student;
DROP TABLE IF EXISTS faculty;
DROP TABLE IF EXISTS club;

SET FOREIGN_KEY_CHECKS = 1;


/*
 Create tables
*/
CREATE TABLE club (
    club_name VARCHAR(100) NOT NULL,
    PRIMARY KEY (club_name)
);

CREATE TABLE faculty (
    faculty_id INT AUTO_INCREMENT,
    faculty_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    PRIMARY KEY (faculty_id),
    CONSTRAINT faculty_email_UQ UNIQUE (email)
);

CREATE TABLE student (
    student_id INT AUTO_INCREMENT,
    student_name VARCHAR(50) NOT NULL,
    student_grade INT NOT NULL,
    PRIMARY KEY (student_id),
    -- Student should be between 6th and 8th grade
    CONSTRAINT student_grade_CK CHECK (student_grade BETWEEN 6 AND 8)
);

CREATE TABLE advises (
    club_name VARCHAR(100) NOT NULL,
    school_year VARCHAR(9) NOT NULL,
    faculty_id INT NOT NULL,
    PRIMARY KEY (club_name, school_year),
    -- A faculty member advises a club. If a club is updated or deleted, cascade changes (i.e remove advisor)
    CONSTRAINT advises_clubName_FK
        FOREIGN KEY (club_name)
        REFERENCES club(club_name)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    -- If a faculty ID is updated, the advises relation should be between the club and updated ID
    CONSTRAINT advises_facultyId_FK
        FOREIGN KEY (faculty_id)
        REFERENCES faculty(faculty_id)
        ON UPDATE CASCADE
);


CREATE TABLE budget (
    club_name VARCHAR(100) NOT NULL,
    school_year VARCHAR(9) NOT NULL,
    budget_amount DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (club_name, school_year),
    -- Foreign key for budget (budget changes depending on club year)
    CONSTRAINT budget_advises_FK
        FOREIGN KEY (club_name, school_year)
        REFERENCES advises(club_name, school_year)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    -- Check that the budget is nonnegative
    CONSTRAINT budget_amount_CK CHECK (budget_amount >= 0)
);

CREATE TABLE member (
    student_id INT NOT NULL,
    club_name VARCHAR(100) NOT NULL,
    school_year VARCHAR(9) NOT NULL,
    PRIMARY KEY (student_id, club_name, school_year),

    -- Foreign keys for member of club to relate to student ID and current club year
    CONSTRAINT member_studentId_FK
        FOREIGN KEY (student_id)
        REFERENCES student(student_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT member_advises_FK
        FOREIGN KEY (club_name, school_year)
        REFERENCES advises(club_name, school_year)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE TABLE meeting (
    meeting_id INT AUTO_INCREMENT,
    meeting_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    details VARCHAR(250),
    classroom VARCHAR(25) NOT NULL,
    school_year VARCHAR(9) NOT NULL,
    club_name VARCHAR(100) NOT NULL,
    PRIMARY KEY (meeting_id),
    -- Club meeting foreign key to relate to current club year
    CONSTRAINT meeting_advises_FK
        FOREIGN KEY (club_name, school_year)
        REFERENCES advises(club_name, school_year)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    -- Logic check to ensure the start time of the meeting is before the ending time 
    CONSTRAINT meeting_time_CK CHECK (start_time < end_time)
);

CREATE TABLE club_event (
    event_id INT AUTO_INCREMENT,
    event_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    details VARCHAR(250),
    school_year VARCHAR(9) NOT NULL,
    club_name VARCHAR(100) NOT NULL,
    PRIMARY KEY (event_id),
    -- Foreign key to relate current club year to club event
    CONSTRAINT event_advises_FK
        FOREIGN KEY (club_name, school_year)
        REFERENCES advises(club_name, school_year)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    -- Ensure start happens before end
    CONSTRAINT event_time_CK CHECK (start_time < end_time)
);


CREATE TABLE expense (
    expense_id INT AUTO_INCREMENT,
    expense_date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    details VARCHAR(250),
    school_year VARCHAR(9) NOT NULL,
    club_name VARCHAR(100) NOT NULL,
    PRIMARY KEY (expense_id),
    -- Foreign key for expenses similar to budget
    CONSTRAINT expense_budget_FK
        FOREIGN KEY (club_name, school_year)
        REFERENCES budget(club_name, school_year)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT expense_amount_CK CHECK (amount >= 0)
);


-- Create a view for each club's budget, total expenses, and remaining budget each year
CREATE OR REPLACE VIEW club_financial_report AS
-- Select all club-year pairs with at least one expense
SELECT
    b.club_name,
    b.school_year,
    b.budget_amount,
    SUM(e.amount) AS total_expenses,
    b.budget_amount - SUM(e.amount) AS remaining_budget
FROM budget b, expense e
WHERE b.club_name = e.club_name
  AND b.school_year = e.school_year
GROUP BY b.club_name, b.school_year, b.budget_amount

UNION

-- Select all club-year pairs with no expenses
SELECT
    b.club_name,
    b.school_year,
    b.budget_amount,
    0 AS total_expenses,
    b.budget_amount AS remaining_budget
FROM budget b
WHERE NOT EXISTS (
    SELECT *
    FROM expense e
    WHERE e.club_name = b.club_name
      AND e.school_year = b.school_year
);

-- Create view for meetings and events combined for each club-year pair as a schedule
CREATE OR REPLACE VIEW club_schedule AS
SELECT
    -- Select all meetings
    meeting_id AS activity_id,
    'Meeting' AS activity_type,
    meeting_date AS activity_date,
    start_time,
    end_time,
    classroom,
    details,
    school_year,
    club_name
FROM meeting

UNION

SELECT
    -- Select all events
    event_id AS activity_id,
    'Event' AS activity_type,
    event_date AS activity_date,
    start_time,
    end_time,
    NULL AS classroom,
    details,
    school_year,
    club_name
FROM club_event;



DELIMITER //

-- Trigger to prevent overlapping of meetings on meeting creation
CREATE TRIGGER meeting_no_overlap_before_insert
BEFORE INSERT ON meeting
FOR EACH ROW
BEGIN
    DECLARE overlap_count INT DEFAULT 0;

    -- First, ensure that the classroom is not already booked
    SELECT COUNT(*) INTO overlap_count
    FROM meeting
    WHERE meeting_date = NEW.meeting_date
      AND classroom = NEW.classroom
      AND NEW.start_time < end_time
      AND NEW.end_time > start_time;

    IF overlap_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'This classroom is already booked for the requested meeting time.';
    END IF;

    -- Next, check that the club does not already have a meeting during the same time and date
    SELECT COUNT(*) INTO overlap_count
    FROM meeting
    WHERE meeting_date = NEW.meeting_date
      AND club_name = NEW.club_name
      AND school_year = NEW.school_year
      AND NEW.start_time < end_time
      AND NEW.end_time > start_time;

    IF overlap_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'A club may not schedule overlapping meetings on the same date.';
    END IF;

    -- Finally, check that the club's meeting does not overlap with one of their scheduled events
    SELECT COUNT(*) INTO overlap_count
    FROM club_event
    WHERE event_date = NEW.meeting_date
      AND club_name = NEW.club_name
      AND school_year = NEW.school_year
      AND NEW.start_time < end_time
      AND NEW.end_time > start_time;

    IF overlap_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'A club may not schedule a meeting that overlaps with one of their events on the same date.';
    END IF;
END//


-- Trigger to prevent an updated meeting time/date from causing overlap issue
CREATE TRIGGER meeting_no_overlap_before_update
BEFORE UPDATE ON meeting
FOR EACH ROW
BEGIN
    DECLARE overlap_count INT DEFAULT 0;

    -- First, ensure that the classroom is not already booked
    SELECT COUNT(*) INTO overlap_count
    FROM meeting
    WHERE meeting_id <> OLD.meeting_id
      AND meeting_date = NEW.meeting_date
      AND classroom = NEW.classroom
      AND NEW.start_time < end_time
      AND NEW.end_time > start_time;

    IF overlap_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'This classroom is already booked for the requested meeting time.';
    END IF;

    -- Next, check that the club does not already have a meeting during the same time and date
    SELECT COUNT(*) INTO overlap_count
    FROM meeting
    WHERE meeting_id <> OLD.meeting_id
      AND meeting_date = NEW.meeting_date
      AND club_name = NEW.club_name
      AND school_year = NEW.school_year
      AND NEW.start_time < end_time
      AND NEW.end_time > start_time;

    IF overlap_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'A club cannot schedule overlapping meetings on the same date.';
    END IF;

    -- Finally, check that the club's meeting does not overlap with one of their scheduled events
    SELECT COUNT(*) INTO overlap_count
    FROM club_event
    WHERE event_date = NEW.meeting_date
      AND club_name = NEW.club_name
      AND school_year = NEW.school_year
      AND NEW.start_time < end_time
      AND NEW.end_time > start_time;

    IF overlap_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'A club cannot schedule a meeting that overlaps with an event on the same date.';
    END IF;
END//


-- Trigger to prevent overlapping of events on event creation
CREATE TRIGGER event_no_overlap_before_insert
BEFORE INSERT ON club_event
FOR EACH ROW
BEGIN
    DECLARE overlap_count INT DEFAULT 0;

    -- First, check that the club does not already have an event during the same time and date
    SELECT COUNT(*) INTO overlap_count
    FROM club_event
    WHERE event_date = NEW.event_date
      AND club_name = NEW.club_name
      AND school_year = NEW.school_year
      AND NEW.start_time < end_time
      AND NEW.end_time > start_time;

    IF overlap_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'A club cannot schedule overlapping events on the same date.';
    END IF;

    -- Next, check that the club's event does not overlap with one of their scheduled meetings
    SELECT COUNT(*) INTO overlap_count
    FROM meeting
    WHERE meeting_date = NEW.event_date
      AND club_name = NEW.club_name
      AND school_year = NEW.school_year
      AND NEW.start_time < end_time
      AND NEW.end_time > start_time;

    IF overlap_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'A club cannot schedule an event that overlaps with a meeting on the same date.';
    END IF;
END//


-- Trigger to prevent an updated event time/date from causing overlap issue
CREATE TRIGGER event_no_overlap_before_update
BEFORE UPDATE ON club_event
FOR EACH ROW
BEGIN
    DECLARE overlap_count INT DEFAULT 0;

    -- First, check that the club does not already have an event during the same time and date
    SELECT COUNT(*) INTO overlap_count
    FROM club_event
    WHERE event_id <> OLD.event_id
      AND event_date = NEW.event_date
      AND club_name = NEW.club_name
      AND school_year = NEW.school_year
      AND NEW.start_time < end_time
      AND NEW.end_time > start_time;

    IF overlap_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'A club cannot schedule overlapping events on the same date.';
    END IF;

    -- Next, check that the club's event does not overlap with one of their scheduled meetings
    SELECT COUNT(*) INTO overlap_count
    FROM meeting
    WHERE meeting_date = NEW.event_date
      AND club_name = NEW.club_name
      AND school_year = NEW.school_year
      AND NEW.start_time < end_time
      AND NEW.end_time > start_time;

    IF overlap_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'A club cannot schedule an event that overlaps with a meeting on the same date.';
    END IF;
END//

DELIMITER ;


/*
 Insert sample data to test database
*/
INSERT INTO club (club_name) VALUES
('Band'),
('Drama'),
('Spanish'),
('Engineering'),
('Math');

INSERT INTO faculty (faculty_name, email, phone) VALUES
('Alice Chen', 'alice.chen@middleschool.edu', '8595551234'),
('Bob Davis', 'bob.davis@middleschool.edu', '8595555678'),
('Carla Evans', 'carla.evans@middleschool.edu', '8595559012'),
('Daniel Ford', 'daniel.ford@middleschool.edu', '8595553456');

INSERT INTO student (student_name, student_grade) VALUES
('Mia Johnson', 6),
('Noah Kim', 7),
('Ava Lopez', 6),
('Ethan Patel', 8),
('Zoe Smith', 7),
('Lucas Nguyen', 6),
('Emma Brown', 8),
('Owen Garcia', 7);

INSERT INTO advises (club_name, school_year, faculty_id) VALUES
('Band', '2024', 1),
('Drama', '2024', 3),
('Spanish', '2024', 4),
('Engineering', '2024', 2),
('Math', '2024', 4),
('Band', '2025', 1),
('Math', '2025', 2);

INSERT INTO budget (club_name, school_year, budget_amount) VALUES
('Band', '2024', 8000.00),
('Drama', '2024', 6000.00),
('Spanish', '2024', 4500.00),
('Engineering', '2024', 9000.00),
('Math', '2024', 5000.00),
('Band', '2025', 8200.00),
('Math', '2025', 5200.00);

INSERT INTO member (student_id, club_name, school_year) VALUES
(1, 'Band', '2024'),
(2, 'Math', '2024'),
(3, 'Engineering', '2024'),
(4, 'Drama', '2024'),
(5, 'Spanish', '2024'),
(6, 'Band', '2025'),
(7, 'Band', '2024'),
(8, 'Math', '2025');

INSERT INTO meeting (meeting_date, start_time, end_time, details, classroom, school_year, club_name) VALUES
('2024-09-12', '16:00:00', '17:30:00', 'Fall rehearsal', 'Room 101', '2024', 'Band'),
('2024-10-20', '17:00:00', '19:00:00', 'Play audition', 'Auditorium', '2024', 'Drama'),
('2024-09-16', '15:30:00', '16:30:00', 'Conversation practice', 'Room 204', '2024', 'Spanish'),
('2024-09-14', '16:00:00', '18:00:00', 'Robot design session', 'Room 303', '2024', 'Engineering'),
('2024-09-13', '15:30:00', '17:00:00', 'Problem solving practice', 'Room 202', '2024', 'Math');

INSERT INTO club_event (event_date, start_time, end_time, details, school_year, club_name) VALUES
('2024-10-15', '09:00:00', '13:30:00', 'Symphony field trip', '2024', 'Band'),
('2024-10-03', '09:00:00', '15:00:00', 'Museum trip', '2024', 'Drama'),
('2024-11-08', '10:00:00', '12:30:00', 'Cultural presentation', '2024', 'Spanish'),
('2025-02-28', '16:00:00', '18:00:00', 'Engineering showcase', '2024', 'Engineering'),
('2024-09-20', '13:45:00', '15:00:00', 'Fall competition', '2024', 'Math');

INSERT INTO expense (expense_date, amount, details, school_year, club_name) VALUES
('2024-09-20', 1250.00, 'Instrument rental', '2024', 'Band'),
('2024-10-10', 900.00, 'Costume materials', '2024', 'Drama'),
('2024-09-18', 300.00, 'Practice workbooks', '2024', 'Spanish'),
('2024-09-30', 1800.00, 'Hardware parts', '2024', 'Engineering'),
('2024-09-25', 450.00, 'Competition registration', '2024', 'Math');


-- 2 Optional trigger tests are provided below. They can be taken out of the comments and run to test the triggers

-- This statement should fail since Room 101 is already booked from 16:00 to 17:30 on 2024-09-12.
-- INSERT INTO meeting (meeting_date, start_time, end_time, details, classroom, school_year, club_name)
-- VALUES ('2024-09-12', '16:30:00', '17:00:00', 'Conflict test', 'Room 101', '2024', 'Math');

-- This should fail since Band already has a meeting from 16:00 to 17:30 on 2024-09-12.
-- INSERT INTO meeting (meeting_date, start_time, end_time, details, classroom, school_year, club_name)
-- VALUES ('2024-09-12', '16:30:00', '17:00:00', 'Conflict test', 'Room 999', '2024', 'Band');


