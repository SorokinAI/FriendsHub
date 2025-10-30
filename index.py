from flask import Flask, render_template, request, redirect, flash, url_for, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import re
from mail_valid import evalid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fh.db'
app.config['SECRET_KEY'] = '123099323hkdsf9932'
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    surname = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telegram_username = db.Column(db.String(64))
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False


    def get_id(self):
        """Возвращает строковую версию идентификатора."""
        return str(self.id)


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    text = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    ser_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # связь с пользователем
    tags = db.relationship('Tag', secondary='post_tags',
                           backref=db.backref('posts', lazy='dynamic'))  # связь с тегами через промежуточную таблицу

    def __repr__(self):
        return f'Post({self.title}, {self.date})'


class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)


# промежуточная таблица для связи многих ко многим между постами и тегами
post_tags = db.Table('post_tags',
                     db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
                     db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
                     )


@app.route('/')
@app.route('/home')
def index():
    posts = Post.query.order_by(Post.date.desc()).all()  # вывод всех постов, сортируя по дате публикации
    return render_template('index.html', posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        telegram_username = request.form['tg']
        password = request.form['password']
        password_retype = request.form['password_retype']

        symbols_to_remove = ['https://t.me/', 't.me/']
        for symbol in symbols_to_remove:
            telegram_username = telegram_username.replace(symbol, "@")

        # Проверки полей
        if not name or not surname or not email or not password or not telegram_username:
            flash("Пожалуйста, заполните все поля", category="error")
            return redirect('/register')

        if User.query.filter_by(email=email).first():
            flash(f"Email '{email}' уже зарегистрирован", category="warning")
            return redirect('/register')

        if not evalid(email):
            flash(f"Введите адрес email", category="warning")
            return redirect('/register')

        if password != password_retype:
            flash(f"Пароли не совпадают", category="warning")
            return redirect('/register')

        # Хешируем пароль
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Создаем нового пользователя
        user = User(
            name=name,
            surname=surname,
            email=email,
            telegram_username=telegram_username,
            password_hash=hashed_password
        )
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=False)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect('/')
        else:
            flash("Что-то введено не верно!", category="danger")

    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/create-post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form.get('title').strip()
        text = request.form.get('text').strip()
        tags_str = request.form.get('tags')  # Получаем строку с тегами

        # Проверяем, заполнены ли поля
        if not title or not text or not tags_str:
            flash('Пожалуйста, заполните все поля.')
            return redirect(url_for('create_post'))

        # Разбиваем строку с тегами на отдельные теги
        tags_list = [t.strip().lower() for t in re.split(r'[,. ]+', tags_str) if t.strip()]

        # Определяем, какие теги уже существуют в базе данных
        existing_tags = Tag.query.filter(Tag.name.in_(tags_list)).all()
        existing_tag_names = {tag.name for tag in existing_tags}

        # Создаем новые теги, которых еще нет в базе данных
        new_tags = []
        for tag_name in tags_list:
            if tag_name not in existing_tag_names:
                new_tag = Tag(name=tag_name)
                new_tags.append(new_tag)

        # Добавляем новые теги в сессию
        db.session.add_all(new_tags)

        # Создаем пост и добавляем к нему все теги
        post = Post(title=title, text=text, author=current_user)
        post.tags.extend(existing_tags + new_tags)

        try:
            db.session.add(post)
            db.session.commit()
            return redirect('/')
        except Exception as e:
            db.session.rollback()
            print(f'Ошибка при добавлении поста: {str(e)}')
    else:
        return render_template('create_post.html')


@app.route('/search-by-tag')
def search_by_tag():
    query = request.args.get('tag')
    if query:
        # Поиск постов по тегу
        found_posts = Post.query.join(post_tags).join(Tag, post_tags.c.tag_id == Tag.id).filter(Tag.name.ilike(f'%{query}%')).all()
        return render_template('search_results.html', posts=found_posts, query=query)
    else:
        return redirect(url_for('index'))  # Если тег не указан, переходим на главную страницу


@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = User.query.get(user_id)
    posts = Post.query.filter(Post.ser_id == user_id).order_by(Post.date.desc()).all()
    return render_template('profile.html', user=user, posts=posts)


@app.route('/about_us')
def dw():
    return render_template('digital_wind.html')


if __name__ == '__main__':
    app.run(debug=True)
