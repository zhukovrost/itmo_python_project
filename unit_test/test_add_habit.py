import pytest
from web import app, db, login_manager
from web.models import User, Habit, Log
from flask import session
from datetime import date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

def create_db_user(username,password):
	'''Добавляет тестового пользователя в БД'''
	db.session.add(User(username=username,
	 password=generate_password_hash(password, method='sha256')))
	db.session.commit()

def login_user(client,username,password):
	data = {
		'username' : username,
		'password' : password
	}

	client.post('/login', data=data)

def test_add_habit(client,reset_db):
	'''Добавление привычки не происходит без входа. После входа успешно добавляется привычка и лог'''
	assert User.query.first() is None # нет пользователя
	create_db_user('test_user','test_password') # создание пользователя БД для теста
	assert len(list(User.query.filter_by(username='test_user'))) == 1 # проверка на добавление

	# добавляем привычку без входа
	rv = client.post('/add_habit', data={
            'title' : 'title_test',
            'description' : 'description_test',
            'frequency' : 'daily'})
	assert Habit.query.filter_by(id=1,
	 title='title_test').first() is None

	# входим и пробуем еще раз
	login_user(client, 'test_user', 'test_password') # входим с созданным пользователем
	rv = client.post('/add_habit', data={
            'title' : 'title_test',
            'description' : 'description_test',
            'frequency' : 'daily'})
	assert Habit.query.filter_by(id=1,
	 title='title_test').first() is not None
	assert Log.query.filter_by(id=1).first() is not None

def test_edit_habit(client,reset_db):
	'''Изменяем привычку'''
	create_db_user('test_user','test_password') # создаем пользователя
	login_user(client, 'test_user', 'test_password')
	client.post('/add_habit', data={'title' : 'test_habit',
	 'description' : 'test_description', 'frequency' : 'daily'}) # создаем привычку

	assert len(db.session.query(Habit, Log).filter(
		Habit.id == Log.habit_id).all()) is 1 # проверяем что создалась одна привычка и один лог

	habit = Habit.query.first()
	log = Log.query.first()

	client.get('/logout')

	data = {
		'title' : 'test_title_edit',
		'description' : 'test_description_edit',
		'frequency' : 'daily'
	}

	client.post(('/habit/{}/edit'.format(habit.id)), data=data)
	assert Habit.query.filter_by(
		title='test_title_edit').first() is None # title не должен меняться

	login_user(client, 'test_user', 'test_password')

	client.post(('/habit/{}/edit'.format(habit.id)), data=data)
	assert Habit.query.filter_by(
		title='test_title_edit').first() is not None # title должен измениться

def test_delete_habit(client,reset_db):
	'''Удаляем привычку'''
	create_db_user('test_user','test_password') # создаем пользователя
	login_user(client, 'test_user', 'test_password')
	client.post('/add_habit', data={'title' : 'test_habit',
	 'description' : 'test_description', 'frequency' : 'daily'}) # создаем привычку

	habit = Habit.query.first()
	log = Log.query.first()

	data = {
		'delete' : 'delete'
	}

	client.post('/habit/{}/edit'.format(habit.id), data=data)
	assert Habit.query.first() is None and Log.query.first() is None # delete должно удалить и привычку и лог

def test_archive_habit(client,reset_db):
	'''Архивируем / Разархивируем привычку'''
	create_db_user('test_user', 'test_password')
	login_user(client, 'test_user', 'test_password')
	client.post('/add_habit', data={'title' : 'test_habit',
	 'description' : 'test_description', 'frequency' : 'daily'}) # создаем привычку

	habit = Habit.query.first()
	log = Log.query.first()

	data = {
		'archive' : 'archive'
	}

	client.post('/habit/{}/edit'.format(habit.id), data=data)
	assert Habit.query.filter_by(active=False).first() is not None # привычка должна архивироваться

	data = {
		'unarchive' : 'unarchive'
	}

	client.post('/habit/{}/edit'.format(habit.id), data=data)
	assert Habit.query.filter_by(active=True).first() is not None # привычка должна разархивироваться

def test_date_forward(client, reset_db):
	'''Перемещение даты вперед'''
	create_db_user('test_user', 'test_password')
	login_user(client, 'test_user', 'test_password')
	client.post('/add_habit', data={'title' : 'test_habit',
	 'description' : 'test_description', 'frequency' : 'daily'}) # создание привычки

	today = date.today()

	data = {
		'increment' : 'previous'
	}

	client.post('/dashboard/{}'.format(today), data=data,
	 follow_redirects=True)

	assert len(Log.query.all()) == 1

	data = {
		'increment' : 'next'
	}

	client.post('/dashboard/{}'.format(today), data=data,
	 follow_redirects=True)

	tmrw = date.today() + timedelta(days=1)

	log = Log.query.filter_by(id=2).first()

	assert date.strftime(log.date, '%Y-%m-%d') == date.strftime(
		tmrw, '%Y-%m-%d') # дата лога соответствует завтрашней дате

	assert len(Log.query.all()) == 2 # должно быть 2 лога - сегодняшняя и завтрашняя дата
