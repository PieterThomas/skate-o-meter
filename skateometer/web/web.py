# region Imports
import logging

from flask import Flask, request, abort, flash, render_template, session, redirect, make_response, url_for
from flaskext.mysql import MySQL
from flask_httpauth import HTTPBasicAuth
from passlib import pwd
from passlib.hash import argon2
from functools import wraps
import time, serial, jwt
from RPi import GPIO

# endregion

log = logging.getLogger(__name__)
app = Flask(__name__, template_folder='./templates')
mysql = MySQL(app)
auth = HTTPBasicAuth()

# region MySQL configurations

app.config['MYSQL_DATABASE_USER'] = 'som-web'
app.config['MYSQL_DATABASE_PASSWORD'] = 'web9810'
app.config['MYSQL_DATABASE_DB'] = 'skateometerdb'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

# endregion

# session config
app.secret_key = pwd.genword(entropy=128)


# region get & set data van database
def get_data(sql, params=None):
    conn = mysql.connect()
    cursor = conn.cursor()
    records = []

    try:
        log.debug(sql)
        cursor.execute(sql, params)
        result = cursor.fetchall()
        for row in result:
            records.append(list(row))

    except Exception as e:
        log.exception("Fout bij het ophalen van data: {0})".format(e))

    cursor.close()
    conn.close()

    return records


def set_data(sql, params=None):
    conn = mysql.connect()
    cursor = conn.cursor()

    try:
        log.debug(sql)
        cursor.execute(sql, params)
        conn.commit()
        log.debug("SQL uitgevoerd")

    except Exception as e:
        log.exception("Fout bij uitvoeren van sql: {0})".format(e))
        return False

    cursor.close()
    conn.close()

    return True


# endregion

# region Maak user
def add_user(login, password, uid):
    try:
        if get_data('SELECT phcstring FROM skateometerdb.users WHERE userid=%s', (login,)):
            message = 'User {} exists!'.format(login)
            log.info(message)
            return False, message

        if get_data('SELECT phcstring FROM skateometerdb.users WHERE BadgeID=%s', (uid,)):
            message = 'BadgeID {} exists!'.format(uid)
            log.info(message)
            return False, message

        argon_hash = argon2.hash(password)
        if set_data('INSERT INTO skateometerdb.users (BadgeID, userid, phcstring) VALUES (%s, %s, %s);',
                    (uid, login, argon_hash)):
            message = 'Added user {}'.format(login)
            log.info(message)
            return True, message

    except Exception as e:
        message = 'Error adding user {}: {}'.format(login, e)
        log.error(message)
        return False, message


# endregion

# region login_required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('auth_token'):  # Kijkt of de cookie bestaat
            return redirect(url_for('login', next=request.url))  # Je wordt doorverwezen naar de login pagina
        return f(*args, **kwargs)

    return decorated_function


# endregion

# region decode_token

def decode_token():
    token = session.get('auth_token')
    if token:
        try:
            return jwt.decode(token, app.secret_key)
        except Exception as e:
            log.exception(e)
            return render_template("login.html", message="Mislukt")


# endregion

# region verify_credentials
@auth.verify_password
def verify_credentials(login, password):
    if decode_token():
        log.debug("Authenticated by token")
        return True
    record = get_data('SELECT phcstring FROM skateometerdb.users WHERE userid=%s', (login,))
    if not record:
        return False
    authorized = argon2.verify(password, record[0][0])
    if authorized:
        session['auth_token'] = jwt.encode(
            {'user': login},
            app.secret_key,
        )
    return authorized


# endregion

# region Tijd omzetten naar juiste waarde
def timedeltatotime(timedeltatime):
    tijd = []
    for i in timedeltatime:
        for x in i:
            uur = str(x)
            tijd.append(uur)

    return tijd


# endregion

# region BadgeID

