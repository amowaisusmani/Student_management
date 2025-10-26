import pymysql, os, sys
import config

SQL_FILE = os.path.join(os.path.dirname(__file__), 'db', 'init.sql')

def run_sql():
    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        sql = f.read()
    # split statements roughly by ';' - pymysql can execute multi statements if needed.
    try:
        conn = pymysql.connect(host=config.DB_HOST, user=config.DB_USER, password=config.DB_PASS, port=config.DB_PORT, cursorclass=pymysql.cursors.DictCursor, autocommit=True)
        with conn.cursor() as cur:
            for stmt in sql.split(';'):
                s = stmt.strip()
                if not s:
                    continue
                cur.execute(s)
        print('Database initialized (student_mgmt_db).')
    except Exception as e:
        print('Error initializing DB:', e)

if __name__ == '__main__':
    run_sql()
