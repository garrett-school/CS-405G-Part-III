DROP DATABASE IF EXISTS afterschool_club;
CREATE DATABASE afterschool_club CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE afterschool_club;

CREATE TABLE club (
    club_name VARCHAR(100) PRIMARY KEY
);

CREATE TABLE faculty (
    faculty_id INT AUTO_INCREMENT PRIMARY KEY,
    faculty_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15) NOT NULL
);

CREATE TABLE student (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    student_name VARCHAR(50) NOT NULL,
    grade INT NOT NULL CHECK (grade BETWEEN 6 AND 8)
);

CREATE TABLE meeting (
    meeting_id INT AUTO_INCREMENT PRIMARY KEY,
    club_name VARCHAR(100) NOT NULL,
    school_year CHAR(4) NOT NULL,
    meeting_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    `description` VARCHAR(250),
    classroom VARCHAR(25),
    CONSTRAINT meeting_clubName_FK FOREIGN KEY (club_name) REFERENCES club(club_name)
);

CREATE TABLE event (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    club_name VARCHAR(100) NOT NULL,
    school_year CHAR(4) NOT NULL,
    event_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    `description` VARCHAR(250),
    CONSTRAINT event_clubName_FK FOREIGN KEY (club_name) REFERENCES club(club_name)
);

CREATE TABLE expense (
    expense_id INT AUTO_INCREMENT PRIMARY KEY,
    club_name VARCHAR(100) NOT NULL,
    school_year CHAR(4) NOT NULL,
    expense_date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    `description` VARCHAR(250),
    CONSTRAINT expense_clubName_FK FOREIGN KEY (club_name) REFERENCES club(club_name),
    CONSTRAINT expense_nonnegative_CK CHECK (amount >= 0)
);

CREATE TABLE club_year (
    club_name VARCHAR(100) NOT NULL,
    school_year CHAR(4) NOT NULL,
    faculty_id INT NOT NULL,
    budget_amount DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (club_name, school_year),
    CONSTRAINT clubYear_clubName_FK FOREIGN KEY (club_name) REFERENCES club(club_name),
    CONSTRAINT clubYear_facultyId_FK FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id),
    CONSTRAINT clubYear_budgetAmount_CK CHECK (budget_amount >= 0)
);

CREATE TABLE member (
    club_name VARCHAR(100) NOT NULL,
    school_year CHAR(4) NOT NULL,
    student_id INT NOT NULL,
    PRIMARY KEY (club_name, school_year, student_id),
    CONSTRAINT member_clubYear_FK FOREIGN KEY (club_name, school_year) REFERENCES club_year(club_name, school_year),
    CONSTRAINT member_studentId_FK FOREIGN KEY (student_id) REFERENCES student(student_id)
);


DELIMITER $$
CREATE TRIGGER trg_activity_before_insert
BEFORE INSERT ON meeting
FOR EACH ROW
BEGIN
    DECLARE overlap_count INT DEFAULT 0;

    SELECT COUNT(*) INTO overlap_count
    FROM meeting
    WHERE meeting_date = NEW.meeting_date
      AND classroom = NEW.classroom
      AND NEW.start_time < end_time
      AND NEW.end_time > start_time;

    IF overlap_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Classroom double-booking detected for the requested time slot.';
    END IF;

    SELECT COUNT(*) INTO overlap_count
    FROM meeting
    WHERE meeting_date = NEW.meeting_date
      AND club_name = NEW.club_name
      AND NEW.start_time < end_time
      AND NEW.end_time > start_time;

    IF overlap_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Club cannot schedule overlapping activities on the same date.';
    END IF;
END$$

