import mysql.connector
import openai
from mysql.connector import OperationalError, InterfaceError

sql_host = "localhost"
sql_db = "boardify"
sql_user = "root"

sql_password = "root"  # local


# sql_password = "discount777"  # server


def connect():
    conn_f = mysql.connector.connect(host=sql_host, user=sql_user, password=sql_password, database=sql_db)
    return conn_f


def get_cursor():
    global conn
    try:
        return conn.cursor(buffered=True)
    except OperationalError:
        conn = connect()
    return conn.cursor(buffered=True)


def db_init():
    global conn
    conn1 = mysql.connector.connect(host=sql_host, user=sql_user, password=sql_password)
    cursor = conn1.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {sql_db}")
    conn1.commit()
    conn1.close()
    conn = connect()
    cursor = get_cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users("
                   "user_id BIGINT PRIMARY KEY,"
                   "company_id INT,"
                   "position_id INT,"
                   "date DATE DEFAULT (CURRENT_DATE),"
                   "position_learn_state SMALLINT DEFAULT 0,"
                   "users_learn_state SMALLINT DEFAULT 0,"
                   "products_learn_state SMALLINT DEFAULT 0,"
                   "company_learn_state SMALLINT DEFAULT 0"
                   ")")
    cursor.execute("CREATE TABLE IF NOT EXISTS admins("
                   "company_id INT,"
                   "user_id BIGINT PRIMARY KEY"
                   ")")
    cursor.execute("CREATE TABLE IF NOT EXISTS positions("
                   "position_id INT AUTO_INCREMENT,"
                   "company_id INT,"
                   "position TEXT,"
                   "PRIMARY KEY (position_id)"
                   ")")
    cursor.execute("CREATE TABLE IF NOT EXISTS companies("
                   "company_id INT AUTO_INCREMENT,"
                   "company TEXT,"
                   "PRIMARY KEY (company_id)"
                   ")")
    cursor.execute("CREATE TABLE IF NOT EXISTS learning("
                   "learning_id INT AUTO_INCREMENT,"
                   "company_id INT,"
                   "learn_type TEXT,"  # position, users, products company
                   "number SMALLINT,"
                   "info TEXT,"
                   "question TEXT,"
                   "answers TEXT,"
                   "correct_answer TEXT,"
                   "PRIMARY KEY (learning_id)"
                   ")")
    conn.commit()
    cursor.close()


def is_user_exists(user_id):
    global conn
    cursor = get_cursor()
    cursor.execute(f"SELECT company FROM users AS u INNER JOIN companies AS c ON u.company_id=c.company_id "
                   f"WHERE user_id=%s", (user_id,))
    is_exists = cursor.fetchone()
    cursor.close()
    if is_exists:
        return True
    return False


def get_admin_company(user_id):
    global conn
    cursor = get_cursor()
    cursor.execute(f"SELECT company_id FROM admins WHERE user_id=%s", (user_id,))
    is_exists = cursor.fetchone()
    cursor.close()
    if is_exists:
        return is_exists[0]
    return False


def get_position(user_id):
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"SELECT u.position_id, p.position FROM "
                       f"users AS u INNER JOIN positions AS p on p.position_id=u.position_id "
                       f"WHERE user_id=%s", (user_id,))
        position = cursor.fetchone()
        return position
    except Exception as e:
        print(e)
        return False


def get_learn_state(user_id, what_get):
    """
    :param user_id: user_id
    :param what_get: Какой параметр обучения берём position, company, products, users
    :return:
    """
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"SELECT {what_get}_learn_state FROM users WHERE user_id=%s", (user_id,))
        position = cursor.fetchone()
        return position
    except Exception as e:
        print(e)
        return False


def get_learn(company_id, what_get, number):
    """
    :param company_id:
    :param what_get: Какой параметр обучения берём position, company, products, users
    :param number: Номер получаемого вопроса
    :return:
    """
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"SELECT company_id, info, question, answer, correct_answer FROM users "
                       f"WHERE company_id=%s AND learn_type=%s AND number=%s", (company_id, what_get, number))
        position = cursor.fetchone()
        return position
    except Exception as e:
        print(e)
        return False


def get_position_by_id(position_id, company_id):
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"SELECT position FROM positions WHERE company_id=%s AND position_id=%s",
                       (company_id, position_id))
        position = cursor.fetchone()[0]
        return position
    except Exception as e:
        print(e)
        return False


def get_company_by_id(company_id):
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"SELECT company FROM companies WHERE company_id=%s", (company_id,))
        position = cursor.fetchone()[0]
        return position
    except Exception as e:
        print(e)
        return False


def get_company(user_id):
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"SELECT company_id FROM users WHERE user_id=%s", (user_id,))
        company_id = cursor.fetchone()[0]
        return company_id
    except Exception as e:
        print(e)
        return False


def get_all_users(user_id):
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"SELECT u.user_id FROM users AS u WHERE "
                       f"u.company_id IN (SELECT company_id FROM admins AS a WHERE a.user_id=%s)", (user_id,))
        all_users = cursor.fetchall()
        return all_users
    except Exception as e:
        print(e)
        return False


def new_admin(user_id):
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"INSERT INTO admins(user_id) VALUES(%s)", (user_id,))
        cursor.close()
        return True
    except Exception as e:
        print(e)
        return False


def new_user(user_id, company_id, position_id):
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"INSERT INTO users(user_id, company_id, position_id) "
                       f"VALUES(%s, %s, %s)", (user_id, company_id, position_id))
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(e)
        return False


def new_learn(company_id, learn_type, number, info, question, answer, correct_answer):
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"INSERT INTO learning(company_id, learn_type, number, info, question, answer, correct_answer),"
                       f" VALUES(%s, %s, %s, %s, %s, %s, %s)",
                       (company_id, learn_type, number, info, question, answer, correct_answer))
        cursor.close()
        return True
    except Exception as e:
        print(e)
        return False


def set_key(key):
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"UPDATE options SET openai_key={key}")
        conn.commit()
        return 1
    except:
        return 0


def del_learn(learning_id):
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(f"DELETE FROM learning WHERE learning_id=%s", (learning_id,))
        conn.commit()
        return True
    except:
        return False


def sql(request):
    global conn
    try:
        cursor = get_cursor()
        cursor.execute(request)
        try:
            if "select" in request.lower():
                response = cursor.fetchall()
            else:
                response = [["COMPLETE"]]
        except InterfaceError as e:
            response = [[e]]
        if not response:
            response = [["None"]]
        conn.commit()
        return response
    except Exception as e:
        return [[e]]


db_init()
conn = connect()
