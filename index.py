from flask import Flask, render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fh.db'
db = SQLAlchemy(app)
lg = LoginManager(app)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # author =
    title = db.Column(db.String(50), nullable=False)
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    tegs = db.Column(db.String(100))

    def __repr__(self):
        return '<Post %r>' % self.id


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    surname = db.Column(db.String(50), nullable=False)
    login = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(50), nullable=False)

    def __init__(self):
        self.__user = None

    def fromdb(self, user_id, database):
        self.__user = database.getUser(user_id)
        return self

    def create(self, user):
        self.__user = user
        return self

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.__user['id'])


@lg.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/')
@app.route('/home')
def index():
    return render_template('index.html')


@app.route('/create-post', methods=['GET', 'POST'])
@login_required
def create_post():
    return render_template('create_post.html')


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    login = request.form.get('login')
    password = request.form.get('password')

    if login and password:
        user = User.query.filter_by(login=login).first()

        if check_password_hash(user.password, password):
            login_user(user)

            next_page = request.args.get('next')
            redirect(next_page)
        else:
            flash('Неверный логин или пароль')

    else:
        flash('')
        return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    login = request.form.get('login')
    password = request.form.get('password')
    password_retype = request.form.get('password_retype')
    name = request.form.get('name')
    surname = request.form.get('surname')

    if request.method == 'POST':
        if not (login or password or password_retype):
            flash('Заполните все поля')
        elif password != password_retype:
            flash('Неверно повторен пароль')
        else:
            hash_pwd = generate_password_hash(password)
            new_user = User(login=login, password=hash_pwd, name=name, surname=surname)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
    return render_template('register.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout_page():
    logout_user()
    return redirect(url_for('index'))


@app.after_request
def redirect_to_signin(response):
    if response.status_code == 401:
        return redirect(url_for('login_page') + '?next=' + request.url)


if __name__ == '__main__':
    app.run(debug=True)
