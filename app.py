#!/usr/bin/env python3
"""
Student Management System (Tkinter + PyMySQL)

Requirements:
- Python 3.11.9
- PyMySQL
- MySQL 8.0.43
- Windows 11 (tested visually)

Files:
- config.py : DB credentials (edit if needed)
- db_init.py : helper to run init.sql to create DB & seed data
- app.py : this GUI application
"""

import os
import re
import csv
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pymysql
import config

DB = None

def get_db_connection(db=True):
    """Return a PyMySQL connection using config.py settings.
       If db=False, do not specify database (used for initial DB setup).
    """
    kwargs = {
        'host': config.DB_HOST,
        'user': config.DB_USER,
        'password': config.DB_PASS,
        'port': config.DB_PORT,
        'cursorclass': pymysql.cursors.DictCursor,
        'autocommit': True
    }
    if db:
        kwargs['db'] = config.DB_NAME
    return pymysql.connect(**kwargs)

# Validation helpers
def valid_phone(phone):
    # India specific: 10 digits, starts with 6-9
    return bool(re.fullmatch(r'^(?:\+91|91)?[6-9]\d{9}$', phone.strip()))

def valid_email(email):
     return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()))

# Database access functions (all parameterized)
def create_student(data):
    sql = """INSERT INTO students (roll_no, first_name, last_name, gender, dob, phone, email, address_line)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (
                data['roll_no'], data['first_name'], data.get('last_name'), data.get('gender','Male'),
                data.get('dob'), data.get('phone'), data.get('email'), data.get('address_line')
            ))
            return cur.lastrowid
    finally:
        conn.close()

def update_student(student_id, data):
    sql = """UPDATE students SET roll_no=%s, first_name=%s, last_name=%s, gender=%s, dob=%s,
             phone=%s, email=%s, address_line=%s WHERE student_id=%s"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (
                data['roll_no'], data['first_name'], data.get('last_name'), data.get('gender','Male'),
                data.get('dob'), data.get('phone'), data.get('email'), data.get('address_line'),
                student_id
            ))
            return cur.rowcount
    finally:
        conn.close()

def delete_student(student_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM students WHERE student_id=%s", (student_id,))
            return cur.rowcount
    finally:
        conn.close()

def search_students(q, page=1, page_size=25):
    offset = (page-1)*page_size
    qlike = f"%{q}%"
    sql = """SELECT * FROM students
             WHERE roll_no LIKE %s OR first_name LIKE %s OR last_name LIKE %s OR phone LIKE %s OR email LIKE %s
             ORDER BY created_at DESC
             LIMIT %s OFFSET %s"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (qlike, qlike, qlike, qlike, qlike, page_size, offset))
            results = cur.fetchall()
            # count
            cur.execute("SELECT COUNT(*) as cnt FROM students WHERE roll_no LIKE %s OR first_name LIKE %s OR last_name LIKE %s OR phone LIKE %s OR email LIKE %s", (qlike, qlike, qlike, qlike, qlike))
            total = cur.fetchone()['cnt']
            return results, total
    finally:
        conn.close()

# Courses
def create_course(data):
    sql = """INSERT INTO courses (code, name, credits, semester, department, description)
             VALUES (%s,%s,%s,%s,%s,%s)"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (
                data['code'], data['name'], data.get('credits',0), data.get('semester'), data.get('department'), data.get('description')
            ))
            return cur.lastrowid
    finally:
        conn.close()

