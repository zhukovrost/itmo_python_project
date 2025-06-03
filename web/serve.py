from datetime import datetime, date, timedelta
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from web import app, db
from .models import User, Habit, Log, Milestone

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == '':
            flash('Пожалуйста, введите имя пользователя')
            return redirect(url_for('signup'))

        if password == '':
            flash('Пожалуйста, введите пароль')
            return redirect(url_for('signup'))

        user = User.query.filter_by(username=username).first()
        # проверяет есть ли такой пользователь

        if user:
            flash('Такой пользователь уже есть')
            return redirect(url_for('signup'))

        # создает нового пользователя
        try:
            new_user = User(username=username,
             password=generate_password_hash(password,
              method='sha256'))
            # добавляет пользователя в базу данных
            db.session.add(new_user)
            db.session.commit()
        except:
            db.session.rollback()
            flash('Что-то помешло регистрации. Попробуйте еще раз')
            return redirect(url_for('signup'))

        return redirect(url_for('login'))

@app.route('/')
def home():
    return redirect(url_for('dashboard', current_date=date.today()))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(username=username).first()

        # проверяет существует ли пользователь
        if not user:
            flash('Такого пользователя не существует')
            return redirect(url_for('login'))
        if not check_password_hash(user.password, password):
            flash('Неверный пароль')
            return redirect(url_for('login'))

        login_user(user, remember=remember)
        return redirect(url_for('dashboard', current_date=date.today()))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run()
