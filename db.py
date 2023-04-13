import traceback

import mysql.connector
import openai
from mysql.connector import OperationalError, InterfaceError

sql_host = "localhost"
sql_db = "boardify"
sql_user = "root"

sql_password = "root"  # local


def connect():
    conn_f = mysql.connector.connect(host=sql_host, user=sql_user, password=sql_password, database=sql_db)
    conn_f.autocommit = True
    return conn_f


def get_cursor():
    conn1 = mysql.connector.connect(host=sql_host, user=sql_user, password=sql_password, database=sql_db)
    conn1.autocommit = True
    try:
        return conn1, conn1.cursor(buffered=True)
    except OperationalError:
        conn1 = connect()
    return conn1, conn1.cursor(buffered=True)


def db_init():
    conn1 = mysql.connector.connect(host=sql_host, user=sql_user, password=sql_password)
    cursor = conn1.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {sql_db}")
    conn1.commit()
    conn1.close()
    conn, cursor = get_cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users("
                   "user_id BIGINT PRIMARY KEY,"
                   "username TEXT,"
                   "company_id INT,"
                   "position_id INT,"
                   "date DATE DEFAULT (CURRENT_DATE),"
                   "position_learn_state SMALLINT DEFAULT -1,"
                   "users_learn_state SMALLINT DEFAULT -1,"
                   "products_learn_state SMALLINT DEFAULT -1,"
                   "company_learn_state SMALLINT DEFAULT -1"
                   ")")
    cursor.execute("CREATE TABLE IF NOT EXISTS admins("
                   "company_id INT,"
                   "email TEXT,"
                   "password TEXT,"
                   "sha TEXT"
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
                   "position_id INT,"
                   "learn_type TEXT,"  # position, users, products company
                   "number SMALLINT,"
                   "info TEXT,"
                   "PRIMARY KEY (learning_id)"
                   ")")
    cursor.execute("CREATE TABLE IF NOT EXISTS questions("
                   "question_id INT AUTO_INCREMENT,"
                   "learning_id INT,"
                   "question TEXT,"
                   "PRIMARY KEY (question_id)"
                   ")")
    cursor.execute("CREATE TABLE IF NOT EXISTS answers("
                   "answer_id INT AUTO_INCREMENT,"
                   "question_id INT,"
                   "answer TEXT,"
                   "is_correct BOOLEAN DEFAULT FALSE,"
                   "PRIMARY KEY (answer_id)"
                   ")")

    cursor.execute("CREATE TABLE IF NOT EXISTS messages("
                   "message_id INT AUTO_INCREMENT,"
                   "user_id BIGINT,"
                   "company_id INT,"
                   "sender BOOLEAN,"  # 1 admin
                   "message TEXT,"
                   "is_read BOOLEAN DEFAULT FALSE,"
                   "date DATE DEFAULT (CURRENT_DATE),"
                   "PRIMARY KEY (message_id)"
                   ")")
    cursor.execute("CREATE TABLE IF NOT EXISTS files("
                   "file_id INT AUTO_INCREMENT,"
                   "company_id INT,"
                   "filename TEXT,"
                   "PRIMARY KEY (file_id)"
                   ")")
    cursor.execute("CREATE TABLE IF NOT EXISTS learning_files("
                   "file_id INT,"
                   "learning_id INT"
                   ")")
    conn.commit()
    conn.close()


def is_user_exists(user_id):
    conn, cursor = get_cursor()
    cursor.execute(f"SELECT company FROM users AS u INNER JOIN companies AS c ON u.company_id=c.company_id "
                   f"WHERE user_id=%s", (user_id,))
    is_exists = cursor.fetchone()
    conn.close()
    if is_exists:
        return True
    return False


def is_correct(answer_id):
    conn, cursor = get_cursor()
    cursor.execute(f"SELECT is_correct FROM answers WHERE answer_id=%s", (answer_id,))
    correct = cursor.fetchone()
    conn.close()
    if correct:
        return correct[0]
    return False


def is_admin(sha):
    conn, cursor = get_cursor()
    cursor.execute(f"SELECT 1 FROM admins WHERE sha=%s", (sha,))
    sha = cursor.fetchone()
    conn.close()
    if sha:
        return True
    return False


def is_admin_exists(email):
    conn, cursor = get_cursor()
    cursor.execute(f"SELECT 1 FROM admins WHERE email=%s", (email,))
    email = cursor.fetchone()
    conn.close()
    if email:
        return True
    return False


