from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from config import Config
from models import db, User, Subject, Task, StudySession, Goal
from datetime import datetime, date, timedelta
from sqlalchemy import func
import json

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# ─── Flask-Login ───────────────────────────────────────────────────────────────
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access StudyFlow.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ─── Auth Routes ───────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.name}! 👋', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        flash('Invalid email or password.', 'error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        if not name or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('register.html')
        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists.', 'error')
            return render_template('register.html')

        # Compute initials
        parts    = name.split()
        initials = (parts[0][0] + (parts[-1][0] if len(parts) > 1 else '')).upper()

        user = User(name=name, email=email, avatar_initials=initials)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash(f'Account created! Welcome to StudyFlow, {name}! 🎉', 'success')
        return redirect(url_for('dashboard'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))




# ─── Dashboard ─────────────────────────────────────────────────────────────────
@app.route('/')
@login_required
def dashboard():
    uid   = current_user.id
    today = date.today()

    total_tasks     = Task.query.filter_by(user_id=uid).count()
    completed_tasks = Task.query.filter_by(user_id=uid, status='completed').count()
    pending_tasks   = Task.query.filter_by(user_id=uid, status='pending').count()
    in_progress     = Task.query.filter_by(user_id=uid, status='in_progress').count()
    overdue_tasks   = Task.query.filter(Task.user_id==uid, Task.due_date < today, Task.status != 'completed').count()

    due_today    = Task.query.filter(Task.user_id==uid, Task.due_date==today,   Task.status != 'completed').all()
    recent_tasks = Task.query.filter_by(user_id=uid).order_by(Task.created_at.desc()).limit(5).all()

    week_ago        = today - timedelta(days=7)
    week_sessions   = StudySession.query.filter(StudySession.user_id==uid, StudySession.date >= week_ago).all()
    total_week_mins = sum(s.duration_minutes for s in week_sessions)
    today_mins      = sum(s.duration_minutes for s in StudySession.query.filter_by(user_id=uid, date=today).all())

    subjects = Subject.query.filter_by(user_id=uid).all()
    goals    = Goal.query.filter_by(user_id=uid, status='active').limit(4).all()

    daily_labels, daily_minutes = [], []
    for i in range(6, -1, -1):
        d    = today - timedelta(days=i)
        mins = db.session.query(func.sum(StudySession.duration_minutes)).filter(
            StudySession.user_id==uid, StudySession.date==d).scalar() or 0
        daily_labels.append(d.strftime('%a'))
        daily_minutes.append(round(mins / 60, 2))

    subj_data = []
    for s in subjects:
        total_mins = db.session.query(func.sum(StudySession.duration_minutes)).filter(
            StudySession.user_id==uid, StudySession.subject_id==s.id).scalar() or 0
        if total_mins > 0:
            subj_data.append({'name': s.name, 'hours': round(total_mins/60, 1), 'color': s.color})

    completion_rate = round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1)

    return render_template('dashboard.html',
        total_tasks=total_tasks, completed_tasks=completed_tasks,
        pending_tasks=pending_tasks, in_progress_tasks=in_progress,
        overdue_tasks=overdue_tasks, due_today=due_today, recent_tasks=recent_tasks,
        total_week_hours=round(total_week_mins/60, 1), today_hours=round(today_mins/60, 1),
        subjects=subjects, goals=goals,
        daily_labels=json.dumps(daily_labels), daily_minutes=json.dumps(daily_minutes),
        subj_data=json.dumps(subj_data), completion_rate=completion_rate, today=today)


# ─── Tasks ─────────────────────────────────────────────────────────────────────
@app.route('/tasks')
@login_required
def tasks():
    uid             = current_user.id
    status_filter   = request.args.get('status', 'all')
    subject_filter  = request.args.get('subject', 'all')
    priority_filter = request.args.get('priority', 'all')

    q = Task.query.filter_by(user_id=uid)
    if status_filter   != 'all': q = q.filter_by(status=status_filter)
    if subject_filter  != 'all': q = q.filter_by(subject_id=int(subject_filter))
    if priority_filter != 'all': q = q.filter_by(priority=priority_filter)

    all_tasks = q.order_by(Task.due_date.asc()).all()
    subjects  = Subject.query.filter_by(user_id=uid).all()
    return render_template('tasks.html', tasks=all_tasks, subjects=subjects,
                           status_filter=status_filter, subject_filter=subject_filter,
                           priority_filter=priority_filter, today=date.today())


