"""Файл для разработчика!
   Необходим для создания базы данных.
"""
from index import db, app
app.app_context().push()
db.create_all()