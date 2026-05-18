from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from models import db, Student, Subject, Result, User
from datetime import datetime
from functools import wraps

import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(app.instance_path, "results.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Create tables
with app.app_context():
    db.create_all()

# ========== WELCOME PAGE (NO LOGIN REQUIRED) ==========

@app.route('/')
def home():
    return render_template('welcome.html')

# ========== AUTHENTICATION ROUTES ==========

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('signup'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('signup'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('signup'))
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Welcome {username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('login'))

# ========== DASHBOARD ROUTE (REQUIRES LOGIN) ==========

@app.route('/dashboard')
@login_required
def dashboard():
    total_students = Student.query.count()
    total_subjects = Subject.query.count()
    
    students = Student.query.all()
    percentages = [s.get_percentage() for s in students]
    avg_percentage = sum(percentages) / len(percentages) if percentages else 0
    
    passed = sum(1 for s in students if s.get_percentage() >= 40)
    failed = total_students - passed
    
    # Grade distribution
    grade_counts = {'A+': 0, 'A': 0, 'B+': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
    for student in students:
        grade = student.get_grade()[0]
        if grade in grade_counts:
            grade_counts[grade] += 1
        else:
            grade_counts['F'] += 1
    
    recent_students = Student.query.order_by(Student.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html',
                         total_students=total_students,
                         total_subjects=total_subjects,
                         avg_percentage=round(avg_percentage, 2),
                         passed=passed,
                         failed=failed,
                         grade_counts=grade_counts,
                         recent_students=recent_students)

# ========== STUDENT ROUTES ==========

@app.route('/students')
@login_required
def students_list():
    # Get filter parameters from URL
    class_filter = request.args.get('class', '')
    search = request.args.get('search', '')
    
    # Start with all students query
    query = Student.query
    
    # Apply class filter if provided
    if class_filter:
        query = query.filter(Student.class_name == class_filter)
    
    # Apply search filter if provided  
    if search:
        query = query.filter(
            Student.name.contains(search) | 
            Student.roll_number.contains(search)
        )
    
    # Execute query
    students = query.order_by(Student.roll_number).all()
    
    # Get all unique classes for dropdown
    all_classes = db.session.query(Student.class_name).distinct().all()
    class_list = [c[0] for c in all_classes if c[0]]
    
    return render_template('students.html', students=students, classes=class_list)

@app.route('/student/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        try:
            student = Student(
                roll_number=request.form['roll_number'],
                name=request.form['name'],
                class_name=request.form['class_name'],
                parent_contact=request.form.get('parent_contact', ''),
                email=request.form.get('email', ''),
                admission_year=int(request.form.get('admission_year', 2024))
            )
            db.session.add(student)
            db.session.commit()
            flash('Student added successfully!', 'success')
            return redirect(url_for('students_list'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('student_form.html', title='Add Student', student=None)

@app.route('/student/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    student = Student.query.get_or_404(id)
    if request.method == 'POST':
        try:
            student.roll_number = request.form['roll_number']
            student.name = request.form['name']
            student.class_name = request.form['class_name']
            student.parent_contact = request.form.get('parent_contact', '')
            student.email = request.form.get('email', '')
            student.admission_year = int(request.form.get('admission_year', 2024))
            db.session.commit()
            flash('Student updated successfully!', 'success')
            return redirect(url_for('students_list'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('student_form.html', title='Edit Student', student=student)

@app.route('/student/delete/<int:id>')
@login_required
def delete_student(id):
    student = Student.query.get_or_404(id)
    try:
        db.session.delete(student)
        db.session.commit()
        flash('Student deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('students_list'))

# ========== RESULT ROUTES ==========

@app.route('/results/<int:student_id>')
@login_required
def view_results(student_id):
    student = Student.query.get_or_404(student_id)
    subjects = Subject.query.all()
    
    results = {}
    for result in student.results:
        results[result.subject_id] = result
    
    return render_template('results.html', student=student, subjects=subjects, results=results)

@app.route('/results/save', methods=['POST'])
@login_required
def save_results():
    data = request.json
    student_id = data['student_id']
    
    try:
        for subject_result in data['results']:
            subject = Subject.query.get(subject_result['subject_id'])
            if not subject:
                return jsonify({'success': False, 'message': f'Subject with id {subject_result["subject_id"]} not found'})
            
            result = Result.query.filter_by(
                student_id=student_id,
                subject_id=subject_result['subject_id']
            ).first()
            
            marks = float(subject_result['marks'])
            if marks < 0 or marks > subject.max_marks:
                return jsonify({'success': False, 'message': f'Marks for {subject.name} must be between 0 and {subject.max_marks}'})
            
            if result:
                result.marks_obtained = marks
                result.total_marks = subject.max_marks
            else:
                result = Result(
                    student_id=student_id,
                    subject_id=subject_result['subject_id'],
                    marks_obtained=marks,
                    total_marks=subject.max_marks
                )
                db.session.add(result)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Results saved successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/report/<int:student_id>')
@login_required
def report_card(student_id):
    student = Student.query.get_or_404(student_id)
    subjects = Subject.query.all()
    
    subject_results = []
    for subject in subjects:
        result = Result.query.filter_by(student_id=student_id, subject_id=subject.id).first()
        subject_results.append({
            'name': subject.name,
            'code': subject.code,
            'marks': result.marks_obtained if result else None,
            'max_marks': subject.max_marks,
            'percentage': (result.marks_obtained / subject.max_marks) * 100 if result else 0
        })
    
    percentage = student.get_percentage()
    grade, color, remark = student.get_grade()
    
    return render_template('report_card.html', 
                         student=student, 
                         subjects=subject_results,
                         percentage=percentage,
                         grade=grade,
                         grade_color=color,
                         remark=remark)

@app.route('/api/statistics')
@login_required
def statistics_api():
    students = Student.query.all()
    class_stats = {}
    
    for student in students:
        if student.class_name not in class_stats:
            class_stats[student.class_name] = {'total': 0, 'sum': 0}
        class_stats[student.class_name]['total'] += 1
        class_stats[student.class_name]['sum'] += student.get_percentage()
    
    result = []
    for class_name, stats in class_stats.items():
        result.append({
            'class': class_name,
            'average': round(stats['sum'] / stats['total'], 2),
            'count': stats['total']
        })
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)