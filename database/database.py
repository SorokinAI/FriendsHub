import psycopg2
from config import host, user, password, db_name

try:
    # Подключение к бд
    connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        database=db_name
    )

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT version();"
        )
        print(cursor.fetchone())


except Exception as _ex:
    print('[INFO] Error while working with PostgreSQL', _ex)
finally:
    if connection:
        connection.close()
        print('[INFO] PostgreSQL connection closed')