def update_course(course_id, data):
    sql = """UPDATE courses SET code=%s, name=%s, credits=%s, semester=%s, department=%s, description=%s WHERE course_id=%s"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (
                data['code'], data['name'], data.get('credits',0), data.get('semester'), data.get('department'), data.get('description'), course_id
            ))
            return cur.rowcount
    finally:
        conn.close()

def delete_course(course_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM courses WHERE course_id=%s", (course_id,))
            return cur.rowcount
    finally:
        conn.close()

def list_courses():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM courses ORDER BY name")
            return cur.fetchall()
    finally:
        conn.close()

# Enrollments
def enroll_student(student_id, course_id):
    sql = "INSERT INTO enrollments (student_id, course_id) VALUES (%s,%s)"
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (student_id, course_id))
            return cur.lastrowid
    finally:
        conn.close()

def unenroll_student(student_id, course_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM enrollments WHERE student_id=%s AND course_id=%s", (student_id, course_id))
            return cur.rowcount
    finally:
        conn.close()

def list_enrollments_for_course(course_id):
    sql = "SELECT e.*, s.roll_no, s.first_name, s.last_name FROM enrollments e JOIN students s ON s.student_id=e.student_id WHERE e.course_id=%s"
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (course_id,))
            return cur.fetchall()
    finally:
        conn.close()

# Attendance
def mark_attendance(student_id, course_id, date_str, status, remarks=''):
    sql = """INSERT INTO attendance (student_id, course_id, `date`, status, remarks)
             VALUES (%s,%s,%s,%s,%s)
             ON DUPLICATE KEY UPDATE status=%s, remarks=%s"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (student_id, course_id, date_str, status, remarks, status, remarks))
            return cur.lastrowid
    finally:
        conn.close()

def get_attendance(course_id, date_from=None, date_to=None):
    sql = "SELECT a.*, s.roll_no, s.first_name, s.last_name FROM attendance a JOIN students s ON s.student_id=a.student_id WHERE a.course_id=%s"
    params = [course_id]
    if date_from:
        sql += " AND a.date >= %s"
        params.append(date_from)
    if date_to:
        sql += " AND a.date <= %s"
        params.append(date_to)
    sql += " ORDER BY a.date DESC"
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            return cur.fetchall()
    finally:
        conn.close()

# Assessments & Grades
def list_assessments(course_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM assessments WHERE course_id=%s ORDER BY name", (course_id,))
            return cur.fetchall()
    finally:
        conn.close()

def add_grade(student_id, course_id, assessment_id, score):
    sql = "INSERT INTO grades (student_id, course_id, assessment_id, score) VALUES (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE score=%s"
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (student_id, course_id, assessment_id, score, score))
            return cur.lastrowid
    finally:
        conn.close()

def get_grades(course_id):
    sql = "SELECT g.*, s.roll_no, s.first_name, s.last_name, a.name as assessment_name, a.max_score FROM grades g JOIN students s ON s.student_id=g.student_id JOIN assessments a ON a.assessment_id=g.assessment_id WHERE g.course_id=%s ORDER BY s.roll_no"
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (course_id,))
            return cur.fetchall()
    finally:
        conn.close()

# Reports: CSV export helpers
def export_csv(rows, headers, filepath):
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for r in rows:
            writer.writerow([r.get(h, '') for h in headers])

# GUI
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Student Management System')
        self.geometry('1000x650')
        self.configure(padx=10, pady=10)
        style = ttk.Style(self)
        style.theme_use('clam')
        # small style tweaks
        style.configure('TNotebook.Tab', padding=[12,8])
        style.configure('TButton', padding=6)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)
        self.students_tab = StudentsTab(self.notebook)
        self.courses_tab = CoursesTab(self.notebook)
        self.enroll_tab = EnrollTab(self.notebook)
        self.att_tab = AttendanceTab(self.notebook)
        self.grade_tab = GradesTab(self.notebook)
        self.report_tab = ReportsTab(self.notebook)
        self.settings_tab = SettingsTab(self.notebook)
        self.notebook.add(self.students_tab, text='Students')
        self.notebook.add(self.courses_tab, text='Courses')
        self.notebook.add(self.enroll_tab, text='Enrollments')
        self.notebook.add(self.att_tab, text='Attendance')
        self.notebook.add(self.grade_tab, text='Grades')
        self.notebook.add(self.report_tab, text='Reports')
        self.notebook.add(self.settings_tab, text='Settings')

class StudentsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        # Left: form, Right: list
        self.columnconfigure(1, weight=1)
        frm = ttk.Frame(self)
        frm.grid(row=0, column=0, sticky='ns')
        # Form fields
        self.vars = {k:tk.StringVar() for k in ('student_id','roll_no','first_name','last_name','gender','dob','phone','email','address_line')}
        lbls = ['Roll No','First Name','Last Name','Gender','DOB (YYYY-MM-DD)','Phone','Email','Address']
        for i, key in enumerate(('roll_no','first_name','last_name','gender','dob','phone','email','address_line')):
            ttk.Label(frm, text=lbls[i]).grid(row=i, column=0, sticky='w', pady=4)
            ent = ttk.Entry(frm, textvariable=self.vars[key], width=25)
            ent.grid(row=i, column=1, pady=4, padx=6)
        # Buttons
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=9, column=0, columnspan=2, pady=8)
        ttk.Button(btn_frame, text='Add', command=self.add_student).grid(row=0, column=0, padx=4)
        ttk.Button(btn_frame, text='Update', command=self.update_student).grid(row=0, column=1, padx=4)
        ttk.Button(btn_frame, text='Delete', command=self.delete_student).grid(row=0, column=2, padx=4)
        ttk.Button(btn_frame, text='Clear', command=self.clear_form).grid(row=0, column=3, padx=4)

        # Right side: search and treeview
        right = ttk.Frame(self)
        right.grid(row=0, column=1, sticky='nsew')
        right.columnconfigure(0, weight=1)
        search_frame = ttk.Frame(right)
        search_frame.pack(fill='x', pady=4)
        self.search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side='left', fill='x', expand=True, padx=4)
        ttk.Button(search_frame, text='Search', command=self.load_students).pack(side='left', padx=4)
        self.tree = ttk.Treeview(right, columns=('student_id','roll_no','first_name','last_name','gender','dob','phone','email','address_line'), show='headings', height=20)
        for c in self.tree['columns']:
            self.tree.heading(c, text=c.replace('_',' ').title())
            self.tree.column(c, width=100, anchor='center')
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        # pagination
        pg = ttk.Frame(right)
        pg.pack(fill='x')
        self.page = 1
        self.total = 0
        ttk.Button(pg, text='Prev', command=self.prev_page).pack(side='left')
        ttk.Button(pg, text='Next', command=self.next_page).pack(side='left')
        self.page_lbl = ttk.Label(pg, text='Page 1')
        self.page_lbl.pack(side='left', padx=10)
        # load initial
        self.load_students()

    def add_student(self):
        data = {k:self.vars[k].get().strip() for k in ('roll_no','first_name','last_name','gender','dob','phone','email','address_line')}
        if not data['roll_no'] or not data['first_name']:
            messagebox.showwarning('Validation','Roll No and First Name required')
            return
        if data['phone'] and not valid_phone(data['phone']):
            messagebox.showwarning('Validation','Phone must be 10 digits starting with 6-9')
            return
        if data['email'] and not valid_email(data['email']):
            messagebox.showwarning('Validation','Enter a valid email')
            return
        try:
            create_student(data)
            messagebox.showinfo('Success','Student added')
            self.clear_form()
            self.load_students()
        except pymysql.err.IntegrityError as e:
            messagebox.showerror('Error','Duplicate Roll No or database constraint')
        except Exception as e:
            messagebox.showerror('Error',str(e))

    def update_student(self):
        sid = self.vars['student_id'].get().strip()
        if not sid:
            messagebox.showwarning('Select','Select a student to update')
            return
        data = {k:self.vars[k].get().strip() for k in ('roll_no','first_name','last_name','gender','dob','phone','email','address_line')}
        if data['phone'] and not valid_phone(data['phone']):
            messagebox.showwarning('Validation','Phone must be 10 digits starting with 6-9')
            return
        if data['email'] and not valid_email(data['email']):
            messagebox.showwarning('Validation','Enter a valid email')
            return
        try:
            update_student(int(sid), data)
            messagebox.showinfo('Success','Student updated')
            self.clear_form()
            self.load_students()
        except pymysql.err.IntegrityError:
            messagebox.showerror('Error','Duplicate Roll No')
        except Exception as e:
            messagebox.showerror('Error',str(e))

    def delete_student(self):
        sid = self.vars['student_id'].get().strip()
        if not sid:
            messagebox.showwarning('Select','Select a student to delete')
            return
        if not messagebox.askyesno('Confirm','Delete this student?'):
            return
        try:
            delete_student(int(sid))
            messagebox.showinfo('Deleted','Student deleted')
            self.clear_form()
            self.load_students()
        except Exception as e:
            messagebox.showerror('Error',str(e))

    def clear_form(self):
        for k in self.vars:
            self.vars[k].set('')
        self.tree.selection_remove(self.tree.selection())

    def on_select(self, ev):
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel[0])['values']
        keys = ('student_id','roll_no','first_name','last_name','gender','dob','phone','email','address_line')
        for i,k in enumerate(keys):
            self.vars[k].set(item[i])

    def load_students(self):
        q = self.search_var.get().strip()
        rows, total = search_students(q, page=self.page, page_size=25)
        self.total = total
        for r in self.tree.get_children():
            self.tree.delete(r)
        for r in rows:
            self.tree.insert('', 'end', values=(r['student_id'], r['roll_no'], r['first_name'], r.get('last_name') or '',
                                                r.get('gender') or '', r.get('dob') and str(r['dob']) or '',
                                                r.get('phone') or '', r.get('email') or '', r.get('address_line') or ''))
        self.page_lbl.config(text=f'Page {self.page} ({self.total} total)')

    def prev_page(self):
        if self.page>1:
            self.page-=1
            self.load_students()

    def next_page(self):
        # simple check
        if self.page*25 < self.total:
            self.page+=1
            self.load_students()

class CoursesTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.columnconfigure(1, weight=1)
        frm = ttk.Frame(self)
        frm.grid(row=0, column=0, sticky='ns')
        self.vars = {k:tk.StringVar() for k in ('course_id','code','name','credits','semester','department','description')}
        labels = ['Code','Name','Credits','Semester','Department','Description']
        for i,key in enumerate(('code','name','credits','semester','department','description')):
            ttk.Label(frm, text=labels[i]).grid(row=i, column=0, sticky='w', pady=4)
            ent = ttk.Entry(frm, textvariable=self.vars[key], width=25)
            ent.grid(row=i, column=1, pady=4, padx=6)
        btnf = ttk.Frame(frm)
        btnf.grid(row=6, column=0, columnspan=2, pady=6)
        ttk.Button(btnf, text='Add', command=self.add_course).grid(row=0, column=0, padx=4)
        ttk.Button(btnf, text='Update', command=self.update_course).grid(row=0, column=1, padx=4)
        ttk.Button(btnf, text='Delete', command=self.delete_course).grid(row=0, column=2, padx=4)
        ttk.Button(btnf, text='Clear', command=self.clear_form).grid(row=0, column=3, padx=4)

        right = ttk.Frame(self)
        right.grid(row=0, column=1, sticky='nsew')
        right.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(right, columns=('course_id','code','name','credits','semester','department'), show='headings', height=20)
        for c in self.tree['columns']:
            self.tree.heading(c, text=c.replace('_',' ').title())
            self.tree.column(c, width=120, anchor='center')
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        self.load_courses()

    def add_course(self):
        data = {k:self.vars[k].get().strip() for k in ('code','name','credits','semester','department','description')}
        if not data['code'] or not data['name']:
            messagebox.showwarning('Validation','Code and Name required')
            return
        try:
            create_course(data)
            messagebox.showinfo('Success','Course added')
            self.clear_form()
            self.load_courses()
        except pymysql.err.IntegrityError:
            messagebox.showerror('Error','Duplicate course code')
        except Exception as e:
            messagebox.showerror('Error',str(e))

    def update_course(self):
        cid = self.vars['course_id'].get().strip()
        if not cid:
            messagebox.showwarning('Select','Select a course')
            return
        data = {k:self.vars[k].get().strip() for k in ('code','name','credits','semester','department','description')}
        try:
            update_course(int(cid), data)
            messagebox.showinfo('Success','Course updated')
            self.clear_form()
            self.load_courses()
        except pymysql.err.IntegrityError:
            messagebox.showerror('Error','Duplicate course code')
        except Exception as e:
            messagebox.showerror('Error',str(e))

    def delete_course(self):
        cid = self.vars['course_id'].get().strip()
        if not cid:
            messagebox.showwarning('Select','Select a course')
            return
        if not messagebox.askyesno('Confirm','Delete this course?'):
            return
        try:
            delete_course(int(cid))
            messagebox.showinfo('Deleted','Course deleted')
            self.clear_form()
            self.load_courses()
        except Exception as e:
            messagebox.showerror('Error',str(e))

    def clear_form(self):
        for k in self.vars:
            self.vars[k].set('')
        self.tree.selection_remove(self.tree.selection())

    def on_select(self, ev):
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel[0])['values']
        keys = ('course_id','code','name','credits','semester','department')
        for i,k in enumerate(keys):
            self.vars[k].set(item[i])

    def load_courses(self):
        rows = list_courses()
        for r in self.tree.get_children():
            self.tree.delete(r)
        for r in rows:
            self.tree.insert('', 'end', values=(r['course_id'], r['code'], r['name'], r.get('credits') or 0, r.get('semester') or '', r.get('department') or ''))

class EnrollTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        left = ttk.Frame(self)
        left.grid(row=0, column=0, sticky='ns')
        ttk.Label(left, text='Select Course').grid(row=0, column=0, pady=4)
        self.course_var = tk.StringVar()
        self.course_cb = ttk.Combobox(left, textvariable=self.course_var, state='readonly')
        self.course_cb.grid(row=0, column=1, pady=4)
        ttk.Button(left, text='Load Students', command=self.load_students).grid(row=0, column=2, padx=6)
        self.student_var = tk.StringVar()
        ttk.Label(left, text='Select Student').grid(row=1, column=0, pady=4)
        self.student_cb = ttk.Combobox(left, textvariable=self.student_var)
        self.student_cb.grid(row=1, column=1, pady=4)
        ttk.Button(left, text='Enroll', command=self.enroll).grid(row=2, column=0, pady=6)
        ttk.Button(left, text='Unenroll', command=self.unenroll).grid(row=2, column=1, pady=6)

        right = ttk.Frame(self)
        right.grid(row=0, column=1, sticky='nsew')
        right.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(right, columns=('id','student_id','roll_no','name','enrolled_on'), show='headings', height=20)
        for c in self.tree['columns']:
            self.tree.heading(c, text=c.replace('_',' ').title())
            self.tree.column(c, width=120, anchor='center')
        self.tree.pack(fill='both', expand=True)
        self.load_course_options()

    def load_course_options(self):
        courses = list_courses()
        self.course_map = {f"{c['code']} - {c['name']}": c['course_id'] for c in courses}
        self.course_cb['values'] = list(self.course_map.keys())
        # students for combobox
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT student_id, roll_no, first_name, last_name FROM students ORDER BY roll_no")
                rows = cur.fetchall()
                self.student_map = {f"{r['roll_no']} - {r['first_name']} {r.get('last_name') or ''}": r['student_id'] for r in rows}
                self.student_cb['values'] = list(self.student_map.keys())
        finally:
            conn.close()

    def load_students(self):
        key = self.course_var.get()
        if not key:
            messagebox.showwarning('Select','Select a course first')
            return
        course_id = self.course_map[key]
        rows = list_enrollments_for_course(course_id)
        for r in self.tree.get_children():
            self.tree.delete(r)
        for r in rows:
            self.tree.insert('', 'end', values=(r['id'], r['student_id'], r['roll_no'], f"{r['first_name']} {r.get('last_name') or ''}", str(r.get('enrolled_on'))))

    def enroll(self):
        skey = self.student_var.get()
        ckey = self.course_var.get()
        if not skey or not ckey:
            messagebox.showwarning('Select','Select both student and course')
            return
        student_id = self.student_map[skey]
        course_id = self.course_map[ckey]
        try:
            enroll_student(student_id, course_id)
            messagebox.showinfo('Enrolled','Student enrolled')
            self.load_students()
        except pymysql.err.IntegrityError:
            messagebox.showerror('Error','Already enrolled')
        except Exception as e:
            messagebox.showerror('Error',str(e))

    def unenroll(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Select','Select enrollment to remove')
            return
        item = self.tree.item(sel[0])['values']
        student_id = item[1]
        course_id = self.course_map[self.course_var.get()]
        if not messagebox.askyesno('Confirm','Unenroll student?'):
            return
        try:
            unenroll_student(student_id, course_id)
            messagebox.showinfo('Removed','Enrollment removed')
            self.load_students()
        except Exception as e:
            messagebox.showerror('Error',str(e))

class AttendanceTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        left = ttk.Frame(self)
        left.grid(row=0, column=0, sticky='ns')
        ttk.Label(left, text='Select Course').grid(row=0, column=0, pady=4)
        self.course_var = tk.StringVar()
        self.course_cb = ttk.Combobox(left, textvariable=self.course_var, state='readonly')
        self.course_cb.grid(row=0, column=1, pady=4)
        ttk.Label(left, text='Date (YYYY-MM-DD)').grid(row=1, column=0, pady=4)
        self.date_var = tk.StringVar(value=str(datetime.date.today()))
        ttk.Entry(left, textvariable=self.date_var).grid(row=1, column=1, pady=4)
        ttk.Button(left, text='Load Enrolled Students', command=self.load_enrolled).grid(row=2, column=0, columnspan=2, pady=6)
        ttk.Button(left, text='Mark All Present', command=self.mark_all_present).grid(row=3, column=0, columnspan=2, pady=6)

        right = ttk.Frame(self)
        right.grid(row=0, column=1, sticky='nsew')
        right.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(right, columns=('student_id','roll_no','name','status'), show='headings', height=20)
        for c in self.tree['columns']:
            self.tree.heading(c, text=c.replace('_',' ').title())
            self.tree.column(c, width=150, anchor='center')
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<Double-1>', self.toggle_status)
        self.load_course_options()

    def load_course_options(self):
        courses = list_courses()
        self.course_map = {f"{c['code']} - {c['name']}": c['course_id'] for c in courses}
        self.course_cb['values'] = list(self.course_map.keys())

    def load_enrolled(self):
        key = self.course_var.get()
        if not key:
            messagebox.showwarning('Select','Select a course first')
            return
        course_id = self.course_map[key]
        rows = list_enrollments_for_course(course_id)
        for r in self.tree.get_children():
            self.tree.delete(r)
        for r in rows:
            # Try to fetch existing attendance for date
            date_str = self.date_var.get().strip()
            status = ''
            conn = get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT status FROM attendance WHERE student_id=%s AND course_id=%s AND date=%s", (r['student_id'], course_id, date_str))
                    rec = cur.fetchone()
                    if rec:
                        status = rec['status']
            finally:
                conn.close()
            self.tree.insert('', 'end', values=(r['student_id'], r['roll_no'], f"{r['first_name']} {r.get('last_name') or ''}", status or 'Absent'))

    def toggle_status(self, ev):
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel[0])['values']
        student_id = item[0]
        course_id = self.course_map[self.course_var.get()]
        date_str = self.date_var.get().strip()
        current = item[3]
        new = 'Present' if current!='Present' else 'Absent'
        try:
            mark_attendance(student_id, course_id, date_str, new)
            self.load_enrolled()
        except Exception as e:
            messagebox.showerror('Error',str(e))

    def mark_all_present(self):
        key = self.course_var.get()
        if not key:
            messagebox.showwarning('Select','Select course first')
            return
        course_id = self.course_map[key]
        date_str = self.date_var.get().strip()
        rows = list_enrollments_for_course(course_id)
        try:
            for r in rows:
                mark_attendance(r['student_id'], course_id, date_str, 'Present')
            messagebox.showinfo('Done','Marked all present')
            self.load_enrolled()
        except Exception as e:
            messagebox.showerror('Error',str(e))

class GradesTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        left = ttk.Frame(self)
        left.grid(row=0, column=0, sticky='ns')
        ttk.Label(left, text='Select Course').grid(row=0, column=0, pady=4)
        self.course_var = tk.StringVar()
        self.course_cb = ttk.Combobox(left, textvariable=self.course_var, state='readonly')
        self.course_cb.grid(row=0, column=1, pady=4)
        ttk.Button(left, text='Load Assessments', command=self.load_assessments).grid(row=1, column=0, columnspan=2, pady=4)
        ttk.Label(left, text='Select Assessment').grid(row=2, column=0, pady=4)
        self.assess_var = tk.StringVar()
        self.assess_cb = ttk.Combobox(left, textvariable=self.assess_var, state='readonly')
        self.assess_cb.grid(row=2, column=1, pady=4)
        ttk.Button(left, text='Load Students', command=self.load_students).grid(row=3, column=0, columnspan=2, pady=6)
        ttk.Label(left, text='Score').grid(row=4, column=0, pady=4)
        self.score_var = tk.StringVar()
        ttk.Entry(left, textvariable=self.score_var).grid(row=4, column=1, pady=4)
        ttk.Button(left, text='Add/Update Grade', command=self.add_grade).grid(row=5, column=0, columnspan=2, pady=6)

        right = ttk.Frame(self)
        right.grid(row=0, column=1, sticky='nsew')
        right.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(right, columns=('student_id','roll_no','name','score','max_score','assessment'), show='headings', height=20)
        for c in self.tree['columns']:
            self.tree.heading(c, text=c.replace('_',' ').title())
            self.tree.column(c, width=120, anchor='center')
        self.tree.pack(fill='both', expand=True)
        self.load_course_options()

    def load_course_options(self):
        courses = list_courses()
        self.course_map = {f"{c['code']} - {c['name']}": c['course_id'] for c in courses}
        self.course_cb['values'] = list(self.course_map.keys())

    def load_assessments(self):
        key = self.course_var.get()
        if not key:
            messagebox.showwarning('Select','Select course')
            return
        course_id = self.course_map[key]
        assessments = list_assessments(course_id)
        self.assess_map = {f"{a['name']} (Max {a['max_score']})": a['assessment_id'] for a in assessments}
        self.assess_cb['values'] = list(self.assess_map.keys())

    def load_students(self):
        key = self.course_var.get()
        if not key:
            messagebox.showwarning('Select','Select course')
            return
        course_id = self.course_map[key]
        rows = get_grades(course_id)
        for r in self.tree.get_children():
            self.tree.delete(r)
        for r in rows:
            self.tree.insert('', 'end', values=(r['student_id'], r['roll_no'], f"{r['first_name']} {r.get('last_name') or ''}", float(r['score']), r.get('max_score'), r.get('assessment_name')))

    def add_grade(self):
        akey = self.assess_var.get()
        skey = None
        sel = self.tree.selection()
        if sel:
            item = self.tree.item(sel[0])['values']
            skey = item[0]
        if not akey or not skey:
            messagebox.showwarning('Select','Select assessment and a student row first')
            return
        try:
            score = float(self.score_var.get())
        except:
            messagebox.showwarning('Validation','Enter numeric score')
            return
        assessment_id = self.assess_map[akey]
        course_id = self.course_map[self.course_var.get()]
        try:
            add_grade(skey, course_id, assessment_id, score)
            messagebox.showinfo('Saved','Grade saved')
            self.load_students()
        except Exception as e:
            messagebox.showerror('Error',str(e))

class ReportsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        ttk.Button(self, text='Export Students CSV', command=self.export_students).pack(pady=6)
        ttk.Button(self, text='Export Enrollments CSV', command=self.export_enrollments).pack(pady=6)
        ttk.Button(self, text='Export Attendance CSV', command=self.export_attendance).pack(pady=6)
        ttk.Button(self, text='Export Grades CSV', command=self.export_grades).pack(pady=6)

    def export_students(self):
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT roll_no, first_name, last_name, gender, dob, phone, email, address_line FROM students ORDER BY roll_no")
                rows = cur.fetchall()
        finally:
            conn.close()
        if not rows:
            messagebox.showinfo('No Data','No students to export')
            return
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv')])
        if not path: return
        export_csv(rows, ['roll_no','first_name','last_name','gender','dob','phone','email','address_line'], path)
        messagebox.showinfo('Saved', f'Exported to {path}')

    def export_enrollments(self):
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT c.code as course_code, c.name as course_name, s.roll_no, s.first_name, s.last_name FROM enrollments e JOIN students s ON s.student_id=e.student_id JOIN courses c ON c.course_id=e.course_id ORDER BY c.code")
                rows = cur.fetchall()
        finally:
            conn.close()
        if not rows:
            messagebox.showinfo('No Data','No enrollments to export')
            return
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv')])
        if not path: return
        export_csv(rows, ['course_code','course_name','roll_no','first_name','last_name'], path)
        messagebox.showinfo('Saved', f'Exported to {path}')

    def export_attendance(self):
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT c.code as course_code, a.date, s.roll_no, s.first_name, s.last_name, a.status FROM attendance a JOIN students s ON s.student_id=a.student_id JOIN courses c ON c.course_id=a.course_id ORDER BY a.date DESC")
                rows = cur.fetchall()
        finally:
            conn.close()
        if not rows:
            messagebox.showinfo('No Data','No attendance to export')
            return
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv')])
        if not path: return
        export_csv(rows, ['course_code','date','roll_no','first_name','last_name','status'], path)
        messagebox.showinfo('Saved', f'Exported to {path}')

    def export_grades(self):
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT c.code as course_code, a.name as assessment, s.roll_no, s.first_name, s.last_name, g.score FROM grades g JOIN students s ON s.student_id=g.student_id JOIN assessments a ON a.assessment_id=g.assessment_id JOIN courses c ON c.course_id=g.course_id ORDER BY c.code")
                rows = cur.fetchall()
        finally:
            conn.close()
        if not rows:
            messagebox.showinfo('No Data','No grades to export')
            return
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv')])
        if not path: return
        export_csv(rows, ['course_code','assessment','roll_no','first_name','last_name','score'], path)
        messagebox.showinfo('Saved', f'Exported to {path}')

class SettingsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        ttk.Label(self, text='Database & App Settings').pack(pady=8)
        ttk.Label(self, text=f"DB Host: {config.DB_HOST}").pack()
        ttk.Label(self, text=f"DB Port: {config.DB_PORT}").pack()
        ttk.Label(self, text=f"DB Name: {config.DB_NAME}").pack()
        ttk.Label(self, text=f"DB User: {config.DB_USER}").pack()
        ttk.Label(self, text='To (re)initialize DB run db_init.py from command line').pack(pady=6)

def main():
    # basic DB connectivity check
    try:
        conn = get_db_connection()
        conn.close()
    except Exception as e:
        messagebox.showerror('DB Error', f'Unable to connect to database. Run db_init.py or check config.py.\\nError: {e}')
        return
    app = App()
    app.mainloop()

if __name__ == '__main__':
    main()
