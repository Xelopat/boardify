import time

from flask import Flask, render_template, request, make_response, redirect, abort, jsonify

from db import *
from boardify_bot import *

app = Flask(__name__)
webhook_url = "https://6367-45-87-247-172.ngrok-free.app"


@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        abort(403)


@app.route('/')
@app.route('/index')
def index():
    key = request.cookies.get('key')
    return render_template("./index.html",
                           is_entered=is_admin(key),
                           admin_company=get_company_by_id(get_admin_company(key)))


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    key = request.cookies.get('key')
    if is_admin(key):
        return redirect("/")
    if request.method == 'POST':
        email, password = request.form.get("email"), request.form.get("password")
        if email and password:
            if not is_admin_exists(email):
                new_admin(email, password)
                key = get_admin(email, password)
                res = make_response(redirect("/index"))
                res.set_cookie('key', key)
                return res
            else:
                return render_template("./registration.html",
                                       is_entered=is_admin(request.cookies.get('key')),
                                       err="Уже зарегестрирован")
        else:
            return render_template("./registration.html",
                                   is_entered=is_admin(request.cookies.get('key')))
    elif request.method == 'GET':
        return render_template("./registration.html",
                               is_entered=is_admin(request.cookies.get('key')))


@app.route('/login', methods=['GET', 'POST'])
def login():
    key = request.cookies.get('key')
    if is_admin(key):
        return redirect("/")
    if request.method == 'POST':
        email, password = request.form.get("email"), request.form.get("password")
        key = get_admin(email, password)
        if key:
            res = make_response(redirect("/index"))
            res.set_cookie('key', key)
            return res
        else:
            return render_template("./login.html",
                                   is_entered=is_admin(request.cookies.get('key')),
                                   err="Неверные данные")
    elif request.method == 'GET':
        return render_template("./login.html",
                               is_entered=is_admin(request.cookies.get('key')))


@app.route('/chat', methods=['GET', 'POST'])
def chat():
    key = request.cookies.get('key')
    if not is_admin(key):
        return redirect("/")
    if request.method == "GET":
        if request.args:
            if "user" in request.args:
                user_id = request.args["user"]
                messages = get_messages(user_id)
                set_read(user_id)
                return render_template("./chat.html",
                                       messages=messages, user_id=user_id)


@app.route('/send_message', methods=['POST'])
def send_message():
    key = request.cookies.get('key')
    if not is_admin(key):
        return ""
    if request.method == "POST":
        if "user_id" in request.form:
            user_id = request.form["user_id"]
            text = request.form["text"]
            new_message(user_id, text, get_admin_company(key), True)
            bot.send_message(user_id, text)
            return ""


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    key = request.cookies.get('key')
    admin_company = get_admin_company(key)
    if not is_admin(key):
        return redirect("/")
    if request.method == "POST":
        files = request.files.getlist('file')
        path = f"./files/{admin_company}/"
        if not os.path.exists(path):
            os.makedirs(path)
        for file in files:
            filename = file.filename
            file_id = new_file(admin_company, filename)
            file.save(f"{path}{file_id}_{filename}")
        return render_template("/upload.html", message=["Успех!", "Файлы успешно загружены!"])
    else:
        return render_template("/upload.html")


@app.route('/check_new_message', methods=['POST'])
def check_new_message():
    if request.method == "POST":
        if "user_id" in request.form:
            user_id = request.form["user_id"]
            new_messages = get_new_messages(user_id)
            if new_messages:
                if request.form["read"] == "yes":
                    set_read(user_id)
                return {"username": new_messages[0], "text": new_messages[1], "user_id": new_messages[2]}
            return "no"


@app.route('/join_company', methods=['GET', 'POST'])
def join_company():
    key = request.cookies.get('key')
    has_company = get_admin_company(key)
    if has_company or not key:
        return redirect("/")
    if request.method == 'POST':
        code = request.form.get("code")
        joined_company = get_admin_company(code)
        if joined_company:
            set_admin_company(key, joined_company)
            return redirect("/index")
        else:
            return render_template("./join_company.html",
                                   is_entered=is_admin(key),
                                   err="Неверные данные")
    elif request.method == 'GET':
        return render_template("./join_company.html",
                               is_entered=is_admin(key))


@app.route('/create_company', methods=['GET', 'POST'])
def create_company():
    key = request.cookies.get('key')
    has_company = get_admin_company(key)
    if has_company:
        return redirect("/")
    if request.method == 'POST':
        company = request.form.get("company")
        if company and is_admin(key):
            new_company(key, company)
            return redirect("/index")
        else:
            if has_company:
                return render_template("./create_company.html",
                                       is_entered=is_admin(key),
                                       err="У Вас уже есть компания")
            else:
                return render_template("./create_company.html",
                                       is_entered=is_admin(key),
                                       err="Неверные данные")
    elif request.method == 'GET':
        return render_template("./create_company.html",
                               is_entered=is_admin(key))


