from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(20), nullable=False)
    parent_contact = db.Column(db.String(15))
    email = db.Column(db.String(100))
    admission_year = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    results = db.relationship('Result', backref='student', lazy=True, cascade='all, delete-orphan')
    
    def get_total_marks(self):
        return sum(r.marks_obtained for r in self.results)
    
    def get_percentage(self):
        if not self.results:
            return 0
        total_obtained = sum(r.marks_obtained for r in self.results)
        total_possible = sum(r.total_marks for r in self.results)
        return round((total_obtained / total_possible) * 100, 2) if total_possible > 0 else 0
    
    def get_grade(self):
        percentage = self.get_percentage()
        if percentage >= 90:
            return ('A+', '#10b981', 'Outstanding')
        elif percentage >= 80:
            return ('A', '#3b82f6', 'Excellent')
        elif percentage >= 70:
            return ('B+', '#8b5cf6', 'Very Good')
        elif percentage >= 60:
            return ('B', '#f59e0b', 'Good')
        elif percentage >= 50:
            return ('C', '#f97316', 'Average')
        elif percentage >= 40:
            return ('D', '#ef4444', 'Pass')
        else:
            return ('F', '#dc2626', 'Fail')
    
    def to_dict(self):
        return {
            'id': self.id,
            'roll_number': self.roll_number,
            'name': self.name,
            'class_name': self.class_name,
            'percentage': self.get_percentage(),
            'grade': self.get_grade()[0]
        }

class Subject(db.Model):
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    code = db.Column(db.String(10), unique=True)
    max_marks = db.Column(db.Integer, default=100)
    
    results = db.relationship('Result', backref='subject', lazy=True)

class Result(db.Model):
    __tablename__ = 'results'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    marks_obtained = db.Column(db.Float, nullable=False)
    total_marks = db.Column(db.Integer, default=100)
    exam_type = db.Column(db.String(20), default='Final Exam')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'subject_id', name='unique_student_subject'),
    )