def is_position_exist(company_id, position):
    conn, cursor = get_cursor()
    cursor.execute(f"SELECT 1 FROM positions WHERE company_id=%s AND position=%s", (company_id, position))
    email = cursor.fetchone()
    conn.close()
    if email:
        return True
    return False


def get_admin(email, password):
    conn, cursor = get_cursor()
    cursor.execute(f"SELECT sha FROM admins WHERE email=%s AND password=%s", (email, password))
    sha = cursor.fetchone()
    conn.close()
    if sha:
        return sha[0]
    return False


def get_admin_company(sha):
    conn, cursor = get_cursor()
    cursor.execute(f"SELECT company_id FROM admins WHERE sha=%s", (sha,))
    is_exists = cursor.fetchone()
    conn.close()
    if is_exists:
        return is_exists[0]
    return False


def get_user_position(user_id):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"SELECT u.position_id, p.position FROM "
                       f"users AS u INNER JOIN positions AS p on p.position_id=u.position_id "
                       f"WHERE user_id=%s", (user_id,))
        position = cursor.fetchone()
        conn.close()
        return position
    except Exception as e:
        print(traceback.format_exc())
        return False


def get_learn_state(user_id, what_get):
    """
    :param user_id: user_id
    :param what_get: Какой параметр обучения берём position, company, products, users
    :return:
    """

    try:
        conn, cursor = get_cursor()
        cursor.execute(f"SELECT {what_get}_learn_state FROM users WHERE user_id=%s", (user_id,))
        position = cursor.fetchone()[0]
        conn.close()
        return position
    except Exception as e:
        print(traceback.format_exc())
        return False


def get_learn(learning_id):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"SELECT info FROM learning WHERE learning_id=%s", (learning_id,))
        position = cursor.fetchone()
        conn.close()
        if position:
            return position[0]
        return False
    except Exception as e:
        print(traceback.format_exc())
        return False


def get_last_state(company_id, position_id, what_get):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"SELECT learning_id FROM learning "
                       f"WHERE company_id=%s AND learn_type=%s AND (position_id=%s OR position_id=-1) "
                       f"ORDER BY -position_id, number DESC LIMIT 1",
                       (company_id, what_get, position_id))
        position = cursor.fetchone()
        conn.close()
        if position:
            return position[0]
        return False
    except Exception as e:
        print(traceback.format_exc())
        return False


def get_questions(learning_id, answered_questions):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"SELECT question_id, question FROM questions "
                       f"WHERE learning_id=%s AND "
                       f"question_id NOT IN ({', '.join([str(i) for i in answered_questions])})", (learning_id,))
        questions = cursor.fetchall()
        conn.close()
        return questions
    except Exception as e:
        print(traceback.format_exc())
        return False


def get_question_by_answer(answer_id):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"SELECT question_id FROM answers WHERE answer_id=%s", (answer_id,))
        question = cursor.fetchone()
        conn.close()
        if question:
            return question[0]
        return False
    except Exception as e:
        print(traceback.format_exc())
        return False


def get_messages(user_id):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"SELECT u.user_id, username, message, is_read, sender "
                       f"FROM messages AS m JOIN users AS u ON m.user_id=u.user_id "
                       f"WHERE u.user_id=%s OR u.user_id=-1 ORDER BY m.date", (user_id,))

        messages = cursor.fetchall()
        conn.close()
        return messages
    except Exception as e:
        print(traceback.format_exc())
        return False


def get_answers(question_id):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"SELECT answer_id, answer, is_correct FROM answers WHERE question_id=%s", (question_id,))
        position = cursor.fetchall()
        conn.close()
        return position
    except Exception as e:
        print(traceback.format_exc())
        return False


def get_all_positions(company_id):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"SELECT position_id, position FROM positions WHERE company_id=%s", (company_id,))
        position = cursor.fetchall()
        conn.close()
        return position
    except Exception as e:
        print(traceback.format_exc())
        return False


def get_learn_id_by_answer(answer_id):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"SELECT learning_id FROM answers AS a JOIN questions AS q ON a.question_id=q.question_id "
                       f"WHERE answer_id=%s", (answer_id,))
        learning_id = cursor.fetchone()
        conn.close()
        if learning_id:
            return learning_id[0]
        return 0
    except Exception as e:
        print(traceback.format_exc())
        return False


