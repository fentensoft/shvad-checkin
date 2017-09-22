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


@app.route("/payment")
def payment():
    return render_template("payment.html")


@app.route("/getpayment")
def getpayment():
    cur = DictCursor(mysql.get_db())
    cur.execute("SELECT id,stu_name,price FROM attend WHERE paid=0 AND attendance=1;")
    return dumps(cur.fetchall(), ensure_ascii=False)


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
                    data[item] = data[item].strip()
                    if item != "address":
                        data[item] = data[item].replace("\n", "<br/>")
                    if (item != "vat_invoice") and (item != "address") and (data[item] == ""):
                        data[item] = "无"
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
    address = request.form.get("address").strip()
    if cid:
        conn = mysql.get_db()
        cur = DictCursor(conn)
        cur.execute("UPDATE attend SET attendance=1,address=%s WHERE id=%s;", (address, cid))
        conn.commit()
        if cur.rowcount == 1:
            return '{"ret": 1}'
        else:
            return '{"ret": -1}'
    else:
        return '{"ret": -1}'


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
