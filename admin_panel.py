"""Файл с настройкой admin-панели и представления моделей"""

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask import redirect, url_for
from flask_login import current_user


class AdminModelView(ModelView):
    """Базовый класс для всех админских представлений с проверкой прав"""

    def is_accessible(self):
        # Проверяем, что пользователь аутентифицирован и является админом
        return current_user.is_authenticated and getattr(current_user, 'is_admin', False)

    def inaccessible_callback(self, name, **kwargs):
        # Если нет доступа - перенаправляем на главную
        return redirect(url_for('index'))


class UserModelView(AdminModelView):
    """Представление для модели User"""

    column_list = ['id', 'name', 'surname', 'email', 'telegram_username', 'is_admin', 'posts']
    column_searchable_list = ['name', 'surname', 'email', 'telegram_username']
    column_filters = ['name', 'surname', 'email', 'is_admin']
    column_editable_list = ['name', 'surname', 'telegram_username', 'is_admin']
    form_columns = ['name', 'surname', 'email', 'telegram_username', 'password_hash', 'is_admin']

    # Скрываем пароль в списке (он будет виден только при редактировании)
    column_exclude_list = ['password_hash']

    def on_model_change(self, form, model, is_created):
        """Хешируем пароль при создании/изменении пользователя"""
        if is_created or (form.password_hash.data and form.password_hash.data != model.password_hash):
            from werkzeug.security import generate_password_hash
            model.password_hash = generate_password_hash(form.password_hash.data)


class PostModelView(AdminModelView):
    """Представление для модели Post"""

    column_list = ['id', 'title', 'author', 'date', 'tags']
    column_searchable_list = ['title', 'text']
    column_filters = ['date', 'author.name']
    column_editable_list = ['title']
    form_columns = ['title', 'text', 'author', 'tags']

    # Красивое отображение связей
    column_labels = {
        'author': 'Автор',
        'tags': 'Теги'
    }

    form_ajax_refs = {
        'author': {
            'fields': ['name', 'email']
        },
        'tags': {
            'fields': ['name']
        }
    }


class TagModelView(AdminModelView):
    """Представление для модели Tag"""

    column_list = ['id', 'name', 'posts']
    column_searchable_list = ['name']
    column_filters = ['name']
    column_editable_list = ['name']
    form_columns = ['name', 'posts']

    # Красивое отображение
    column_labels = {
        'posts': 'Посты'
    }


def setup_admin(app, database):
    """Функция для настройки и инициализации админки"""

    # Импортируем модели ВНУТРИ функции, чтобы избежать циклического импорта
    from models import User, Post, Tag

    # Создаем экземпляр Flask-Admin
    admin = Admin(
        app,
        name='FH Admin Panel',
        template_mode='bootstrap3',
        url='/admin'
    )

    # Добавляем представления для моделей
    admin.add_view(UserModelView(User, database.session, name='👤 Пользователи', category='Модели'))
    admin.add_view(PostModelView(Post, database.session, name='📝 Посты', category='Модели'))
    admin.add_view(TagModelView(Tag, database.session, name='🏷️ Теги', category='Модели'))

    return admin
