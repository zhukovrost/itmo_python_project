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


@app.route('/dashboard/<current_date>', methods=['GET', 'POST'])
@login_required
def dashboard(current_date):
    if request.method == 'GET':
        habits = Habit.query.filter_by(user_id = current_user.id,
         active=True).filter(Habit.date_created
         <= datetime.strptime(current_date, '%Y-%m-%d')).all()
        if habits:
            for habit in habits:
                if not Log.query.filter_by(habit_id=habit.id,
                 date=datetime.strptime(current_date,
                  '%Y-%m-%d')).first():
                    try:
                        gap = (datetime.strptime(current_date,
                         '%Y-%m-%d').date()
                         - habit.last_modified.date()).days
                        weekly_test =  gap > 0 and gap % 7 == 0
                        monthly_test =  gap > 0 and gap % 30 == 0

                        if ((habit.frequency == 'daily')
                            or (habit.frequency == 'weekly'
                             and weekly_test)
                            or (habit.frequency == 'monthly'
                             and monthly_test)):
                            log = Log(
                                user_id=current_user.id,
                                habit_id=habit.id,
                                date=datetime.strptime(current_date,
                                 '%Y-%m-%d')
                                )
                            db.session.add(log)
                            db.session.commit()

                    except:
                        db.session.rollback()
                        return redirect(url_for('dashboard',
                         current_date=date.today()))

        habit_log_iter = db.session.query(Habit, Log).filter(Habit.id
         == Log.habit_id, Log.date == datetime.strptime(current_date,
          '%Y-%m-%d'), Habit.active == True).filter_by(
            user_id=current_user.id).all()

        # выполненные и предстоящие привычки за день
        count = {
            'completed' : len(db.session.query(Log).filter(
                Log.date == datetime.strptime(current_date,
                 '%Y-%m-%d'), Log.status == True).filter_by(
                    user_id=current_user.id).all()),
            'todo' : len(db.session.query(Log).filter(
                Log.date == datetime.strptime(current_date
                , '%Y-%m-%d'), Log.status == False).filter_by(
                    user_id=current_user.id).all())}
        # выполненные и пропущенные привычки за последние 30 дней
        date1 = datetime.strptime(current_date, '%Y-%m-%d')
        count_month = {
            'completed' : len(db.session.query(Log).filter(
                Log.date == date1, Log.status == True).filter_by(
                    user_id=current_user.id).all()),
            'todo' : len(db.session.query(Log).filter(
                Log.date == date1, Log.status == False).filter_by(
                    user_id=current_user.id).all())
        }
        for i in range (30):
            date1 = date1 - timedelta(days=1)
            count_month['completed'] += len(
                db.session.query(Log).filter(Log.date == date1,
                 Log.status == True).filter_by(
                    user_id=current_user.id).all())
            count_month['todo'] += len(
                db.session.query(Log).filter(Log.date == date1,
                 Log.status == False).filter_by(
                    user_id=current_user.id).all())

        return render_template('dashboard.html',
         user=current_user, date=current_date, habits=habit_log_iter,
          count=count, count_month = count_month)

    if request.method == 'POST':
        current_date = datetime.strptime(current_date, '%Y-%m-%d')
        if request.form.get('increment') == 'previous':
            current_date = current_date - timedelta(days=1)
        elif request.form.get('increment') == 'next':
            current_date = current_date + timedelta(days=1)
        elif request.form.get('increment') == 'today':
            current_date = current_date.today()

        elif request.form.get('done'):
            for checked_off_id in request.form.getlist('done'):
                try:
                    log = Log.query.filter_by(user_id=current_user.id,
                     id=checked_off_id, date=current_date).first()
                    log.status = True

                    db.session.add(log)
                    db.session.commit()

                    try:
                        cur_habit_id = Log.query.filter_by(
                            id=checked_off_id).first().habit_id
                        count_log = len(Log.query.filter_by(
                            user_id=current_user.id,
                             habit_id=cur_habit_id,
                              status=True).all())

                        if count_log in [3,7,14,30,60]:
                            cur_habit_title = Habit.query.filter_by(
                                id = cur_habit_id).first().title
                            flash('Ура! Вы выполнили'
                            +f'"{cur_habit_title}"'
                            +f'{count_log} дней в сумме!')
                            get_milestone = Milestone.query.filter_by(
                                 user_id=current_user.id,
                                 habit_id=cur_habit_id, type='count',
                                 text='Выполните привычку'
                                 + f'{count_log} раз!').first()
                            get_milestone.status=True
                            db.session.commit()

                    except:
                        db.session.rollback()
                        flash("Не получилось проверить ваш прогресс."
                        +"Отмените и отметьте заново?")
                        return redirect(url_for('dashboard',
                         current_date=datetime.strptime(current_date,
                          '%Y-%m-%d')))

                    try:
                        # проверка на выполнение подряд
                        last_logs = Log.query.filter_by(
                            user_id=current_user.id,
                             habit_id = cur_habit_id,
                              status=True).order_by(Log.date.desc())

                        # проверка на регулярность привычки
                        habit_freq = Habit.query.filter_by(
                            user_id=current_user.id,
                             id=cur_habit_id).first().frequency

                        freq_to_days = {'daily': 1, 'weekly':7,
                         'monthly': 30}

                        for n in [3,7,14,30,60]:
                            count_logs = 1
                            for i in range(1,n):
                                date_to_check = current_date - timedelta(
                                    days= i*freq_to_days[habit_freq])
                                if date_to_check in [log.date for log
                                 in last_logs]:
                                    count_logs += 1

                            if count_logs == n:
                                flash("Отлично! Вы выполнили "
                                +f"'{cur_habit_title}'"
                                +f" {n} раз подряд!")
                                get_streak_milestone = Milestone.query.filter_by(
                                    user_id=current_user.id,
                                     habit_id=cur_habit_id,
                                      type='streak',
                                       text='Выполнить привычку'
                                       +f' {n} раз подряд!').first()
                                get_streak_milestone.status=True
                                db.session.commit()

                    except:
                        flash("Не получилось отследить"
                        +" ваш прогресс по этой привычке."
                        + "Попробуйте еще раз?")
                        return redirect(url_for('dashboard',
                         current_date=datetime.strptime(current_date,
                          '%Y-%m-%d')))


                except:
                    db.session.rollback()
                    flash('Не получилось отметить привычку '
                    +'как выполненную. Попробуйте еще раз')
                    return redirect(url_for('dashboard',
                     current_date=date.today()))



        elif request.form.get('undo-done'):
            for checked_off_id in request.form.getlist('undo-done'):
                try:
                    log = Log.query.filter_by(user_id=current_user.id,
                     id=checked_off_id).filter(
                        Log.date.like(current_date)).first()
                    log.status = False
                    db.session.add(log)
                    db.session.commit()
                except:
                    db.session.rollback()
                    flash('Не получилось отменить выполнение. '
                    +'Попробуйте еще раз')
                    return redirect(url_for('dashboard',
                     current_date=date.today()))

        return redirect(url_for('dashboard',
         current_date=datetime.strftime(current_date,
          '%Y-%m-%d')))