@app.route('/employers', methods=['GET'])
def employers():
    key = request.cookies.get('key')
    admin = is_admin(key)
    admin_company = get_admin_company(key)
    all_users = get_all_users(admin_company)
    percents = []
    for i in all_users:
        count_position = [i[0] for i in get_learning_ids(admin_company, i[2], "position")]
        count_users = [i[0] for i in get_learning_ids(admin_company, i[2], "users")]
        count_products = [i[0] for i in get_learning_ids(admin_company, i[2], "products")]
        count_company = [i[0] for i in get_learning_ids(admin_company, i[2], "company")]
        percents.append(
            [100 if not i[3] else 0 if i[3] == -1 else count_position.index(i[3]) * 100 // len(
                count_position) if count_position else 0,
             100 if not i[4] else 0 if i[4] == -1 else count_users.index(i[4]) * 100 // len(
                 count_users) if count_users else 0,
             100 if not i[5] else 0 if i[5] == -1 else count_products.index(i[5]) * 100 // len(
                 count_products) if count_products else 0,
             100 if not i[6] else 0 if i[6] == -1 else count_company.index(i[6]) * 100 // len(
                 count_company) if count_company else 0])
    if not admin:
        return redirect("/")

    return render_template("./employers.html", users=all_users, len=len(all_users), percents=percents,
                           users_json=[i[0] for i in all_users])


@app.route('/mailing', methods=['GET', 'POST'])
def mailing():
    key = request.cookies.get('key')
    admin_company = get_admin_company(key)
    if not admin_company:
        return redirect("/")
    if request.method == "POST":
        if "text" in request.form:
            users = get_all_users(admin_company)
            text = request.form["text"]
            for i in users:
                bot.send_message(i[0], text)
            return render_template("./mailing.html", message=["Успех!", "Сообщения разосланы"])
        else:
            render_template("./mailing.html")
    all_positions = get_all_users(admin_company)
    return render_template("./mailing.html")


@app.route('/links', methods=['GET'])
def links():
    key = request.cookies.get('key')
    admin_company = get_admin_company(key)
    all_positions = get_all_positions(admin_company)
    return render_template("./links.html", company=admin_company, positions=all_positions, key=key)


@app.route('/options', methods=['GET', 'POST'])
def options():
    if request.method == "POST":
        key = request.cookies.get('key')
        admin_company = get_admin_company(key)
        if "edit" in request.args and "position_id" in request.args:
            edit = request.args["edit"]
            position_id = request.args["position_id"]
            args = request.form
            all_dict = {}
            for i in args:
                text = args[i]
                if i[-1] == "f":
                    all_dict[int(i[:-1])][2] = text
                    continue
                level = [int(j) for j in i.split("_")]
                level_len = len(level)
                if level_len == 1:
                    all_dict[level[0]] = [text, {}, ""]
                elif level_len == 2:
                    all_dict[level[0]][1][level[1]] = [text, {}]
                elif level_len == 3:
                    all_dict[level[0]][1][level[1]][1][level[2]] = [text, 0]
                elif level_len == 4:
                    all_dict[level[0]][1][level[1]][1][level[2]][1] = 1

            learning_ids_r = [str(i[0]) for i in get_learning_ids_r(admin_company, position_id, edit)]
            learning_ids_r.append("-1")
            question_id_r = [str(i[0]) for i in get_question_id_r(learning_ids_r)]

            del_learning_files(learning_ids_r)
            del_infos(learning_ids_r)
            del_questions(learning_ids_r)
            del_answers(question_id_r)
            for i in all_dict:
                learning_id = new_learn(admin_company, position_id, edit, i, all_dict[i][0])
                if all_dict[i][2] != "-1":
                    new_learning_file(all_dict[i][2], learning_id)
                for j in all_dict[i][1]:
                    question_id = new_question(learning_id, all_dict[i][1][j][0])
                    for k in all_dict[i][1][j][1]:
                        new_answer(question_id, all_dict[i][1][j][1][k][0], all_dict[i][1][j][1][k][1])
            return render_template("./options.html", edit=False, mas=False,
                                   message=["Успех!", "Данные успешно обновлены"],
                                   positions=get_all_positions(admin_company))
        elif "position" in request.form:
            if not is_position_exist(admin_company, request.form["position"]):
                new_position(admin_company, request.form["position"])
                return render_template("./options.html", edit=False, mas=False,
                                       message=["Успех!", f'Должность {request.form["position"]} успешно добавлена'],
                                       positions=get_all_positions(admin_company))
            else:
                return render_template("./options.html", edit=False, mas=False,
                                       message=["Ошибка!", "Такая должность уже есть"],
                                       positions=get_all_positions(admin_company))
        return render_template("./options.html", edit=False, mas=False,
                               positions=get_all_positions(admin_company))
    if request.method == 'GET':
        key = request.cookies.get('key')
        admin = is_admin(key)
        admin_company = get_admin_company(key)
        positions = get_all_positions(admin_company)
        edit = False
        mas = False
        if request.args:
            if "edit" in request.args and "position_id" in request.args:
                edit = request.args["edit"]
                positions = request.args["position_id"]
                information = get_information(admin_company, positions, edit)
                mas = []
                for i in information:
                    learning_id, info, position_id = i
                    questions = get_questions(learning_id, [-1])
                    questions_d = []
                    file = get_learning_file(learning_id)
                    for q in questions:
                        question_id, question = q
                        answers = get_answers(question_id)
                        answers_mas = []
                        for a in answers:
                            answer_id, answer, correct = a
                            answers_mas.append([answer_id, answer, correct])
                        questions_d.append([question_id, question, answers_mas])
                    mas.append([learning_id, info, position_id, questions_d, file])
        if not admin:
            return redirect("/")
        all_files = get_all_files(admin_company)
        return render_template("./options.html", edit=edit, mas=mas, positions=positions, all_files=all_files)


if __name__ == '__main__':
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(webhook_url + "/webhook")
    app.run(host="localhost", port=5000, debug=True)
