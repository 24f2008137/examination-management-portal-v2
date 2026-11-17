from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(), unique=True, nullable=False)
    email = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    role = db.Column(db.String(), nullable=False, default='student')  # admin / examiner / student
    status = db.Column(db.String(), default='Active')

    examiner_profile = db.relationship('ExaminerProfile', backref='user', uselist=False)
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False)

class ExaminerProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    name = db.Column(db.String(), nullable=False)
    contact_details = db.Column(db.String())
    department = db.Column(db.String())
    status = db.Column(db.String(), default='Active')

    examslot = db.relationship('ExamSlot', backref='examiner', lazy=True)
    evaluation = db.relationship('Evaluation', backref='examiner', lazy=True)


class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    name = db.Column(db.String(), nullable=False)
    contact_details = db.Column(db.String())
    department = db.Column(db.String())

    booking = db.relationship('Booking', backref='studentprofile', lazy=True)
    evaluation = db.relationship('Evaluation', backref='studentprofile', lazy=True)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(), nullable=False, unique=True)
    course_name = db.Column(db.String(), nullable=False)
    course_description = db.Column(db.String(), nullable=False)
    course_status = db.Column(db.String(), default='Active')

    exam = db.relationship('Exam', backref='course', lazy=True)


class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    exam_name = db.Column(db.String(), nullable=False)
    exam_type = db.Column(db.String(), nullable=False)
    exam_duration = db.Column(db.Integer, nullable=False)
    maximum_marks = db.Column(db.Integer, nullable=False)
    slot_creation_start_date = db.Column(db.Date, nullable=False)
    slot_creation_end_date = db.Column(db.Date, nullable=False)
    slot_booking_start_date = db.Column(db.Date, nullable=False)
    slot_booking_end_date = db.Column(db.Date, nullable=False)
    exam_status = db.Column(db.String(), default='Draft') #Draft / Slot Creation / Booking Open / Closed / Completed
    results_published = db.Column(db.Boolean, default=False)

    examslot = db.relationship('ExamSlot', backref='exam', lazy=True)
    rubric = db.relationship('ExamRubric', backref='exam', lazy=True)
    assigned_examiner = db.relationship('ExamExaminer', backref='exam', lazy=True)


# which examiners are assigned to which exam
class ExamExaminer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey('examiner_profile.id'), nullable=False)

    examiner = db.relationship('ExaminerProfile', backref='assigned_exam')


class ExamSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey('examiner_profile.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    maximum_student_capacity = db.Column(db.Integer, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(), default='Available')  # Available / Full / Cancelled / Completed
    meeting_link = db.Column(db.String())

    bookings = db.relationship('Booking', backref='examslot', lazy=True)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slot_id = db.Column(db.Integer, db.ForeignKey('exam_slot.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    booking_status = db.Column(db.String(), default='Booked')  # Booked / Cancelled / Completed
    booking_date = db.Column(db.DateTime, default=datetime.now)

    evaluation = db.relationship('Evaluation', backref='booking', uselist=False)


class ExamRubric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    criterion_name = db.Column(db.String(), nullable=False)
    max_marks = db.Column(db.Integer, nullable=False)
    weightage = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(), nullable=False)

    scores = db.relationship('EvaluationScore', backref='exam_rubric', lazy=True)


class Evaluation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey('examiner_profile.id'), nullable=False)
    marks = db.Column(db.Float, default=0)  # total of all criterion marks
    remarks = db.Column(db.String())
    evaluation_date = db.Column(db.DateTime, default=datetime.now)
    evaluation_status = db.Column(db.String(), default='Pending')  # Pending / Evaluated

    score = db.relationship('EvaluationScore', backref='evaluation', lazy=True)


class EvaluationScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluation.id'), nullable=False)
    rubric_id = db.Column(db.Integer, db.ForeignKey('exam_rubric.id'), nullable=False)
    marks = db.Column(db.Float, nullable=False)