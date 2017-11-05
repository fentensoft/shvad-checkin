from flask import Flask, render_template, request, jsonify, send_from_directory
from flaskext.mysql import MySQL
from json import dumps
from pymysql.cursors import DictCursor
import re
import pandas as pd
import datetime

app = Flask(__name__)
app.config["MYSQL_DATABASE_HOST"] = "172.17.0.14"
app.config["MYSQL_DATABASE_PORT"] = 3306
app.config["MYSQL_DATABASE_USER"] = "root"
app.config["MYSQL_DATABASE_PASSWORD"] = "tony989@pple"
app.config["MYSQL_DATABASE_DB"] = "shvad"
mysql = MySQL()
mysql.init_app(app)


@app.route('/')
def index():
    conn = mysql.get_db()
    cur = conn.cursor()
    cur.execute("SELECT config_value FROM config WHERE config_name='index_title';")
    title = cur.fetchone()[0]
    cur.execute("SELECT config_value FROM config WHERE config_name='index_prompt';")
    prompt = cur.fetchone()[0]
    cur.execute("SELECT config_value FROM config WHERE config_name='checkin_start';")
    start = datetime.datetime.strptime(cur.fetchone()[0], "%Y-%m-%d %H:%M")
    cur.execute("SELECT config_value FROM config WHERE config_name='checkin_stop';")
    end = datetime.datetime.strptime(cur.fetchone()[0], "%Y-%m-%d %H:%M")
    return render_template('index.html', ddl=get_ddl(), title=title, prompt=prompt, checkin_avail=(start <= datetime.datetime.now() <= end))


@app.route('/timeconfig', methods=['GET', 'POST'])
def timeconfig():
    conn = mysql.get_db()
    cur = conn.cursor()
    if request.method == 'GET':
        cur.execute("SELECT config_value FROM config WHERE config_name='checkin_start';")
        start = cur.fetchone()[0]
        cur.execute("SELECT config_value FROM config WHERE config_name='checkin_stop';")
        stop = cur.fetchone()[0]
        return jsonify({"checkin_start": start, "checkin_stop": stop})
    else:
        start = request.form.get("checkin_start")
        stop = request.form.get("checkin_stop")
        cur.execute("UPDATE config SET config_value=%s WHERE config_name='checkin_start';", start)
        cur.execute("UPDATE config SET config_value=%s WHERE config_name='checkin_stop';", stop)
        conn.commit()
        return jsonify({"ret": 1})


@app.route('/reset')
def reset():
    conn = mysql.get_db()
    cur = conn.cursor()
    cur.execute("UPDATE attend SET attendance=0, paid=0, fp='';")
    conn.commit()
    return "1"


@app.route("/payment")
def payment():
    return render_template("payment.html")


@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route("/getpayment")
def getpayment():
    cur = DictCursor(mysql.get_db())
    cur.execute("SELECT id,stu_name,stu_unit,price FROM attend WHERE paid=0 AND attendance=1;")
    return dumps(cur.fetchall(), ensure_ascii=False)


@app.route("/getlist")
def getlist():
    cur = DictCursor(mysql.get_db())
    cur.execute("SELECT * FROM attend;")
    return jsonify(cur.fetchall())


@app.route("/getexcel")
def getexcel():
    conn = mysql.get_db()
    df = pd.read_sql("SELECT id,stu_name,stu_gender,stu_unit,attendance FROM attend;", conn, index_col="id")
    df.to_excel("tmp.xlsx")
    return send_from_directory("./", "tmp.xlsx", as_attachment=True, attachment_filename="attend_{}.xlsx".format(datetime.datetime.now().strftime("%Y-%m-%d-%H:%M")))


@app.route("/confirmpayment", methods=["POST"])
def confirmpayment():
    cid = request.form.get("id")
    if cid:
        conn = mysql.get_db()
        cur = conn.cursor()
        cur.execute("UPDATE attend SET paid=1 WHERE id=%s;", cid)
        conn.commit()
        if cur.rowcount == 1:
            return '{"ret": 1}'
        else:
            return '{"ret": -1}'
    else:
        return '{"ret": -2}'


def get_column_config():
    conn = mysql.get_db()
    cur = conn.cursor()
    cur.execute("SELECT col_name, col_is_input FROM ddl_config;")
    ret = {}
    for i in cur.fetchall():
        ret[i[0]] = i[1]
    return ret


@app.route('/info', methods=["POST"])
def info():
    stu_name = request.form.get("stu_name")
    fp = request.form.get("fp")
    if stu_name and fp:
        result = {}
        cur = DictCursor(mysql.get_db())
        cur.execute("SELECT COUNT(*) AS c FROM attend WHERE fp=%s;", fp)
        if cur.fetchone()["c"] > 0:
            return jsonify({"ret": -2})
        cur.execute("SELECT * FROM attend WHERE stu_name=%s;", stu_name)
        data = cur.fetchone()
        col_config = get_column_config()
        if data:
            del data["fp"]
            result["id"] = data.pop("id")
            result["attendance"] = data.pop("attendance")
            new_data = {}
            for item in data:
                if isinstance(data[item], str):
                    data[item] = data[item].strip()
                    if col_config[item] == 0:
                        data[item] = data[item].replace("\n", "<br/>")
                        if not data[item]:
                            data[item] = "无"
                if col_config[item] == 1:
                    new_data["input_" + item] = data[item]
                else:
                    new_data[item] = data[item]
            result["data"] = new_data
            result["ret"] = 1
        else:
            result["ret"] = -1
        return jsonify(result)
    else:
        return jsonify({"ret": -1})


@app.route("/checkin", methods=["POST"])
def checkin():
    cid = request.form.get("id")
    if cid:
        conn = mysql.get_db()
        cur = DictCursor(conn)
        varlist = ""
        val_tuple = ()
        for item in request.form:
            if item.startswith("input_"):
                varlist += "," + item.replace("input_", "") + "=%s"
                val_tuple += (request.form[item], )
        val_tuple += (request.form.get("fp"), cid, )
        cur.execute("UPDATE attend SET attendance=1" + varlist + ",fp=%s WHERE id=%s;", val_tuple)
        conn.commit()
        if cur.rowcount == 1:
            return jsonify({"ret": 1})
        else:
            return jsonify({"ret": -1})
    else:
        return jsonify({"ret": -1})


def get_ddl():
    conn = mysql.get_db()
    cur = conn.cursor()
    ret = []
    for i in range(2):
        cur.execute("SELECT DISTINCT col_category FROM ddl_config WHERE col_is_input=%s AND col_display=1;", i)
        categories = cur.fetchall()
        ret.append([])
        for category in categories:
            cur.execute("SELECT col_name, col_label, col_type FROM ddl_config WHERE col_is_input=%s  AND col_category=%s AND col_display=1 ORDER BY col_priority ;", (i, category[0]))
            blocks = cur.fetchall()
            curr_category = {"category": category[0], "rows":[], "cards": []}
            for block in blocks:
                row = {}
                row["col_name"] = block[0]
                row["col_label"] = block[1]
                row["col_type"] = re.sub(r"\(\d*\)", "", block[2])
                if row["col_type"] == "TEXT":
                    curr_category["cards"].append(row)
                else:
                    curr_category["rows"].append(row)
            ret[i].append(curr_category)
    return ret

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