def get_badgeid():
    ser = serial.Serial('/dev/ttyUSB0', 9600)
    _id = ""
    id_found = True
    while id_found:
        naam = ser.read_all()
        plaats = str(naam).find("UID:")
        if plaats != -1:
            uidSerial = naam[plaats + 3:plaats + 14]
            uid = str(uidSerial, 'utf-8')
            _id = uid.replace(" ", "")
            print(_id)
            if len(_id) == 8:
                id_found = False
                return _id
        time.sleep(0.25)


# endregion

# region Login / Register / Logout

@app.route('/register', methods=['GET', 'POST'])
def register():
    result = None
    GPIO.add_event_detect()
    if request.method == 'POST':
        user = request.form['user']
        password = request.form['password']
        if not user and password:
            abort(400)
        result, message = add_user(user, password, get_badgeid())
        flash(message)
    return render_template('register.html', success=result)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        user = request.form['user']
        password = request.form['password']
        uid = get_data("SELECT BadgeID FROM skateometerdb.users WHERE userid = (%s)", user)

        for i in uid:
            for x in i:
                badgeid = x
        if not user and password:
            mes = "Fill all fields."
            return render_template('login.html', message=mes)
        if verify_credentials(user, password):
            logged_in = make_response(redirect('/secure'))
            logged_in.set_cookie('badgeid', badgeid)
            return logged_in
        else:
            mes = "Wrong username or password"
            return render_template('login.html', message=mes)
    else:
        print("Something went wrong, please try again.")
        return render_template('login.html', mes="Something went wrong, please try again.")


@app.route('/logout')
def logout():
    session.pop('auth_token')
    resp = make_response(redirect('login'))
    resp.set_cookie('badgeid', "mislukt", expires=0)
    return resp


@app.route('/secure')
@auth.login_required
def secure():
    auth_data = decode_token()
    if not auth_data:
        abort(403)
    return redirect('/')


# endregion


@app.route('/')
@login_required
def index():
    badgeid = request.cookies.get('badgeid')
    name = get_data(
        "SELECT column_name from information_schema.columns where table_schema='skateometerdb' and table_name='session'")
    data = get_data("SELECT SessionID, BadgeID, Starttime, Endtime, ROUND(Distance, 2) FROM skateometerdb.session WHERE BadgeID = (%s)", badgeid)
    return render_template("sessiemenu.html", sessies=data, name=name)


@app.route("/data")
@login_required
def data():
    badgeid = request.cookies.get('badgeid')
    field_names = get_data(
        "SELECT column_name from information_schema.columns where table_schema='skateometerdb' and table_name='data'")
    data_list = get_data(
        "SELECT * FROM speedometerdb.data as D INNER JOIN skateometerdb.session as S ON D.SessionID = S.SessionID WHERE S.BadgeID = (%s)",
        badgeid)

    return render_template("data.html", data=data_list, columns=field_names)


@app.route("/details-session-<sessie>")
@login_required
def sessiondetail(sessie):
    info = []
    info.append(get_data("SELECT ROUND(AVG(Speed),2) FROM skateometerdb.data WHERE SessionID = (%s)", sessie))
    info.append(get_data("SELECT TIMEDIFF(max(TimeHM), min(TimeHM)) FROM skateometerdb.data WHERE SessionID = (%s)",
                         sessie))
    info.append(get_data("SELECT ROUND(MIN(Speed),2) FROM skateometerdb.data WHERE SessionID = (%s)", sessie))
    info.append(get_data("SELECT ROUND(MAX(Speed),2) FROM skateometerdb.data WHERE SessionID = (%s)", sessie))

    snelheid = []
    for i in get_data("SELECT ROUND(Speed, 2) FROM skateometerdb.data WHERE SessionID = (%s)", sessie):
        for x in i:
            snelheid.append(x)
    tijd = timedeltatotime(get_data("SELECT TimeHM FROM skateometerdb.data WHERE SessionID = (%s)", sessie))
    print(snelheid)
    print(tijd)

    return render_template("session_detail.html", speed=snelheid, time=tijd, info=info)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    log.info("Flask app starting")
    app.run(host='0.0.0.0', debug=True)
