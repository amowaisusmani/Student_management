
# Student Management System (Tkinter + PyMySQL)

## Overview
A simple college project Student Management System using:
- Python 3.11.9
- MySQL 8.0.43
- PyMySQL
- Tkinter (built-in)

Features included:
- Students CRUD (fields: student_id, roll_no, first_name, last_name, gender, dob, phone, email, address_line)
- Courses CRUD
- Enrollments (M:N)
- Attendance (Present/Absent)
- Assessments (Half Term & Final Term) and Grades
- CSV exports (Students, Enrollments, Attendance, Grades)
- Simple tabbed UI using ttk.Notebook
- Parameterized queries only (protects against SQL injection)
- India phone validation (10 digits starting with 6-9)
- Pagination for students (25 rows/page)

## Setup (Windows 11)
1. Install Python 3.11.9 and MySQL 8.0.43.
2. Install required Python package:
   ```
   pip install -r requirements.txt
   ```
3. Update "config.py" if your MySQL credentials differ.
4. Initialize the database:
   - Option A: Use MySQL Workbench / CLI to run "db/init.sql".
   - Option B: Run the included script:
     ```
     python db_init.py
     ```
5. Run the app:
   ```
   python app.py
   ```

## Notes
- Admin account created by init.sql: username="admin", password="admin123".
- Passwords are stored plaintext in "admins" table.
- No foreign key constraints were added.