@app.route('/add_habit', methods=['GET', 'POST'])
@login_required
def add_habit():
    if request.method == 'GET':
        habits = Habit.query.filter_by(user_id=current_user.id,
         active=True)
        return render_template('add_habit.html', habits=habits,
         user=current_user)
    elif request.method == 'POST':

        try:
            #adds a habit
            habit = Habit(
                user_id=current_user.id,
                title=request.form.get('title'),
                description=request.form.get('description'),
                frequency=request.form.get('frequency'),
                date_created=datetime.today(),
                active=True
            )

            db.session.add(habit)
            db.session.flush() #staging

            log = Log(
                user_id=current_user.id,
                habit_id=habit.id,
                date=date.today()
            )

            db.session.add(log)

            form = request.form.to_dict()
            new_milestone_counter = 0
            while ('new_milestone_text_' + str(
                new_milestone_counter)) in form.keys():
                if form['new_milestone_text_' + str(
                    new_milestone_counter)]:
                    deadline = None
                    if 'new_milestone_deadline_' + str(
                        new_milestone_counter) in form.keys():
                        deadline = datetime.strptime(
                            form['new_milestone_deadline_' + str(
                                new_milestone_counter)], '%Y-%m-%d')
                    if deadline and deadline.date() < datetime.now(
                    ).date():
                        flash('Срок не может быть в прошлом')
                        return redirect(url_for('add_habit'))
                    else:
                        milestone = Milestone(
                            user_id = current_user.id,
                            habit_id = habit.id,
                            text = form['new_milestone_text_' + str(
                                new_milestone_counter)],
                            deadline = deadline)
                        db.session.add(milestone)
                new_milestone_counter += 1

            for n in [3,7,14,30,60]:
                iteration_milestone = Milestone(
                    user_id=current_user.id,
                 habit_id=habit.id, type='count',
                  text=f'Выполнено {n} раз!')
                db.session.add(iteration_milestone)

            for n in [3,7,14,30,60]:
                streak_milestone = Milestone(user_id=current_user.id,
                 habit_id=habit.id, type='streak',
                  text=f'Выполнено {n} раз подряд!')
                db.session.add(streak_milestone)

            db.session.commit()
        except:
            db.session.rollback()
            flash('Возникла ошибка при загрузке. Попробуйте снова.')
            return redirect(url_for('add_habit'))

        return redirect(url_for('dashboard',
         current_date=date.today()))

