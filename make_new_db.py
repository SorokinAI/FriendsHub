"""
Скрипт для полного пересоздания базы данных
ВНИМАНИЕ: Удалит все существующие данные!
"""

from app import app
from models import db, User


def recreate_database():
    with app.app_context():
        print("🗑️  Удаляем старую базу данных...")

        # Удаляем все таблицы
        db.drop_all()

        print("✅ Старые таблицы удалены")
        print("🔄 Создаем новые таблицы...")

        # Создаем все таблицы заново
        db.create_all()

        print("✅ Новые таблицы созданы")
        print("👤 Создаем тестового администратора...")

        # Все данные админа
        admin_email = 'as8571474@yandex.ru'
        admin_name = 'Арсений'
        admin_surname = 'Сорокин'
        admin_tg = '@ArseniiSorokin'
        admin_password = 'qwerty1234'

        # Создаем нового админа
        admin_user = User(
            name=admin_name,
            surname=admin_surname,
            email=admin_email,
            telegram_username=admin_tg,
            is_admin=True
        )
        admin_user.set_password(admin_password)

        db.session.add(admin_user)
        db.session.commit()

        print("✅ Администратор создан:")
        print(f"   Email: {admin_email}")
        print(f"   Пароль: {admin_password}")
        print(f"   Фамилия, Имя: {admin_surname} {admin_name}")
        print(f"   Telegram: {admin_tg}")

        print("\n🎉 База данных успешно пересоздана!")


if __name__ == '__main__':
    recreate_database()
