from flask import Flask, render_template
from flaskext.mysql import MySQL

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


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