def get_position_by_id(position_id, company_id):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"SELECT position FROM positions WHERE company_id=%s AND position_id=%s",
                       (company_id, position_id))
        position = cursor.fetchone()[0]
        conn.close()
        return position
    except Exception as e:
        print(traceback.format_exc())
        return False


def get_company_by_id(company_id):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"SELECT company FROM companies WHERE company_id=%s", (company_id,))
        position = cursor.fetchone()
        conn.close()
        if position:
            return position[0]
        return False
    except Exception as e:
        print(traceback.format_exc())
        return False


def get_company(user_id):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"SELECT company_id FROM users WHERE user_id=%s", (user_id,))
        company_id = cursor.fetchone()
        conn.close()
        if company_id:
            return company_id[0]
        return False
    except Exception as e:
        print(traceback.format_exc())
        return False


def get_position_id_by_learning_id(learning_id):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"SELECT position_id FROM learning WHERE learning_id=%s", (learning_id,))
        company_id = cursor.fetchone()
        if company_id:
            return company_id[0]
        return False
    except Exception as e:
        print(traceback.format_exc())
        return False


def get_all_users(company_id):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"SELECT u.user_id, u.username, u.position_id, "
                       f"u.position_learn_state, u.users_learn_state,"
                       "u.products_learn_state, u.company_learn_state "
                       "FROM users AS u WHERE u.company_id=%s", (company_id,))
        all_users = cursor.fetchall()
        conn.close()
        return all_users
    except Exception as e:
        print(traceback.format_exc())
        return False


def get_learning_ids(company_id, position_id, learn_type):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"SELECT learning_id FROM learning "
                       f"WHERE company_id=%s AND (position_id=%s OR position_id=-1) AND learn_type=%s "
                       f"ORDER BY position_id, number",
                       (company_id, position_id, learn_type))
        learning_ids = cursor.fetchall()
        conn.close()
        return learning_ids
    except Exception as e:
        print(traceback.format_exc())
        return 1


def get_learning_ids_r(company_id, position_id, learn_type):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"SELECT learning_id FROM learning "
                       f"WHERE company_id=%s AND position_id=%s AND learn_type=%s "
                       f"ORDER BY position_id, number",
                       (company_id, position_id, learn_type))
        learning_ids = cursor.fetchall()
        conn.close()
        return learning_ids
    except Exception as e:
        print(traceback.format_exc())
        return 1


def get_learning_file(learning_id):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"SELECT l.file_id, filename FROM learning_files AS l JOIN files AS f ON l.file_id=f.file_id "
                       f"WHERE learning_id=%s",
                       (learning_id,))
        file_id = cursor.fetchone()
        conn.close()
        if file_id:
            return file_id
        return False
    except Exception as e:
        print(traceback.format_exc())
        return False


def get_all_files(company_id):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"SELECT file_id, filename FROM files WHERE company_id={company_id}")
        file_ids = cursor.fetchall()
        conn.close()
        return file_ids
    except Exception as e:
        print(traceback.format_exc())
        return 1


def get_question_id_r(mas):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"SELECT question_id FROM questions "
                       f"WHERE learning_id IN ({','.join(mas)}) ")
        learning_ids = cursor.fetchall()
        conn.close()
        return learning_ids
    except Exception as e:
        print(traceback.format_exc())
        return 1


def get_information(company, position_id, learn_type):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"SELECT learning_id, info, position_id FROM learning "
                       f"WHERE company_id=%s AND position_id=%s AND learn_type=%s ORDER BY position_id, number",
                       (company, position_id, learn_type))
        info = cursor.fetchall()
        conn.close()
        if info:
            return info
        return []
    except Exception as e:
        print(traceback.format_exc())
        return False


def get_number_by_learning_id(learning_id):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"SELECT number FROM learning WHERE learning_id=%s", (learning_id,))
        number = cursor.fetchone()
        conn.close()
        if number:
            return number[0]
        return False
    except Exception as e:
        print(traceback.format_exc())
        return False


def get_first_state(company_id, position_id, what_get):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"SELECT learning_id FROM learning "
                       f"WHERE company_id=%s AND learn_type=%s AND (position_id=%s OR position_id=-1) "
                       f"ORDER BY position_id, number LIMIT 1",
                       (company_id, what_get, position_id))
        position = cursor.fetchone()
        conn.close()
        if position:
            return position[0]
        return False
    except Exception as e:
        print(traceback.format_exc())
        return False


