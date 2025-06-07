import pytest
from web import app, db, login_manager
from web.models import User, Milestone, Log, Habit
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
from flask_login import current_user

def create_user():
    '''Создает тестового пользователя в БД'''
    db.session.add(User(username='test_user',
     password=generate_password_hash('test_password', method='sha256')))
    db.session.commit()

def test_add_milestone_no_deadline(client,reset_db):
    '''Добавляет этап без дедлайна'''
    # добавление пользователя в БД
    create_user()
    assert len(list(User.query.filter_by(username='test_user'))) == 1 # проверка на добавление пользователя

    # создание привычки с этапом без входа не работает
    rv = client.post('/add_habit', data={
            'title' : 'title_test',
            'description' : 'description_test',
            'frequency' : 'daily',
            'new_milestone_text_0': 'test_mile',
            'new_milestone_type_0': 'count',
            'new_milestone_deadline_0': None})
    assert Milestone.query.filter_by(habit_id=1, text='test_mile').first() is None

    client.post('/login', data={'username': 'test_user',
     'password': 'test_password'}) # вход с созданным пользователем
    assert current_user.id == 1

    # создание этапа
    rv = client.post('/add_habit', data={
            'title' : 'title_test',
            'description' : 'description_test',
            'frequency' : 'daily',
            'new_milestone_text_0': 'test_mile',
            'new_milestone_type_0': 'count',
            'new_milestone_deadline_0': None})

    m = Milestone.query.filter_by(habit_id=1, text='test_mile').first()
    assert m.text == 'test_mile' # этап должен быть добавлен с правильным описанием
    assert m.habit_id == 1 # для верной привычки
    assert m.user_id == 1 # и пользователя
    assert m.deadline == None # дедлайн не поставлен


def test_set_milestone_past(client,reset_db):
    '''Создание этапа с дедлайном в прошлом не должно работать'''
    ### В начале пробуем при создании привычки с нуля

    # добавляем пользователя и привычку в БД
    create_user()

    # входим
    client.post('/login', data={'username': 'test_user',
     'password': 'test_password'}) # входим с созданным пользователем
    assert current_user.id == 1

    # добавляем этап вчера
    deadline = datetime.strftime((datetime.now() - timedelta(days=1)),
    '%Y-%m-%d')
    rv = client.post('/add_habit', data={
            'title' : 'title_test',
            'description' : 'description_test',
            'frequency' : 'daily',
            'new_milestone_text_0': 'test_from_edit',
            'new_milestone_type_0': 'count',
            'new_milestone_deadline_0': deadline}, follow_redirects=True)

    m = Milestone.query.filter_by(habit_id=1).first()
    h = Habit.query.filter_by(title='title_test').first()
    assert m is None # этап не был добавлен
    assert h is None # привычка не была добавлена

    # создаем привычку без этапов
    rv = client.post('/add_habit', data={'title' : 'title_test',
    'description' : 'description_test','frequency' : 'daily'})
    m = Milestone.query.filter_by(habit_id=1, type='custom').first()
    assert m is None # на этот момент не должно быть этапов

    # пробуем добавить для привычки этап в прошлом
    rv = client.post('/habit/1/edit', data={
        'new_milestone_text_0': 'test_from_edit',
        'new_milestone_type_0': 'count',
        'new_milestone_deadline_0': '2020-01-01'}
    , follow_redirects=True)
    m = Milestone.query.filter_by(habit_id=1,
     text='test_from_edit').first()
    assert m is None # не должно работать т.к. дедлайн в прошлом