CREATE TRIGGER trg_activity_before_update
BEFORE UPDATE ON meeting
FOR EACH ROW
BEGIN
    DECLARE overlap_count INT DEFAULT 0;

    SELECT COUNT(*) INTO overlap_count
    FROM activity
    WHERE meeting_date = NEW.meeting_date
      AND classroom = NEW.classroom
      AND NEW.start_time < end_time
      AND NEW.end_time > start_time
      AND meeting_id <> OLD.meeting_id;

    IF overlap_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Classroom double-booking detected for the requested time slot.';
    END IF;

    SELECT COUNT(*) INTO overlap_count
    FROM activity
    WHERE meeting_date = NEW.meeting_date
      AND club_name = NEW.club_name
      AND NEW.start_time < end_time
      AND NEW.end_time > start_time
      AND meeting_id <> OLD.meeting_id;

    IF overlap_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Club cannot schedule overlapping activities on the same date.';
    END IF;
END$$

-- Create trigger to check remaining budget when creating expenses?

DELIMITER ;

INSERT INTO faculty (faculty_name, email, phone) VALUES
('Alice Chen', 'alice.chen@middleschool.edu', '8595551234'),
('Bob Davis', 'bob.davis@middleschool.edu', '8595555678'),
('Carla Evans', 'carla.evans@middleschool.edu', '8595559012'),
('Daniel Ford', 'daniel.ford@middleschool.edu', '8595553456');

INSERT INTO student (student_name, grade) VALUES
('Mia Johnson', 6),
('Noah Kim', 7),
('Ava Lopez', 6),
('Ethan Patel', 8),
('Zoe Smith', 7),
('Lucas Nguyen', 6),
('Emma Brown', 8),
('Owen Garcia', 7);

INSERT INTO club VALUES
('Band'),
('Orchestra'),
('MathCounts'),
('Robotics'),
('Drama');

INSERT INTO club_year VALUES
('Band', '2024', 1, 8000.00),
('Orchestra', '2024', 1, 7500.00),
('MathCounts', '2024', 4, 5000.00),
('Robotics', '2024', 2, 9000.00),
('Drama', '2024', 3, 6000.00),
('Band', '2025', 1, 8200.00),
('MathCounts', '2025', 2, 5200.00);

INSERT INTO member VALUES
('Band', '2024', 7),
('Band', '2024', 1),
('MathCounts', '2024', 2),
('Robotics', '2024', 3),
('Drama', '2024', 4),
('Orchestra', '2024', 5),
('Band', '2025', 6);

INSERT INTO meeting (club_name, school_year, meeting_date, start_time, end_time, `description`, classroom) VALUES
('Band', '2024', '2024-09-12', '16:00:00', '17:30:00', 'Fall rehearsal', 'Room 101'),
('Band', '2024', '2024-10-05', '15:30:00', '18:00:00', 'Community concert', 'Auditorium'),
('MathCounts', '2024', '2024-09-13', '15:30:00', '17:00:00', 'Problem solving practice', 'Room 202'),
('Robotics', '2024', '2024-09-14', '16:00:00', '18:00:00', 'Robot programming', 'Room 303'),
('Drama', '2024', '2024-10-20', '17:00:00', '19:00:00', 'Play audition', 'Auditorium');

INSERT INTO `event` (club_name, school_year, event_date, start_time, end_time, `description`) VALUES
('Band', '2024', '2024-10-15', '09:00:00', '13:30:00', 'Symphony field trip'),
('MathCounts', '2024', '2024-09-20', '13:45:00', '15:00:00', 'Fall competition'),
('MathCounts', '2024', '2025-03-14', '13:45:00', '15:00:00', 'Spring competition'),
('Robotics', '2024', '2025-02-28', '16:00:00', '18:00:00', 'League tournament'),
('Drama', '2024', '2024-10-03', '09:00:00', '15:00:00', 'Museum trip');

INSERT INTO expense (club_name, school_year, expense_date, amount, `description`) VALUES
('Band', '2024', '2024-09-20', 1250.00, 'Instrument rental'),
('MathCounts', '2024', '2024-09-25', 450.00, 'Competition registration'),
('Robotics', '2024', '2024-09-30', 1800.00, 'Hardware parts'),
('Drama', '2024', '2024-10-10', 900.00, 'Costume materials');
