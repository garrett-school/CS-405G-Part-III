DROP DATABASE IF EXISTS afterschool_clubs;
CREATE DATABASE afterschool_clubs CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE afterschool_clubs;

CREATE TABLE faculty (
    faculty_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    department VARCHAR(100)
);

CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    grade INT NOT NULL CHECK (grade BETWEEN 6 AND 8),
    email VARCHAR(100) UNIQUE
);

CREATE TABLE clubs (
    club_id INT AUTO_INCREMENT PRIMARY KEY,
    club_name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255)
);

CREATE TABLE club_year (
    club_year_id INT AUTO_INCREMENT PRIMARY KEY,
    club_id INT NOT NULL,
    year INT NOT NULL,
    advisor_id INT NOT NULL,
    budget DECIMAL(12,2) NOT NULL DEFAULT 0,
    CONSTRAINT uk_club_year UNIQUE (club_id, year),
    FOREIGN KEY (club_id) REFERENCES clubs(club_id) ON DELETE CASCADE,
    FOREIGN KEY (advisor_id) REFERENCES faculty(faculty_id) ON DELETE RESTRICT
);

CREATE TABLE club_membership (
    membership_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    club_year_id INT NOT NULL,
    joined_on DATE NOT NULL,
    CONSTRAINT uk_student_club_year UNIQUE (student_id, club_year_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (club_year_id) REFERENCES club_year(club_year_id) ON DELETE CASCADE
);

CREATE TABLE activity (
    activity_id INT AUTO_INCREMENT PRIMARY KEY,
    club_year_id INT NOT NULL,
    activity_type ENUM('meeting', 'event') NOT NULL,
    activity_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    description VARCHAR(255) NOT NULL,
    classroom VARCHAR(50) NOT NULL,
    CHECK (start_time < end_time),
    FOREIGN KEY (club_year_id) REFERENCES club_year(club_year_id) ON DELETE CASCADE
);

CREATE TABLE expenses (
    expense_id INT AUTO_INCREMENT PRIMARY KEY,
    club_year_id INT NOT NULL,
    expense_date DATE NOT NULL,
    amount DECIMAL(12,2) NOT NULL CHECK (amount >= 0),
    description VARCHAR(255),
    FOREIGN KEY (club_year_id) REFERENCES club_year(club_year_id) ON DELETE CASCADE
);

DELIMITER $$
CREATE TRIGGER trg_activity_before_insert
BEFORE INSERT ON activity
FOR EACH ROW
BEGIN
    DECLARE overlap_count INT DEFAULT 0;

    SELECT COUNT(*) INTO overlap_count
    FROM activity
    WHERE activity_date = NEW.activity_date
      AND classroom = NEW.classroom
      AND NEW.start_time < end_time
      AND NEW.end_time > start_time;

    IF overlap_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Classroom double-booking detected for the requested time slot.';
    END IF;

    SELECT COUNT(*) INTO overlap_count
    FROM activity
    WHERE activity_date = NEW.activity_date
      AND club_year_id = NEW.club_year_id
      AND NEW.start_time < end_time
      AND NEW.end_time > start_time;

    IF overlap_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Club cannot schedule overlapping activities on the same date.';
    END IF;
END$$

CREATE TRIGGER trg_activity_before_update
BEFORE UPDATE ON activity
FOR EACH ROW
BEGIN
    DECLARE overlap_count INT DEFAULT 0;

    SELECT COUNT(*) INTO overlap_count
    FROM activity
    WHERE activity_date = NEW.activity_date
      AND classroom = NEW.classroom
      AND NEW.start_time < end_time
      AND NEW.end_time > start_time
      AND activity_id <> OLD.activity_id;

    IF overlap_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Classroom double-booking detected for the requested time slot.';
    END IF;

    SELECT COUNT(*) INTO overlap_count
    FROM activity
    WHERE activity_date = NEW.activity_date
      AND club_year_id = NEW.club_year_id
      AND NEW.start_time < end_time
      AND NEW.end_time > start_time
      AND activity_id <> OLD.activity_id;

    IF overlap_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Club cannot schedule overlapping activities on the same date.';
    END IF;
END$$
DELIMITER ;

INSERT INTO faculty (first_name, last_name, email, department) VALUES
('Alice', 'Chen', 'alice.chen@middleschool.edu', 'Music'),
('Bob', 'Davis', 'bob.davis@middleschool.edu', 'STEM'),
('Carla', 'Evans', 'carla.evans@middleschool.edu', 'English'),
('Daniel', 'Ford', 'daniel.ford@middleschool.edu', 'Math');

INSERT INTO students (first_name, last_name, grade, email) VALUES
('Mia', 'Johnson', 6, 'mia.johnson@student.edu'),
('Noah', 'Kim', 7, 'noah.kim@student.edu'),
('Ava', 'Lopez', 6, 'ava.lopez@student.edu'),
('Ethan', 'Patel', 8, 'ethan.patel@student.edu'),
('Zoe', 'Smith', 7, 'zoe.smith@student.edu'),
('Lucas', 'Nguyen', 6, 'lucas.nguyen@student.edu'),
('Emma', 'Brown', 8, 'emma.brown@student.edu'),
('Owen', 'Garcia', 7, 'owen.garcia@student.edu');

INSERT INTO clubs (club_name, description) VALUES
('Band', 'After-school band practice and performances'),
('Orchestra', 'String orchestra rehearsal and events'),
('MathCounts', 'Mathematics competition preparation'),
('Robotics', 'Robotics build and programming club'),
('Drama', 'School drama club rehearsals and productions');

INSERT INTO club_year (club_id, year, advisor_id, budget) VALUES
((SELECT club_id FROM clubs WHERE club_name = 'Band'), 2024, 1, 8000.00),
((SELECT club_id FROM clubs WHERE club_name = 'Orchestra'), 2024, 1, 7500.00),
((SELECT club_id FROM clubs WHERE club_name = 'MathCounts'), 2024, 4, 5000.00),
((SELECT club_id FROM clubs WHERE club_name = 'Robotics'), 2024, 2, 9000.00),
((SELECT club_id FROM clubs WHERE club_name = 'Drama'), 2024, 3, 6000.00),
((SELECT club_id FROM clubs WHERE club_name = 'Band'), 2025, 1, 8200.00),
((SELECT club_id FROM clubs WHERE club_name = 'MathCounts'), 2025, 4, 5200.00);

INSERT INTO club_membership (student_id, club_year_id, joined_on) VALUES
((SELECT student_id FROM students WHERE first_name = 'Mia' AND last_name = 'Johnson'), (SELECT club_year_id FROM club_year WHERE year = 2024 AND club_id = (SELECT club_id FROM clubs WHERE club_name = 'Band')), '2024-09-05'),
((SELECT student_id FROM students WHERE first_name = 'Noah' AND last_name = 'Kim'), (SELECT club_year_id FROM club_year WHERE year = 2024 AND club_id = (SELECT club_id FROM clubs WHERE club_name = 'Band')), '2024-09-05'),
((SELECT student_id FROM students WHERE first_name = 'Ava' AND last_name = 'Lopez'), (SELECT club_year_id FROM club_year WHERE year = 2024 AND club_id = (SELECT club_id FROM clubs WHERE club_name = 'MathCounts')), '2024-09-06'),
((SELECT student_id FROM students WHERE first_name = 'Ethan' AND last_name = 'Patel'), (SELECT club_year_id FROM club_year WHERE year = 2024 AND club_id = (SELECT club_id FROM clubs WHERE club_name = 'Robotics')), '2024-09-07'),
((SELECT student_id FROM students WHERE first_name = 'Zoe' AND last_name = 'Smith'), (SELECT club_year_id FROM club_year WHERE year = 2024 AND club_id = (SELECT club_id FROM clubs WHERE club_name = 'Drama')), '2024-09-05'),
((SELECT student_id FROM students WHERE first_name = 'Lucas' AND last_name = 'Nguyen'), (SELECT club_year_id FROM club_year WHERE year = 2024 AND club_id = (SELECT club_id FROM clubs WHERE club_name = 'Orchestra')), '2024-09-08'),
((SELECT student_id FROM students WHERE first_name = 'Emma' AND last_name = 'Brown'), (SELECT club_year_id FROM club_year WHERE year = 2025 AND club_id = (SELECT club_id FROM clubs WHERE club_name = 'Band')), '2025-09-05');

INSERT INTO activity (club_year_id, activity_type, activity_date, start_time, end_time, description, classroom) VALUES
((SELECT club_year_id FROM club_year WHERE year = 2024 AND club_id = (SELECT club_id FROM clubs WHERE club_name = 'Band')), 'meeting', '2024-09-12', '16:00:00', '17:30:00', 'Fall rehearsal', 'Room 101'),
((SELECT club_year_id FROM club_year WHERE year = 2024 AND club_id = (SELECT club_id FROM clubs WHERE club_name = 'Band')), 'event', '2024-10-05', '15:30:00', '18:00:00', 'Community concert', 'Auditorium'),
((SELECT club_year_id FROM club_year WHERE year = 2024 AND club_id = (SELECT club_id FROM clubs WHERE club_name = 'MathCounts')), 'meeting', '2024-09-13', '15:30:00', '17:00:00', 'Problem solving practice', 'Room 202'),
((SELECT club_year_id FROM club_year WHERE year = 2024 AND club_id = (SELECT club_id FROM clubs WHERE club_name = 'Robotics')), 'meeting', '2024-09-14', '16:00:00', '18:00:00', 'Robot programming', 'Room 303'),
((SELECT club_year_id FROM club_year WHERE year = 2024 AND club_id = (SELECT club_id FROM clubs WHERE club_name = 'Drama')), 'event', '2024-10-20', '17:00:00', '19:00:00', 'Play audition', 'Auditorium');

INSERT INTO expenses (club_year_id, expense_date, amount, description) VALUES
((SELECT club_year_id FROM club_year WHERE year = 2024 AND club_id = (SELECT club_id FROM clubs WHERE club_name = 'Band')), '2024-09-20', 1250.00, 'Instrument rental'),
((SELECT club_year_id FROM club_year WHERE year = 2024 AND club_id = (SELECT club_id FROM clubs WHERE club_name = 'MathCounts')), '2024-09-25', 450.00, 'Competition registration'),
((SELECT club_year_id FROM club_year WHERE year = 2024 AND club_id = (SELECT club_id FROM clubs WHERE club_name = 'Robotics')), '2024-09-30', 1800.00, 'Hardware parts'),
((SELECT club_year_id FROM club_year WHERE year = 2024 AND club_id = (SELECT club_id FROM clubs WHERE club_name = 'Drama')), '2024-10-10', 900.00, 'Costume materials');