@app.route('/tasks/add', methods=['POST'])
@login_required
def add_task():
    title = request.form.get('title', '').strip()
    if not title:
        flash('Task title is required.', 'error')
        return redirect(url_for('tasks'))
    due_str  = request.form.get('due_date', '')
    due_date = datetime.strptime(due_str, '%Y-%m-%d').date() if due_str else None
    subj_id  = request.form.get('subject_id')
    task = Task(user_id=current_user.id, title=title,
                description=request.form.get('description', ''),
                subject_id=int(subj_id) if subj_id else None,
                priority=request.form.get('priority', 'medium'),
                status='pending', due_date=due_date)
    db.session.add(task)
    db.session.commit()
    flash('Task added successfully!', 'success')
    return redirect(url_for('tasks'))


@app.route('/tasks/update_status/<int:task_id>', methods=['POST'])
@login_required
def update_task_status(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    task.status = request.form.get('status')
    if task.status == 'completed':
        task.completed_at = datetime.utcnow()
    db.session.commit()
    return redirect(request.referrer or url_for('tasks'))


@app.route('/tasks/edit/<int:task_id>', methods=['POST'])
@login_required
def edit_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    title = request.form.get('title', '').strip()
    if not title:
        flash('Task title is required.', 'error')
        return redirect(url_for('tasks'))
    due_str  = request.form.get('due_date', '')
    due_date = datetime.strptime(due_str, '%Y-%m-%d').date() if due_str else None
    subj_id  = request.form.get('subject_id')
    task.title       = title
    task.description = request.form.get('description', '')
    task.priority    = request.form.get('priority', 'medium')
    task.status      = request.form.get('status', task.status)
    task.due_date    = due_date
    task.subject_id  = int(subj_id) if subj_id else None
    if task.status == 'completed' and not task.completed_at:
        task.completed_at = datetime.utcnow()
    db.session.commit()
    flash('Task updated successfully!', 'success')
    return redirect(url_for('tasks'))


@app.route('/tasks/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted.', 'info')
    return redirect(url_for('tasks'))


# ─── Subjects ──────────────────────────────────────────────────────────────────
@app.route('/subjects')
@login_required
def subjects():
    uid  = current_user.id
    stats = []
    for s in Subject.query.filter_by(user_id=uid).all():
        total     = len(s.tasks)
        completed = sum(1 for t in s.tasks if t.status == 'completed')
        mins      = sum(ss.duration_minutes for ss in s.sessions)
        stats.append({'subject': s, 'total_tasks': total, 'completed_tasks': completed,
                      'pending_tasks': total - completed,
                      'total_hours': round(mins/60, 1),
                      'completion_rate': round((completed/total*100) if total > 0 else 0, 1)})
    return render_template('subjects.html', subject_stats=stats)


@app.route('/subjects/add', methods=['POST'])
@login_required
def add_subject():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Subject name is required.', 'error')
        return redirect(url_for('subjects'))
    db.session.add(Subject(user_id=current_user.id, name=name,
                           color=request.form.get('color', '#6366f1'),
                           description=request.form.get('description', ''),
                           target_hours=float(request.form.get('target_hours', 0))))
    db.session.commit()
    flash(f'Subject "{name}" added!', 'success')
    return redirect(url_for('subjects'))


@app.route('/subjects/delete/<int:subject_id>', methods=['POST'])
@login_required
def delete_subject(subject_id):
    subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first_or_404()
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted.', 'info')
    return redirect(url_for('subjects'))


# ─── Study Sessions ────────────────────────────────────────────────────────────
@app.route('/sessions')
@login_required
def sessions():
    uid = current_user.id
    return render_template('sessions.html',
        sessions=StudySession.query.filter_by(user_id=uid).order_by(StudySession.date.desc()).all(),
        subjects=Subject.query.filter_by(user_id=uid).all(), today=date.today())


@app.route('/sessions/add', methods=['POST'])
@login_required
def add_session():
    date_str = request.form.get('date', '')
    s_date   = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
    subj_id  = request.form.get('subject_id')
    db.session.add(StudySession(user_id=current_user.id,
                                subject_id=int(subj_id) if subj_id else None,
                                date=s_date,
                                duration_minutes=int(request.form.get('duration_minutes', 0)),
                                notes=request.form.get('notes', ''),
                                productivity_rating=int(request.form.get('productivity_rating', 3))))
    db.session.commit()
    flash('Study session logged!', 'success')
    return redirect(url_for('sessions'))


@app.route('/sessions/delete/<int:session_id>', methods=['POST'])
@login_required
def delete_session(session_id):
    s = StudySession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
    db.session.delete(s)
    db.session.commit()
    flash('Session deleted.', 'info')
    return redirect(url_for('sessions'))


# ─── Analytics ─────────────────────────────────────────────────────────────────
@app.route('/analytics')
@login_required
def analytics():
    uid   = current_user.id
    today = date.today()
    subjects = Subject.query.filter_by(user_id=uid).all()

    labels_30, minutes_30 = [], []
    for i in range(29, -1, -1):
        d    = today - timedelta(days=i)
        mins = db.session.query(func.sum(StudySession.duration_minutes)).filter(
            StudySession.user_id==uid, StudySession.date==d).scalar() or 0
        labels_30.append(d.strftime('%b %d'))
        minutes_30.append(round(mins/60, 2))

    subj_names, subj_hours, subj_colors = [], [], []
    task_subj_labels, task_completed_list, task_pending_list = [], [], []
    for s in subjects:
        mins = db.session.query(func.sum(StudySession.duration_minutes)).filter(
            StudySession.user_id==uid, StudySession.subject_id==s.id).scalar() or 0
        subj_names.append(s.name); subj_hours.append(round(mins/60, 1)); subj_colors.append(s.color)
        task_subj_labels.append(s.name)
        task_completed_list.append(sum(1 for t in s.tasks if t.status == 'completed'))
        task_pending_list.append(sum(1 for t in s.tasks if t.status != 'completed'))

    prod_labels, prod_ratings = [], []
    for i in range(13, -1, -1):
        d   = today - timedelta(days=i)
        avg = db.session.query(func.avg(StudySession.productivity_rating)).filter(
            StudySession.user_id==uid, StudySession.date==d).scalar()
        prod_labels.append(d.strftime('%b %d'))
        prod_ratings.append(round(float(avg), 2) if avg else 0)

    total_mins      = db.session.query(func.sum(StudySession.duration_minutes)).filter_by(user_id=uid).scalar() or 0
    total_tasks     = Task.query.filter_by(user_id=uid).count()
    completed_tasks = Task.query.filter_by(user_id=uid, status='completed').count()

    return render_template('analytics.html',
        labels_30=json.dumps(labels_30), minutes_30=json.dumps(minutes_30),
        subj_names=json.dumps(subj_names), subj_hours=json.dumps(subj_hours), subj_colors=json.dumps(subj_colors),
        task_subj_labels=json.dumps(task_subj_labels),
        task_completed=json.dumps(task_completed_list), task_pending=json.dumps(task_pending_list),
        prod_labels=json.dumps(prod_labels), prod_ratings=json.dumps(prod_ratings),
        total_study_hours=round(total_mins/60, 1),
        total_sessions=StudySession.query.filter_by(user_id=uid).count(),
        total_tasks=total_tasks, completed_tasks=completed_tasks,
        completion_rate=round((completed_tasks/total_tasks*100) if total_tasks > 0 else 0, 1),
        goals=Goal.query.filter_by(user_id=uid).all(), subjects=subjects)


# ─── Goals ─────────────────────────────────────────────────────────────────────
@app.route('/goals')
@login_required
def goals():
    return render_template('goals.html',
        goals=Goal.query.filter_by(user_id=current_user.id).order_by(Goal.created_at.desc()).all(),
        today=date.today())


@app.route('/goals/add', methods=['POST'])
@login_required
def add_goal():
    title = request.form.get('title', '').strip()
    if not title:
        flash('Goal title is required.', 'error')
        return redirect(url_for('goals'))
    due_str = request.form.get('target_date', '')
    db.session.add(Goal(user_id=current_user.id, title=title,
                        description=request.form.get('description', ''),
                        target_date=datetime.strptime(due_str, '%Y-%m-%d').date() if due_str else None,
                        progress=int(request.form.get('progress', 0))))
    db.session.commit()
    flash('Goal added!', 'success')
    return redirect(url_for('goals'))


@app.route('/goals/update/<int:goal_id>', methods=['POST'])
@login_required
def update_goal(goal_id):
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    goal.progress = int(request.form.get('progress', goal.progress))
    goal.status   = request.form.get('status', goal.status)
    db.session.commit()
    return redirect(url_for('goals'))


@app.route('/goals/delete/<int:goal_id>', methods=['POST'])
@login_required
def delete_goal(goal_id):
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    db.session.delete(goal)
    db.session.commit()
    flash('Goal deleted.', 'info')
    return redirect(url_for('goals'))


# ─── App Init ──────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        db.create_all()   # create tables if they don't exist (data is preserved)
    app.run(debug=True, port=5000)
