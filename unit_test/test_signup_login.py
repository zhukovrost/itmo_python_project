from werkzeug.security import generate_password_hash, check_password_hash
import pytest
from web import app, db, login_manager
from web.models import User, Habit, Log
from flask import session
from flask_login import current_user

def create_user(username,password):
	'''Возвращает объект User для теста'''
	return User(username=username,
	 password=generate_password_hash(password, method='sha256'))


def test_empty_db(client):
	"""Пустая база данных"""

	rv = client.get('/login')
	assert rv.status_code == 200
	assert User.query.first() is None # в БД нет пользователей
	assert Habit.query.first() is None # в БД нет привычек
	assert Log.query.first() is None


def test_signup(client, reset_db):
	'''Успешно регистрируем пользователя'''
	assert client.get("/signup").status_code == 200 # страница регистрации загрузилась
	
	# регистрация
	rv = client.post("/signup", data={"username": "test_user",
	 "password": "test_password"})
	
	assert rv.status_code == 302 # регистрация успешна
	assert rv.location == 'http://localhost/login' # пользователь должен быть перенаправлен на страницу входа
	assert User.query.filter_by(
		username="test_user").first() is not None # пользователь добавлен в БД
	

def test_signup_existing_username_failure(client, reset_db):
	'''Регистрация не должна пройти если в БД уже есть такое имя пользователя'''
	new_user = create_user(username='test_user',
	 password='test_password') 
	db.session.add(new_user) # добавляем тестового пользователя в БД
	db.session.commit()
	rv = client.post("/signup", data={"username": "test_user",
	 "password": "test_password"}, follow_redirects=True)
	# assert b'Такой пользователь уже есть' in rv.data # пользователь получает сообщение об ошибке
	assert len(list(User.query.filter_by(username='test_user'))) == 1 # пользователь не был зарегестрирован дважды


def test_signup_empty_username_failure(client, reset_db):
	'''Регистрация не должна пройти с пустым именем пользователя'''
	rv = client.post("/signup", data={"username": "",
	 "password": "a"}, follow_redirects=True)
	# assert b'Пожалуйста, введите имя пользователя' in rv.data # пользователь получает сообщение об ошибке
	assert len(list(User.query.filter_by(username=''))) == 0 # пользователь не был зарегестрирован


def test_signup_empty_password_failure(client, reset_db):
	'''Регистрация не должна пройти с пустым паролем'''
	rv = client.post("/signup", data={"username": "test_user",
	 "password": ""}, follow_redirects=True)
	# assert b'Пожалуйста, введите пароль' in rv.data # пользователь получает сообщение об ошибке
	assert len(list(User.query.filter_by(username='test_user'))) == 0 # пользователь не был зарегестрирован

	
def test_login_logout(client, reset_db):
	'''Пользователь с корректными данными может войти и выйти'''
	assert client.get("/login").status_code == 200 # страница входа загрузилась
	assert User.query.first() is None # проверка на то, что БД - пустая
	new_user = create_user(username='test_user',
	 password='test_password') # создание тестового объекта User
	db.session.add(new_user) # добавляем пользователя в БД
	db.session.commit()
	assert len(list(User.query.filter_by(username='test_user'))) == 1 # пользователь был добавлен в БД
	rv = client.post('/login', data={'username': 'test_user',
	 'password': 'test_password'}) # вход с данными пользователя
	#assert rv.location == 'http://localhost/dashboard' # пользователь должен быть перенаправлен на панель управления
	assert current_user.is_authenticated  # логин менеджер должен определить аутентифицированного пользователя
	assert current_user.id == 1 # логин менеджер должен показать что пользователь имеет id = 1 
	
	rv = client.get('/logout') # выходим
	assert rv.location == 'http://localhost/login' # пользователь должен быть перенаправлен на страницу входа
	assert not current_user.is_authenticated  # логин менеджер не должен показывать аутентифицированных пользователей


def test_alphnum_login_logout(client, reset_db):
	'''Пользователь с корректными буквенно-цифровыми данными может войти и выйти'''
	assert client.get("/login").status_code == 200 # страница входа загрузилась
	assert User.query.first() is None # проверка на то, что БД - пустая
	new_user = create_user(username='test123', password='test123') # создание тестового объекта User
	db.session.add(new_user) # добавляем пользователя в БД
	db.session.commit()
	assert len(list(User.query.filter_by(username='test123'))) == 1 # пользователь был добавлен в БД
	rv = client.post('/login', data={'username': 'test123',
	 'password': 'test123'}) # вход с данными пользователя
	#assert rv.location == 'http://localhost/dashboard' # пользователь должен быть перенаправлен на панель управления
	assert current_user.is_authenticated  # логин менеджер должен определить аутентифицированного пользователя
	assert current_user.id == 1 # логин менеджер должен показать что пользователь имеет id = 1 
	
	rv = client.get('/logout') # выходим
	assert rv.location == 'http://localhost/login' # пользователь должен быть перенаправлен на страницу входа
	assert not current_user.is_authenticated  # логин менеджер не должен показывать аутентифицированных пользователей


def test_login_failure(client, reset_db):
	'''Пользователь не может войти с неправильным паролем или именем пользователя'''
	new_user = create_user(username='a', password='a') # создание тестового объекта User
	db.session.add(new_user) # добавляем пользователя в БД
	db.session.commit()
	assert len(list(User.query.filter_by(username='a'))) == 1 # пользователь был добавлен в БД
	
	# Неправильный пароль
	rv = client.post('/login', data={'username': 'a', 'password': 'b'},
	 follow_redirects=True) # входим с неправильным паролем
	# assert b'Неверный пароль' in rv.data # пользователю будет показано сообщение об ошибке
	assert not current_user.is_authenticated  # логин менеджер не должен показывать аутентифицированных пользователей
	
	# Несуществующее имя пользователя
	rv = client.post('/login', data={'username': 'b', 'password': 'a'},
	 follow_redirects=True) # входим с несуществующим именем пользователя
	# assert b'Такого пользователя не существует' in rv.data # пользователю будет показано сообщение об ошибке
	assert not current_user.is_authenticated  # логин менеджер не должен показывать аутентифицированных пользователей
