from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


# ─── User ───────────────────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    avatar_initials = db.Column(db.String(4), default='')
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships scoped to user
    subjects = db.relationship('Subject', backref='owner', lazy=True, cascade='all, delete-orphan')
    tasks    = db.relationship('Task',    backref='owner', lazy=True, cascade='all, delete-orphan')
    sessions = db.relationship('StudySession', backref='owner', lazy=True, cascade='all, delete-orphan')
    goals    = db.relationship('Goal',    backref='owner', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'email': self.email}


# ─── Subject ─────────────────────────────────────────────────────────────────
class Subject(db.Model):
    __tablename__ = 'subjects'
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name         = db.Column(db.String(100), nullable=False)
    color        = db.Column(db.String(20), default='#6366f1')
    description  = db.Column(db.Text, default='')
    target_hours = db.Column(db.Float, default=0.0)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    tasks    = db.relationship('Task',         backref='subject', lazy=True, cascade='all, delete-orphan')
    sessions = db.relationship('StudySession', backref='subject', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'color': self.color,
            'description': self.description, 'target_hours': self.target_hours,
            'created_at': self.created_at.isoformat()
        }


# ─── Task ─────────────────────────────────────────────────────────────────────
class Task(db.Model):
    __tablename__ = 'tasks'
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title        = db.Column(db.String(200), nullable=False)
    description  = db.Column(db.Text, default='')
    subject_id   = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=True)
    priority     = db.Column(db.String(20), default='medium')   # low, medium, high, urgent
    status       = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    due_date     = db.Column(db.Date, nullable=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id, 'title': self.title, 'description': self.description,
            'subject_id': self.subject_id,
            'subject_name':  self.subject.name  if self.subject else 'General',
            'subject_color': self.subject.color if self.subject else '#6366f1',
            'priority': self.priority, 'status': self.status,
            'due_date':      self.due_date.isoformat()      if self.due_date      else None,
            'created_at':    self.created_at.isoformat(),
            'completed_at':  self.completed_at.isoformat()  if self.completed_at  else None,
        }


# ─── Study Session ────────────────────────────────────────────────────────────
class StudySession(db.Model):
    __tablename__ = 'study_sessions'
    id                  = db.Column(db.Integer, primary_key=True)
    user_id             = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id          = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=True)
    date                = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    duration_minutes    = db.Column(db.Integer, default=0)
    notes               = db.Column(db.Text, default='')
    productivity_rating = db.Column(db.Integer, default=3)   # 1‒5
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'subject_name':  self.subject.name  if self.subject else 'General',
            'subject_color': self.subject.color if self.subject else '#6366f1',
            'date': self.date.isoformat(),
            'duration_minutes': self.duration_minutes,
            'notes': self.notes,
            'productivity_rating': self.productivity_rating,
        }


# ─── Goal ─────────────────────────────────────────────────────────────────────
class Goal(db.Model):
    __tablename__ = 'goals'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    target_date = db.Column(db.Date, nullable=True)
    progress    = db.Column(db.Integer, default=0)    # 0‒100 %
    status      = db.Column(db.String(20), default='active')  # active, completed, paused
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'title': self.title, 'description': self.description,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'progress': self.progress, 'status': self.status,
        }
