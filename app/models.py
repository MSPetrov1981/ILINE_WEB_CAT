from app import db
from sqlalchemy.orm import relationship
from datetime import datetime

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