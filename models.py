from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ========== USER MODEL ==========
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

# ========== STUDENT MODEL ==========
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
    
    def __repr__(self):
        return f'<Student {self.name}>'

# ========== SUBJECT MODEL ==========
class Subject(db.Model):
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    code = db.Column(db.String(10), unique=True)
    max_marks = db.Column(db.Integer, default=100)
    
    results = db.relationship('Result', backref='subject', lazy=True)
    
    def __repr__(self):
        return f'<Subject {self.name}>'

# ========== RESULT MODEL ==========
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
    
    def __repr__(self):
        return f'<Result {self.student_id}:{self.subject_id}>'