@app.route('/habit/<habit_id>')
@login_required
def habit(habit_id):
    habits = Habit.query.filter_by(
        user_id=current_user.id, active=True)
    habit = Habit.query.filter_by(
        id=habit_id, user_id=current_user.id).first()
    milestones = Milestone.query.filter_by(
        habit_id=habit_id, user_id=current_user.id).all()
    return render_template('habit.html', habits=habits,
     habit=habit, milestones=milestones)

@app.route('/habit/<habit_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_habit(habit_id):
    habit = Habit.query.filter_by(id=habit_id,
     user_id=current_user.id).first()
    if request.method == 'GET':
        habits = Habit.query.filter_by(user_id=current_user.id,
         active=True)
        milestones = Milestone.query.filter_by(habit_id=habit_id,
         user_id=current_user.id, type='custom').all()
        return render_template('edit_habit.html', habits=habits,
         milestones = milestones, habit=habit)
    elif request.method == 'POST':
        form = request.form.to_dict()
        if 'archive' in form.keys():
            habit.active = False
            try:
                db.session.add(habit)
                db.session.commit()
            except:
                db.session.rollback()
                flash('Возникла ошибка. Попробуйте еще раз')
                return redirect(url_for('habit', habit_id=habit.id))

            return redirect(url_for('habit', habit_id=habit.id))

        elif 'unarchive' in form.keys():
            habit.active = True
            try:
                db.session.add(habit)
                db.session.commit()
            except:
                db.session.rollback()
                flash('Возникла ошибка. Попробуйте еще раз.')
                return redirect(url_for('habit', habit_id=habit.id))


            return redirect(url_for('habit', habit_id=habit.id))

        elif 'delete' in form.keys():
            Log.query.filter_by(habit_id=habit.id).delete()
            Milestone.query.filter_by(habit_id=habit.id).delete()
            try:
                db.session.delete(habit)
                db.session.commit()
            except:
                db.session.rollback()
                flash('Возникла ошибка при удалении привычки.'
                +' Попробуйте еще раз (а, может это знак?).')
                return redirect(url_for('habit', habit_id=habit.id))


            return redirect(url_for('dashboard',
             current_date=date.today()))

        elif 'title' in form.keys() or 'description' in form.keys(
        ) or 'frequency' in form.keys(
        ) or 'new_milestone_text_0' in form.keys0():
            try:
                if 'title' in form.keys():
                    habit.title = form['title']
                if 'description' in form.keys():
                    habit.description = form['description']
                if 'frequency' in form.keys():
                    habit.frequency = form['frequency']

                habit.last_modified = datetime.today()

                milestones = Milestone.query.filter_by(
                    habit_id=habit_id, user_id=current_user.id,
                     type='custom').all()

                for milestone in milestones:
                    if ('milestone_text_' + str(
                        milestone.id)) in form.keys():
                        deadline = None
                        if ('milestone_deadline_' + str(
                            milestone.id)) in form.keys():
                            deadline = datetime.strptime(
                                form['milestone_deadline_' + str(
                                    milestone.id)], '%Y-%m-%d')

                        milestone.text = form['milestone_text_' + str(
                            milestone.id)]
                        milestone.deadline = deadline

                new_milestone_counter = 0
                while ('new_milestone_text_' + str(
                    new_milestone_counter)) in form.keys():
                    deadline = None
                    if ('new_milestone_deadline_' + str(
                        new_milestone_counter)) in form.keys(
                        ) and form['new_milestone_deadline_' + str(
                            new_milestone_counter)]:
                        print('haha',
                        form['new_milestone_deadline_' + str(
                            new_milestone_counter)])
                        deadline = datetime.strptime(
                            form['new_milestone_deadline_' + str(
                                new_milestone_counter)], '%Y-%m-%d')
                    if deadline and deadline.date() < datetime.now(
                    ).date():
                        flash('Срок не может быть в прошлом!')
                        return redirect(url_for('add_habit'))
                    else:
                        milestone = Milestone(
                            user_id = current_user.id,
                            habit_id = habit.id,
                            text = form['new_milestone_text_' + str(
                                new_milestone_counter)],
                            deadline = deadline)
                        db.session.add(milestone)
                    new_milestone_counter += 1

                db.session.add(habit)
                db.session.commit()
            except:
                db.session.rollback()

            return redirect(url_for('habit', habit_id=habit.id))

@app.route('/archive')
@login_required
def archive():
    habits = Habit.query.filter_by(user_id=current_user.id,
     active=False).all()
    return render_template("archive.html", habits=habits)

@app.route('/active_habits')
@login_required
def active_habits():
    habits = Habit.query.filter_by(user_id=current_user.id,
     active=True).all()
    return render_template("active_habits.html", habits=habits)


if __name__ == '__main__':
    app.run()