def get_new_messages(user_id):
    try:
        conn, cursor = get_cursor()
        cursor.execute(
            f"SELECT u.username, message, u.user_id FROM messages AS m JOIN users AS u ON m.user_id=u.user_id "
            f"WHERE m.user_id=%s AND NOT is_read", (user_id,))
        number = cursor.fetchone()
        conn.close()

        if number:
            return number
        return False
    except Exception as e:
        print(traceback.format_exc())
        return False


def new_admin(email, password):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"INSERT INTO admins(email, password, sha) VALUES(%s, %s, SHA2(CONCAT(%s), 256))",
                       (email, password, email + password))
        conn.close()
        return True
    except Exception as e:
        print(traceback.format_exc())
        return False


def new_message(user_id, message, company_id, is_sender_admin):
    try:
        conn, cursor = get_cursor()
        cursor.execute(
            f"INSERT INTO messages(user_id, message, is_read, company_id, sender) VALUES(%s, %s, %s, %s, %s)",
            (user_id, message, is_sender_admin, company_id, is_sender_admin))

        conn.close()
        return True
    except Exception as e:
        print(traceback.format_exc())
        return False


def new_position(company_id, position):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"INSERT INTO positions(company_id, position) VALUES(%s, %s)",
                       (company_id, position))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(traceback.format_exc())
        return False


def new_company(sha, company):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"INSERT INTO companies(company) VALUES(%s)", (company,))
        set_admin_company(sha, cursor.lastrowid)
        conn.close()
        return True
    except Exception as e:
        print(traceback.format_exc())
        return False


def new_user(user_id, username, company_id, position_id):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"INSERT INTO users(user_id, username, company_id, position_id) "
                       f"VALUES(%s, %s, %s, %s)", (user_id, username, company_id, position_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(traceback.format_exc())
        return False


def new_learn(company_id, position_id, learn_type, number, info):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"INSERT INTO learning(company_id, position_id, learn_type,  number, info) "
                       f"VALUES(%s, %s, %s, %s, %s)",
                       (company_id, position_id, learn_type, number, info))
        conn.close()
        return cursor.lastrowid
    except Exception as e:
        print(traceback.format_exc())
        return False


def new_learning_file(file_id, learning_id):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"INSERT INTO learning_files(file_id, learning_id) "
                       f"VALUES(%s, %s)",
                       (file_id, learning_id))
        conn.close()
        return cursor.lastrowid
    except Exception as e:
        print(traceback.format_exc())
        return False


def new_question(learning_id, question):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"INSERT INTO questions(learning_id, question) "
                       f"VALUES(%s, %s)",
                       (learning_id, question))
        conn.close()
        return cursor.lastrowid
    except Exception as e:
        print(traceback.format_exc())
        return False


def new_file(company_id, filename):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"INSERT INTO files(company_id, filename) "
                       f"VALUES(%s, %s)",
                       (company_id, filename))
        conn.close()
        return cursor.lastrowid
    except Exception as e:
        print(traceback.format_exc())
        return False


def new_answer(question_id, answer, correct):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"INSERT INTO answers(question_id, answer, is_correct) "
                       f"VALUES(%s, %s, %s)",
                       (question_id, answer, correct))
        conn.close()
        return cursor.lastrowid
    except Exception as e:
        print(traceback.format_exc())
        return False


