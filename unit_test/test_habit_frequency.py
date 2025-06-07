import pytest
from web import app, db, login_manager
from web.models import User, Habit, Log
from flask import session
from datetime import date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

def create_db_user(username,password):
	'''Добавляем пользователя в БД'''
	db.session.add(User(username=username,
	 password=generate_password_hash(password, method='sha256')))
	db.session.commit()

def login_user(client,username,password):
	data = {
		'username' : username,
		'password' : password
	}

	client.post('/login', data=data)

def test_add_weekly_habit(client,reset_db):
	'''Добавляем еженедельную привычку'''
	assert User.query.first() is None # нет пользователя
	create_db_user('test_user','test_password') # создаем пользователя в БД для теста
	assert len(list(User.query.filter_by(username='test_user'))) == 1 # проверка на добавление пользователя
	login_user(client, 'test_user', 'test_password') # входим с созданным пользователем

	rv = client.post('/add_habit', data={
            'title' : 'title_test',
            'description' : 'description_test',
            'frequency' : 'weekly'})
	habit = Habit.query.filter_by(id=1, title='title_test').first()
	assert habit is not None #
	assert habit.frequency == 'weekly' # привычка имеет правильную регулярность
	assert Log.query.filter_by(id=1).first() is not None # создан лог привычки
	
def test_add_monthly_habit(client,reset_db):
	'''Добавляем ежемесячную привычку'''
	assert User.query.first() is None # нет пользователя
	create_db_user('test_user','test_password') # создаем пользователя в БД для теста
	assert len(list(User.query.filter_by(username='test_user'))) == 1 # проверка на добавление пользователя
	login_user(client, 'test_user', 'test_password') # входим с созданным пользователем

	rv = client.post('/add_habit', data={
            'title' : 'title_test',
            'description' : 'description_test',
            'frequency' : 'monthly'})
	habit = Habit.query.filter_by(id=1, title='title_test').first()
	assert habit is not None
	assert habit.frequency == 'monthly' # привычка имеет правильную регулярность
	assert Log.query.filter_by(id=1).first() is not None # создан лог привычки


def test_date_forward_weekly(client, reset_db):
	create_db_user('test_user', 'test_password')
	login_user(client, 'test_user', 'test_password')
	client.post('/add_habit', data={'title' : 'test_habit',
	 'description' : 'test_description', 'frequency' : 'weekly'}) # создаем привычку

	data = {'increment' : 'next'}
	client.post('/dashboard/{}'.format(date.today()), data=data,
	 follow_redirects=True) # переходим на завтра
	assert len(Log.query.all()) == 1 # 1 лог

	for i in range(1,7): # переходим на следующий день еще 6 раз
		tmrw = date.today() + timedelta(days=i)
		client.post('/dashboard/{}'.format(tmrw), data=data,
		 follow_redirects=True)

	correct_date = date.today() + timedelta(days=7)
	log = Log.query.filter_by(id=2).first() # должен существовать
	assert date.strftime(log.date, '%Y-%m-%d') == date.strftime(
		correct_date, '%Y-%m-%d') # дата лога должна быть через неделю
	assert len(Log.query.all()) == 2 # 2 лога, для этой и следующей недели

def test_date_forward_monthly(client, reset_db):
	create_db_user('test_user', 'test_password')
	login_user(client, 'test_user', 'test_password')
	client.post('/add_habit', data={'title' : 'test_habit',
	 'description' : 'test_description', 'frequency' : 'monthly'}) # создаем привычку

	data = {'increment' : 'next'}
	client.post('/dashboard/{}'.format(date.today()), data=data,
	 follow_redirects=True) # переходим на завтра
	assert len(Log.query.all()) == 1 # 1 лог
	assert Habit.query.all()[0].frequency == 'monthly'
	
	for i in range(1,30): # переходим на следующий день еще 29 раз
		tmrw = date.today() + timedelta(days=i)
		client.post('/dashboard/{}'.format(tmrw), data=data,
		 follow_redirects=True)

	correct_date = date.today() + timedelta(days=30)
	log = Log.query.filter_by(id=2).first() # должне существовать
	assert date.strftime(log.date, '%Y-%m-%d') == date.strftime(
		correct_date, '%Y-%m-%d') # дата лога должна быть через месяц
	assert len(Log.query.all()) == 2 # 2 лога, для этого и следующего месяца

def test_edit_frequency(client,reset_db):
	'''Editing the frequency of a habit is correctly saved in the db'''
	create_db_user('test_user','test_password') # создаем пользователя
	login_user(client, 'test_user', 'test_password')
	client.post('/add_habit', data={'title' : 'test_habit',
	 'description' : 'test_description', 'frequency' : 'daily'}) # создаем привычку

	assert len(db.session.query(Habit, Log).filter(
		Habit.id == Log.habit_id).all()) is 1 # проверяем что создана одна привычка и один лог

	habit = Habit.query.first()
	log = Log.query.first()
	
	data = {
		'frequency' : 'weekly',
	}

	client.post(('/habit/{}/edit'.format(habit.id)), data=data)
	habit = Habit.query.filter_by(title='test_habit').first()
	assert habit.frequency == 'weekly' # регулярность должна была поменяться
	assert habit.last_modified.date() == date.today() # дата последнего изменения должна измениться
	
	#
	# проверяем что логи создаются еженедельно
	#
	
	data = {'increment' : 'next'}
	client.post('/dashboard/{}'.format(date.today()), data=data,
	 follow_redirects=True) # переходим на завтра
	assert len(Log.query.all()) == 1 # 1 лог

	for i in range(1,7): # переходим на следующий день еще 6 раз
		tmrw = date.today() + timedelta(days=i)
		client.post('/dashboard/{}'.format(tmrw), data=data,
		 follow_redirects=True) 

	correct_date = date.today() + timedelta(days=7)
	log = Log.query.filter_by(id=2).first() # должен существовать
	assert date.strftime(log.date, '%Y-%m-%d') == date.strftime(
		correct_date, '%Y-%m-%d') # дата лога должна быть через неделю
	assert len(Log.query.all()) == 2 # 2 лога, для этой и следующей недели