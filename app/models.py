from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
import bcrypt
from sqlalchemy.orm import relationship

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Связь с логами
    login_logs = db.relationship('LoginLog', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def __repr__(self):
        return f'<User {self.username}>'

class LoginLog(db.Model):
    __tablename__ = 'login_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    logout_time = db.Column(db.DateTime, nullable=True)
    session_duration = db.Column(db.Integer, nullable=True)  # в секундах
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<LoginLog {self.user_id} {self.login_time}>'

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(50), nullable=False)
    hire_date = db.Column(db.Date, nullable=False)
    salary = db.Column(db.Integer, nullable=False)
    boss_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    
    # Self-referential relationship
    boss = relationship('Employee', remote_side=[id], backref='subordinates')
    
    def __repr__(self):
        return f'<Employee {self.full_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'position': self.position,
            'hire_date': self.hire_date.isoformat(),
            'salary': self.salary,
            'boss_name': self.boss.full_name if self.boss else None,
            'boss_id': self.boss_id
        }

    @staticmethod
    def get_unique_positions():
        """Получает список уникальных должностей из базы"""
        positions = db.session.query(Employee.position).distinct().all()
        return [position[0] for position in positions if position[0]]

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))