from flask import Flask, render_template, request
from flaskext.mysql import MySQL
from json import dumps
from pymysql.cursors import DictCursor

app = Flask(__name__)
app.config["MYSQL_DATABASE_HOST"] = "127.0.0.1"
app.config["MYSQL_DATABASE_USER"] = "root"
app.config["MYSQL_DATABASE_PASSWORD"] = ""
app.config["MYSQL_DATABASE_DB"] = "shvad"
mysql = MySQL()
mysql.init_app(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/info', methods=["POST"])
def info():
    stu_name = request.form.get("stu_name")
    if stu_name:
        result = {}
        cur = DictCursor(mysql.get_db())
        cur.execute("SELECT * FROM attend WHERE stu_name=%s;", stu_name)
        data = cur.fetchone()
        if data:
            result["id"] = data.pop("id")
            result["attendance"] = data.pop("attendance")
            for item in data:
                if isinstance(data[item], str):
                    data[item] = data[item].strip().replace("\n", "<br/>")
            result["data"] = data
            result["ret"] = 1
        else:
            result["ret"] = -1
        return dumps(result, ensure_ascii=False)
    else:
        return '{"ret": -1}'


@app.route("/checkin", methods=["POST"])
def checkin():
    cid = request.form.get("id")
    if cid:
        conn = mysql.get_db()
        cur = DictCursor(conn)
        cur.execute("UPDATE attend SET attendance=1 WHERE id=%s;", cid)
        conn.commit()
        if cur.rowcount == 1:
            return '{"ret": 1}'
        else:
            return '{"ret": -1}'
    else:
        return '{"ret": -1}'


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
