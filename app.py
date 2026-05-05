from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from models import db, Student, Subject, Result
from sqlalchemy import func, desc
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///results.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Create tables and add sample data

with app.app_context():
    db.create_all()
    
    # Add sample subjects if none exist
    if Subject.query.count() == 0:
        subjects = [
            Subject(name='Mathematics', code='MATH101', max_marks=100),
            Subject(name='Physics', code='PHY101', max_marks=100),
            Subject(name='Chemistry', code='CHEM101', max_marks=100),
            Subject(name='English', code='ENG101', max_marks=100),
            Subject(name='Computer Science', code='CS101', max_marks=100),
        ]
        db.session.add_all(subjects)
        db.session.commit()
    
    # Add sample students if none exist
    if Student.query.count() == 0:
        sample_students = [
            Student(roll_number='2024001', name='Aarav Sharma', class_name='10A', parent_contact='9876543210', email='aarav@example.com', admission_year=2024),
            Student(roll_number='2024002', name='Vivaan Gupta', class_name='10A', parent_contact='9876543211', email='vivaan@example.com', admission_year=2024),
            Student(roll_number='2024003', name='Ananya Singh', class_name='10B', parent_contact='9876543212', email='ananya@example.com', admission_year=2024),
            Student(roll_number='2024004', name='Diya Verma', class_name='10B', parent_contact='9876543213', email='diya@example.com', admission_year=2024),
            Student(roll_number='2024005', name='Advik Reddy', class_name='10A', parent_contact='9876543214', email='advik@example.com', admission_year=2024),
        ]
        db.session.add_all(sample_students)
        db.session.commit()
        
        # Add sample results
        subjects = Subject.query.all()
        students = Student.query.all()
        for student in students:
            for subject in subjects:
                import random
                marks = random.randint(45, 98)
                result = Result(student_id=student.id, subject_id=subject.id, marks_obtained=marks, total_marks=100)
                db.session.add(result)
        db.session.commit()

# Routes
@app.route('/')
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
        grade_counts[grade] = grade_counts.get(grade, 0) + 1
    
    # Recent students
    recent_students = Student.query.order_by(Student.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html',
                         total_students=total_students,
                         total_subjects=total_subjects,
                         avg_percentage=round(avg_percentage, 2),
                         passed=passed,
                         failed=failed,
                         grade_counts=grade_counts,
                         recent_students=recent_students)

@app.route('/students')
def students_list():
    class_filter = request.args.get('class', '')
    search = request.args.get('search', '')
    
    query = Student.query
    if class_filter:
        query = query.filter_by(class_name=class_filter)
    if search:
        query = query.filter(
            Student.name.contains(search) | 
            Student.roll_number.contains(search) |
            Student.email.contains(search)
        )
    
    students = query.order_by(Student.roll_number).all()
    classes = db.session.query(Student.class_name).distinct().all()
    
    return render_template('students.html', students=students, classes=[c[0] for c in classes if c[0]])

@app.route('/student/add', methods=['GET', 'POST'])
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
            return redirect(url_for('add_student'))
    
    return render_template('student_form.html', title='Add Student', student=None)

@app.route('/student/edit/<int:id>', methods=['GET', 'POST'])
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
def delete_student(id):
    student = Student.query.get_or_404(id)
    try:
        db.session.delete(student)
        db.session.commit()
        flash('Student deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('students_list'))

@app.route('/results/<int:student_id>')
def view_results(student_id):
    student = Student.query.get_or_404(student_id)
    subjects = Subject.query.all()
    
    results = {}
    for result in student.results:
        results[result.subject_id] = result
    
    return render_template('results.html', student=student, subjects=subjects, results=results)

@app.route('/results/save', methods=['POST'])
def save_results():
    data = request.json
    student_id = data['student_id']
    
    try:
        for subject_result in data['results']:
            result = Result.query.filter_by(
                student_id=student_id,
                subject_id=subject_result['subject_id']
            ).first()
            
            marks = float(subject_result['marks'])
            
            if result:
                result.marks_obtained = marks
            else:
                result = Result(
                    student_id=student_id,
                    subject_id=subject_result['subject_id'],
                    marks_obtained=marks,
                    total_marks=100
                )
                db.session.add(result)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Results saved successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/report/<int:student_id>')
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