def set_state(user_id, learn_type, learning_id):
    try:
        conn, cursor = get_cursor()

        cursor.execute(f"UPDATE users SET {learn_type}_learn_state={learning_id} "
                       f"WHERE user_id=%s", (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(traceback.format_exc())
        return False


def set_username(user_id, username):
    try:
        conn, cursor = get_cursor()

        cursor.execute(f"UPDATE users SET username='{username}' "
                       f"WHERE user_id=%s", (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(traceback.format_exc())
        return False


def set_admin_company(sha, company_id):
    try:
        conn, cursor = get_cursor()
        print(sha, company_id)
        cursor.execute(f"UPDATE admins SET company_id={company_id} "
                       f"WHERE sha=%s", (sha,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(traceback.format_exc())
        return False


def set_read(user_id):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"UPDATE messages SET is_read=TRUE "
                       f"WHERE user_id=%s", (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(traceback.format_exc())
        return False


def del_learn(learning_id):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"DELETE FROM learning WHERE learning_id=%s", (learning_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(traceback.format_exc())
        return False


def del_info(company_id, position_id, learn_type):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"DELETE FROM learning WHERE company_id=%s AND position_id=%s AND learn_type=%s",
                       (company_id, position_id, learn_type))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(traceback.format_exc())
        return False


def del_questions(mas):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"DELETE FROM questions WHERE learning_id IN ({','.join(mas)})")
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(traceback.format_exc())
        return False


def del_infos(mas):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"DELETE FROM learning WHERE learning_id IN ({','.join(mas)})")
        conn.commit()
        conn.close()
        return True
    except:
        return False


def del_learning_files(mas):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"DELETE FROM learning_files WHERE learning_id IN ({','.join(mas)})")
        conn.commit()
        conn.close()
        return True
    except:
        return False


def del_answers(mas):
    try:
        conn, cursor = get_cursor()
        cursor.execute(f"DELETE FROM answers WHERE question_id IN ({','.join(mas)})")
        conn.commit()
        conn.close()
        return True
    except:
        return False


def sql(request):
    try:
        conn, cursor = get_cursor()
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
        conn.close()
        return response
    except Exception as e:
        return [[e]]


def found_next_learning(user_id, learning_id, learn_type):
    try:
        conn, cursor = get_cursor()
        number = get_number_by_learning_id(learning_id)
        user_position = get_user_position(user_id)[0]
        what_position = get_position_id_by_learning_id(learning_id)
        if what_position == -1:
            cursor.execute(f"SELECT learning_id FROM learning "
                           f"WHERE position_id=-1 AND number > {number} AND learn_type=%s ORDER BY number ",
                           (learn_type,))
            learning_first = cursor.fetchone()
            if learning_first:
                learning_next_id = learning_first[0]
            else:
                cursor.execute(f"SELECT learning_id FROM learning "
                               f"WHERE position_id={user_position} AND learn_type=%s "
                               f"ORDER BY number", (learn_type,))
                learning_second = cursor.fetchone()
                if learning_second:
                    learning_next_id = learning_second[0]
                else:
                    conn.close()
                    return False
        else:
            cursor.execute(f"SELECT learning_id FROM learning "
                           f"WHERE position_id={user_position} AND number > {number} AND learn_type=%s "
                           f"ORDER BY number", (learn_type,))
            learning_second = cursor.fetchone()
            if learning_second:
                learning_next_id = learning_second[0]
            else:
                conn.close()
                return False
        conn.close()
        return learning_next_id
    except Exception as e:
        print(traceback.format_exc())
        return False


def found_prev_learning(user_id, learning_id, learn_type):
    try:
        conn, cursor = get_cursor()
        user_position = get_user_position(user_id)[0]
        number = get_number_by_learning_id(learning_id)
        what_position = get_position_id_by_learning_id(learning_id)
        if what_position != -1:
            cursor.execute(f"SELECT learning_id FROM learning "
                           f"WHERE position_id={user_position} AND number < {number} AND learn_type=%s "
                           f"ORDER BY -number", (learn_type,))
            learning_first = cursor.fetchone()
            if learning_first:
                learning_prev_id = learning_first[0]
            else:
                cursor.execute(f"SELECT learning_id FROM learning WHERE position_id=-1 AND learn_type=%s "
                               f"ORDER BY -number", (learn_type,))
                learning_second = cursor.fetchone()
                if learning_second:
                    learning_prev_id = learning_second[0]
                else:
                    conn.close()
                    return False
        else:
            cursor.execute(f"SELECT learning_id FROM learning "
                           f"WHERE position_id=-1 AND number < {number} AND learn_type=%s "
                           f"ORDER BY -number", (learn_type,))
            learning_first = cursor.fetchone()
            if learning_first:
                learning_prev_id = learning_first[0]
            else:
                conn.close()
                return True
        conn.close()
        return learning_prev_id
    except Exception as e:
        print(traceback.format_exc())
        return False


def found_first_learning(user_id, learning_id, learn_type):
    try:
        conn, cursor = get_cursor()
        number = get_number_by_learning_id(learning_id)
        user_position = get_user_position(user_id)[0]
        what_position = get_position_id_by_learning_id(learning_id)
        cursor.execute(f"SELECT learning_id FROM learning "
                       f"WHERE (position_id=-1 OR position_id={user_position}) AND learn_type=%s "
                       f"ORDER BY position_id, number ",
                       (learn_type,))
        learning_first = cursor.fetchone()
        conn.close()
        if learning_first:
            return learning_first[0]
    except Exception as e:
        print(traceback.format_exc())
        return False


db_init()
