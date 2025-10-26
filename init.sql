DROP DATABASE IF EXISTS student_mgmt;
CREATE DATABASE student_mgmt;
USE student_mgmt;

-- Students table
CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    roll_no VARCHAR(20) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    gender ENUM('Male','Female','Other') NOT NULL,
    dob DATE NOT NULL,
    phone CHAR(10) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    address_line VARCHAR(255) NOT NULL
);

-- Courses table
CREATE TABLE courses (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    course_name VARCHAR(100) NOT NULL UNIQUE
);

-- Enrollment table (M:N relation, no constraints beyond unique pair)
CREATE TABLE enrollments (
    enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    UNIQUE KEY unique_enroll (student_id, course_id)
);

-- Attendance table
CREATE TABLE attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    status ENUM('Present','Absent') NOT NULL,
    attendance_date DATE NOT NULL
);

-- Exams table (only 2 tests per year)
CREATE TABLE exams (
    exam_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    exam_type ENUM('Half Yearly','Final Term') NOT NULL,
    exam_date DATE NOT NULL
);

-- Results table
CREATE TABLE results (
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    exam_id INT NOT NULL,
    marks_obtained DECIMAL(5,2) NOT NULL,
    total_marks DECIMAL(5,2) NOT NULL
);
