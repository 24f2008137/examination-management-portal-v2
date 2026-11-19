from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash
from datetime import datetime
from model import db, User, ExaminerProfile, StudentProfile, Course, Exam, ExamExaminer, ExamSlot, Booking, ExamRubric, Evaluation
from utils.decorators import roles_required
from utils.cache import cached, invalidate, TTL_DASHBOARD

EXAM_TYPES = ["Viva", "Assessment"]

admin_bp = Blueprint('admin', __name__)


def _dates_error(exam):
    
    if exam.slot_creation_end_date < exam.slot_creation_start_date:
        return 'Slot creation end date cannot be before its start date'
    if exam.slot_booking_end_date < exam.slot_booking_start_date:
        return 'Slot booking end date cannot be before its start date'
    if exam.slot_booking_start_date < exam.slot_creation_start_date:
        return 'Booking cannot start before slot creation starts'
    return None


def _rubric_total_error(exam_id, new_max, ignore_rubric_id=None):
    
    exam = Exam.query.get(exam_id)
    total = sum(r.max_marks for r in exam.rubric if r.id != ignore_rubric_id) + new_max
    if total > exam.maximum_marks:
        return (f'Rubric marks would total {total}, which exceeds the '
                f'exam maximum of {exam.maximum_marks}')
    return None


@admin_bp.route('/api/admin/courses', methods=['GET'])
@roles_required('admin')
def get_courses():

    search = request.args.get('q', '')

    courses = Course.query.filter(
        Course.course_name.ilike(f'%{search}%')
    ).all()

    result = []

    for course in courses:
        result.append({
            'id': course.id,
            'course_code': course.course_code,
            'course_name': course.course_name,
            'course_description': course.course_description,
            'course_status': course.course_status
        })

    return jsonify(result)


@admin_bp.route('/api/admin/courses', methods=['POST'])
@roles_required('admin')
def create_course():

    data = request.get_json()

    course = Course(
        course_code=data['course_code'],
        course_name=data['course_name'],
        course_description=data['course_description'],
        course_status=data.get('course_status', 'Active')
    )

    db.session.add(course)
    db.session.commit()

    return jsonify({"message": "Course created successfully"}), 201


@admin_bp.route('/api/admin/courses/<int:id>', methods=['PUT'])
@roles_required('admin')
def update_course(id):

    course = Course.query.get(id)

    if not course:
        return jsonify({"message": "Course not found"}), 404

    data = request.get_json()

    course.course_code = data.get('course_code', course.course_code)
    course.course_name = data.get('course_name', course.course_name)
    course.course_description = data.get('course_description', course.course_description)
    course.course_status = data.get('course_status', course.course_status)

    db.session.commit()

    return jsonify({"message": "Course updated successfully"})


@admin_bp.route('/api/admin/courses/<int:id>', methods=['DELETE'])
@roles_required('admin')
def delete_course(id):

    course = Course.query.get(id)

    if not course:
        return jsonify({"message": "Course not found"}), 404

    db.session.delete(course)
    db.session.commit()

    return jsonify({"message": "Course deleted successfully"})


@admin_bp.route('/api/admin/exams', methods=['POST'])
@roles_required('admin')
def create_exam():

    data = request.get_json()

    course = Course.query.get(data['course_id'])

    if not course:
        return jsonify({'message': 'Course not found'}), 404

    if data.get('exam_type') not in EXAM_TYPES:
        return jsonify({'message': 'Exam type must be one of: ' + ', '.join(EXAM_TYPES)}), 400

    exam = Exam(
        course_id=data['course_id'],
        exam_name=data['exam_name'],
        exam_type=data['exam_type'],
        exam_duration=data['exam_duration'],
        maximum_marks=data['maximum_marks'],
        slot_creation_start_date=datetime.strptime(data['slot_creation_start_date'], '%Y-%m-%d').date(),
        slot_creation_end_date=datetime.strptime(data['slot_creation_end_date'], '%Y-%m-%d').date(),
        slot_booking_start_date=datetime.strptime(data['slot_booking_start_date'], '%Y-%m-%d').date(),
        slot_booking_end_date=datetime.strptime(data['slot_booking_end_date'], '%Y-%m-%d').date(),
        exam_instructions=data.get('exam_instructions'),
        exam_status='Draft'
    )

    error = _dates_error(exam)
    if error:
        return jsonify({'message': error}), 400

    db.session.add(exam)
    db.session.commit()

    return jsonify({
        'message': 'Exam created successfully',
        'exam_id': exam.id
    }), 201


@admin_bp.route('/api/admin/exams/<int:id>', methods=['PUT'])
@roles_required('admin')
def update_exam(id):

    exam = Exam.query.get(id)

    if not exam:
        return jsonify({'message': 'Exam not found'}), 404

    data = request.get_json()

    new_type = data.get('exam_type', exam.exam_type)
    if new_type != exam.exam_type and new_type not in EXAM_TYPES:   # old rows keep their legacy type
        return jsonify({'message': 'Exam type must be one of: ' + ', '.join(EXAM_TYPES)}), 400

    exam.course_id = data.get('course_id', exam.course_id)
    exam.exam_name = data.get('exam_name', exam.exam_name)
    exam.exam_type = data.get('exam_type', exam.exam_type)
    exam.exam_duration = data.get('exam_duration', exam.exam_duration)
    exam.maximum_marks = data.get('maximum_marks', exam.maximum_marks)
    exam.exam_instructions = data.get('exam_instructions', exam.exam_instructions)

    if 'slot_creation_start_date' in data:
        exam.slot_creation_start_date = datetime.strptime(data['slot_creation_start_date'], '%Y-%m-%d').date()

    if 'slot_creation_end_date' in data:
        exam.slot_creation_end_date = datetime.strptime(data['slot_creation_end_date'], '%Y-%m-%d').date()

    if 'slot_booking_start_date' in data:
        exam.slot_booking_start_date = datetime.strptime(data['slot_booking_start_date'], '%Y-%m-%d').date()

    if 'slot_booking_end_date' in data:
        exam.slot_booking_end_date = datetime.strptime(data['slot_booking_end_date'], '%Y-%m-%d').date()

    error = _dates_error(exam)
    if error:
        db.session.rollback()
        return jsonify({'message': error}), 400

    db.session.commit()

    return jsonify({'message': 'Exam updated successfully'}), 200


@admin_bp.route('/api/admin/exams/<int:id>', methods=['DELETE'])
@roles_required('admin')
def delete_exam(id):

    exam = Exam.query.get(id)

    if not exam:
        return jsonify({'message': 'Exam not found'}), 404

    db.session.delete(exam)
    db.session.commit()

    return jsonify({'message': 'Exam deleted successfully'}), 200


@admin_bp.route('/api/admin/exams/<int:id>/status', methods=['PUT'])
@roles_required('admin')
def update_exam_status(id):

    exam = Exam.query.get(id)

    if not exam:
        return jsonify({'message': 'Exam not found'}), 404

    data = request.get_json()

    status = data.get('exam_status')

    if status not in ['Draft', 'Slot Creation', 'Booking Open', 'Closed', 'Completed']:
        return jsonify({'message': 'Invalid exam status'}), 400

    if status == 'Slot Creation':
        if not exam.assigned_examiner:
            return jsonify({'message': 'Assign at least one examiner first'}), 400
        if not exam.rubric:
            return jsonify({'message': 'Create the evaluation rubric first'}), 400

    if status == 'Booking Open':
        has_slots = ExamSlot.query.filter(
            ExamSlot.exam_id == exam.id,
            ExamSlot.status == 'Available',
            ExamSlot.available_seats > 0
        ).first()
        if not has_slots:
            return jsonify({'message': 'No available slots have been created yet'}), 400

    exam.exam_status = status

    if status == 'Completed':
        for slot in exam.examslot:
            if slot.status != 'Cancelled':
                slot.status = 'Completed'

    db.session.commit()

    return jsonify({
        'message': 'Exam status updated successfully',
        'exam_status': exam.exam_status
    }), 200


@admin_bp.route('/api/admin/exams/<int:id>/publish', methods=['POST'])
@roles_required('admin')
def publish_exam(id):

    exam = Exam.query.get(id)

    if not exam:
        return jsonify({'message': 'Exam not found'}), 404

    if exam.exam_status != 'Completed':
        return jsonify({
            'message': 'Results can be published only after the exam is completed'
        }), 400

    exam.results_published = True

    db.session.commit()

    return jsonify({
        'message': 'Exam results published successfully'
    }), 200


@admin_bp.route('/api/admin/exams/<int:id>/rubrics', methods=['POST'])
@roles_required('admin')
def create_rubric(id):

    exam = Exam.query.get(id)

    if not exam:
        return jsonify({'message': 'Exam not found'}), 404

    data = request.get_json()

    error = _rubric_total_error(id, data['max_marks'])
    if error:
        return jsonify({'message': error}), 400

    rubric = ExamRubric(
        exam_id=id,
        criterion_name=data['criterion_name'],
        max_marks=data['max_marks'],
        weightage=data['weightage'],
        description=data['description']
    )

    db.session.add(rubric)
    db.session.commit()

    return jsonify({'message': 'Rubric created successfully'}), 201


@admin_bp.route('/api/admin/rubrics/<int:id>', methods=['PUT'])
@roles_required('admin')
def update_rubric(id):

    rubric = ExamRubric.query.get(id)

    if not rubric:
        return jsonify({'message': 'Rubric not found'}), 404

    data = request.get_json()

    error = _rubric_total_error(
        rubric.exam_id, data.get('max_marks', rubric.max_marks), ignore_rubric_id=rubric.id
    )
    if error:
        return jsonify({'message': error}), 400

    rubric.criterion_name = data.get('criterion_name', rubric.criterion_name)
    rubric.max_marks = data.get('max_marks', rubric.max_marks)
    rubric.weightage = data.get('weightage', rubric.weightage)
    rubric.description = data.get('description', rubric.description)

    db.session.commit()

    return jsonify({'message': 'Rubric updated successfully'}), 200


@admin_bp.route('/api/admin/rubrics/<int:id>', methods=['DELETE'])
@roles_required('admin')
def delete_rubric(id):

    rubric = ExamRubric.query.get(id)

    if not rubric:
        return jsonify({'message': 'Rubric not found'}), 404

    db.session.delete(rubric)
    db.session.commit()

    return jsonify({'message': 'Rubric deleted successfully'}), 200


@admin_bp.route('/api/admin/examiners', methods=['GET'])
@roles_required('admin')
def get_examiners():

    search = request.args.get('q', '')

    examiners = ExaminerProfile.query.join(User).filter(
        (ExaminerProfile.name.ilike(f'%{search}%')) |
        (ExaminerProfile.department.ilike(f'%{search}%')) |
        (User.username.ilike(f'%{search}%'))
    ).all()

    result = []

    for examiner in examiners:
        result.append({
            'id': examiner.id,
            'user_id': examiner.user_id,
            'username': examiner.user.username,
            'name': examiner.name,
            'contact_details': examiner.contact_details,
            'department': examiner.department,
            'status': examiner.status
        })

    return jsonify(result), 200


@admin_bp.route('/api/admin/examiners', methods=['POST'])
@roles_required('admin')
def create_examiner():

    data = request.get_json()

    user = User(
        username=data['username'],
        email=data['email'],
        password=generate_password_hash(data['password']),
        role='examiner'
    )

    db.session.add(user)
    db.session.flush()

    examiner = ExaminerProfile(
        user_id=user.id,
        name=data['name'],
        contact_details=data.get('contact_details'),
        department=data.get('department')
    )

    db.session.add(examiner)
    db.session.commit()

    return jsonify({
        'message': 'Examiner created successfully',
        'examiner_id': examiner.id
    }), 201


@admin_bp.route('/api/admin/examiners/<int:id>', methods=['PUT'])
@roles_required('admin')
def update_examiner(id):

    examiner = ExaminerProfile.query.get(id)

    if not examiner:
        return jsonify({'message': 'Examiner not found'}), 404

    data = request.get_json()

    examiner.name = data.get('name', examiner.name)
    examiner.contact_details = data.get('contact_details', examiner.contact_details)
    examiner.department = data.get('department', examiner.department)

    if 'status' in data:
        examiner.status = data['status']
        examiner.user.status = data['status']

    db.session.commit()

    return jsonify({'message': 'Examiner updated successfully'}), 200


@admin_bp.route('/api/admin/exams/<int:id>/examiners', methods=['GET'])
@roles_required('admin')
def get_assigned_examiners(id):

    exam = Exam.query.get(id)

    if not exam:
        return jsonify({'message': 'Exam not found'}), 404

    assignments = ExamExaminer.query.filter_by(exam_id=id).all()

    result = []

    for assignment in assignments:
        examiner = assignment.examiner

        result.append({
            'id': examiner.id,
            'name': examiner.name,
            'department': examiner.department
        })

    return jsonify(result), 200


@admin_bp.route('/api/admin/exams/<int:id>/examiners', methods=['PUT'])
@roles_required('admin')
def assign_examiners(id):

    exam = Exam.query.get(id)

    if not exam:
        return jsonify({'message': 'Exam not found'}), 404

    data = request.get_json()

    examiner_ids = data.get('examiner_ids', [])

    if not isinstance(examiner_ids, list):
        return jsonify({'message': 'Examiner IDs must be a list'}), 400

    for examiner_id in examiner_ids:

        examiner = ExaminerProfile.query.get(examiner_id)

        if not examiner:
            return jsonify({
                'message': f'Examiner {examiner_id} not found'
            }), 404

        if examiner.status != 'Active' or examiner.user.status != 'Active':
            return jsonify({
                'message': f'Examiner {examiner_id} is inactive'
            }), 400

    removed = ExamExaminer.query.filter(
        ExamExaminer.exam_id == id,
        ~ExamExaminer.examiner_id.in_(examiner_ids)
    ).all()

    for assignment in removed:
        if ExamSlot.query.filter_by(exam_id=id, examiner_id=assignment.examiner_id).first():
            return jsonify({
                'message': f'{assignment.examiner.name} already has slots for this exam. '
                           'Reassign or remove those slots first.'
            }), 400

    ExamExaminer.query.filter_by(exam_id=id).delete()

    for examiner_id in examiner_ids:

        assignment = ExamExaminer(
            exam_id=id,
            examiner_id=examiner_id
        )

        db.session.add(assignment)

    db.session.commit()
    invalidate('exams')

    return jsonify({
        'message': 'Examiners assigned successfully'
    }), 200


@admin_bp.route('/api/admin/students', methods=['GET'])
@roles_required('admin')
def get_students():

    search = request.args.get('q', '')

    students = StudentProfile.query.join(User).filter(
        (StudentProfile.name.ilike(f'%{search}%')) |
        (StudentProfile.department.ilike(f'%{search}%')) |
        (User.username.ilike(f'%{search}%'))
    ).all()

    result = []

    for student in students:
        result.append({
            'id': student.id,
            'user_id': student.user_id,
            'username': student.user.username,
            'name': student.name,
            'contact_details': student.contact_details,
            'department': student.department,
            'status': student.user.status
        })

    return jsonify(result), 200


@admin_bp.route('/api/admin/students/<int:id>/status', methods=['PUT'])
@roles_required('admin')
def update_student_status(id):

    student = StudentProfile.query.get(id)

    if not student:
        return jsonify({'message': 'Student not found'}), 404

    data = request.get_json()

    status = data.get('status')

    if status not in ['Active', 'Inactive']:
        return jsonify({'message': 'Invalid status'}), 400

    student.user.status = status

    db.session.commit()

    return jsonify({
        'message': 'Student status updated successfully',
        'status': student.user.status
    }), 200


@admin_bp.route('/api/admin/students/<int:id>/history', methods=['GET'])
@roles_required('admin')
def get_student_history(id):

    student = StudentProfile.query.get(id)

    if not student:
        return jsonify({'message': 'Student not found'}), 404

    result = []

    for booking in student.booking:

        result.append({
            'booking_id': booking.id,
            'booking_status': booking.booking_status,
            'booking_date': str(booking.booking_date),
            'exam_name': booking.examslot.exam.exam_name,
            'exam_date': str(booking.examslot.date),
            'examiner': booking.examslot.examiner.name,
            'evaluation': None
        })

        if booking.evaluation:
            result[-1]['evaluation'] = {
                'marks': booking.evaluation.marks,
                'remarks': booking.evaluation.remarks,
                'evaluation_status': booking.evaluation.evaluation_status
            }

    return jsonify(result), 200


@admin_bp.route('/api/admin/slots', methods=['GET'])
@roles_required('admin')
def get_all_slots():

    exam_id = request.args.get('exam_id')
    examiner_id = request.args.get('examiner_id')
    status = request.args.get('status')

    slots = ExamSlot.query

    if exam_id:
        slots = slots.filter_by(exam_id=exam_id)

    if examiner_id:
        slots = slots.filter_by(examiner_id=examiner_id)

    if status:
        slots = slots.filter_by(status=status)

    slots = slots.all()

    result = []

    for slot in slots:
        result.append({
            'id': slot.id,
            'exam_id': slot.exam_id,
            'exam_name': slot.exam.exam_name,
            'examiner_id': slot.examiner_id,
            'examiner_name': slot.examiner.name,
            'date': str(slot.date),
            'start_time': str(slot.start_time),
            'end_time': str(slot.end_time),
            'available_seats': slot.available_seats,
            'maximum_student_capacity': slot.maximum_student_capacity,
            'status': slot.status
        })

    return jsonify(result), 200


@admin_bp.route('/api/admin/slots/<int:id>/reschedule', methods=['PUT'])
@roles_required('admin')
def reschedule_slot(id):

    slot = ExamSlot.query.get(id)

    if not slot:
        return jsonify({'message': 'Slot not found'}), 404

    data = request.get_json()

    if 'date' in data:
        slot.date = datetime.strptime(data['date'], '%Y-%m-%d').date()

    if 'start_time' in data:
        slot.start_time = datetime.strptime(data['start_time'], '%H:%M').time()

    if 'end_time' in data:
        slot.end_time = datetime.strptime(data['end_time'], '%H:%M').time()

    if slot.end_time <= slot.start_time:
        db.session.rollback()
        return jsonify({'message': 'End time must be after start time'}), 400

    db.session.commit()

    return jsonify({'message': 'Slot rescheduled successfully'}), 200


@admin_bp.route('/api/admin/slots/<int:id>/examiner', methods=['PUT'])
@roles_required('admin')
def reassign_examiner(id):

    slot = ExamSlot.query.get(id)

    if not slot:
        return jsonify({'message': 'Slot not found'}), 404

    data = request.get_json()

    examiner = ExaminerProfile.query.get(data['examiner_id'])

    if not examiner:
        return jsonify({'message': 'Examiner not found'}), 404

    if examiner.status != 'Active' or examiner.user.status != 'Active':
        return jsonify({'message': 'Examiner is inactive'}), 400

    assignment = ExamExaminer.query.filter_by(
        exam_id=slot.exam_id,
        examiner_id=examiner.id
    ).first()

    if not assignment:
        return jsonify({
            'message': 'Examiner is not assigned to this exam'
        }), 400

    slot.examiner_id = examiner.id

    db.session.commit()

    return jsonify({
        'message': 'Examiner reassigned successfully'
    }), 200


@admin_bp.route('/api/admin/bookings', methods=['GET'])
@roles_required('admin')
def get_all_bookings():

    search = request.args.get('q', '')
    status = request.args.get('status')
    exam_id = request.args.get('exam_id')

    bookings = Booking.query.join(
        StudentProfile
    ).join(
        User
    ).join(
        ExamSlot
    ).join(
        Exam
    )

    if search:
        bookings = bookings.filter(
            (StudentProfile.name.ilike(f'%{search}%')) |
            (User.username.ilike(f'%{search}%')) |
            (Exam.exam_name.ilike(f'%{search}%'))
        )

    if status:
        bookings = bookings.filter(
            Booking.booking_status == status
        )

    if exam_id:
        bookings = bookings.filter(
            Exam.id == exam_id
        )

    bookings = bookings.all()

    result = []

    for booking in bookings:
        result.append({
            'booking_id': booking.id,
            'student_id': booking.student_id,
            'student_name': booking.studentprofile.name,
            'exam_name': booking.examslot.exam.exam_name,
            'slot_id': booking.slot_id,
            'examiner_name': booking.examslot.examiner.name,
            'exam_date': str(booking.examslot.date),
            'booking_status': booking.booking_status,
            'booking_date': str(booking.booking_date)
        })

    return jsonify(result), 200


@admin_bp.route('/api/admin/bookings/<int:id>/reschedule', methods=['PUT'])
@roles_required('admin')
def reschedule_booking(id):

    booking = Booking.query.get(id)

    if not booking:
        return jsonify({'message': 'Booking not found'}), 404

    if booking.booking_status != 'Booked':
        return jsonify({'message': 'Booking cannot be rescheduled'}), 400

    data = request.get_json() or {}

    new_slot = ExamSlot.query.get(data.get('slot_id'))

    if not new_slot:
        return jsonify({'message': 'New slot not found'}), 404

    old_slot = booking.examslot

    if new_slot.exam_id != old_slot.exam_id:
        return jsonify({'message': 'Cannot change to another exam'}), 400

    if new_slot.status != 'Available' or new_slot.available_seats <= 0:
        return jsonify({'message': 'No available seats in new slot'}), 400

    if new_slot.id == old_slot.id:
        return jsonify({'message': 'Already booked in this slot'}), 400

    old_slot.available_seats += 1

    if old_slot.status not in ['Cancelled', 'Completed']:
        old_slot.status = 'Available'

    new_slot.available_seats -= 1

    if new_slot.available_seats == 0:
        new_slot.status = 'Full'

    booking.slot_id = new_slot.id

    db.session.commit()

    return jsonify({'message': 'Booking rescheduled successfully'}), 200


@admin_bp.route('/api/admin/dashboard', methods=['GET'])
@roles_required('admin')
@cached('dashboard', TTL_DASHBOARD)
def admin_dashboard():

    total_students = StudentProfile.query.count()
    total_examiners = ExaminerProfile.query.count()
    total_courses = Course.query.count()
    total_exams = Exam.query.count()
    total_bookings = Booking.query.count()
    total_slots = ExamSlot.query.count()

    pending_evaluations = Booking.query.filter(
        Booking.booking_status == 'Booked',
        ~Booking.evaluation.has()
    ).count()

    completed_evaluations = Evaluation.query.filter_by(
        evaluation_status='Evaluated'
    ).count()

    return jsonify({
        'total_students': total_students,
        'total_examiners': total_examiners,
        'total_courses': total_courses,
        'total_exams': total_exams,
        'total_bookings': total_bookings,
        'total_slots': total_slots,
        'pending_evaluations': pending_evaluations,
        'completed_evaluations': completed_evaluations
    }), 200


@admin_bp.route('/api/admin/reports', methods=['GET'])
@roles_required('admin')
@cached('dashboard', TTL_DASHBOARD)
def admin_reports():

    total_bookings = Booking.query.count()

    booked = Booking.query.filter_by(
        booking_status='Booked'
    ).count()

    cancelled = Booking.query.filter_by(
        booking_status='Cancelled'
    ).count()

    completed = Booking.query.filter_by(
        booking_status='Completed'
    ).count()

    exams = Exam.query.all()

    exam_reports = []

    for exam in exams:

        bookings = Booking.query.join(ExamSlot).filter(
            ExamSlot.exam_id == exam.id
        ).all()

        exam_reports.append({
            'exam_id': exam.id,
            'exam_name': exam.exam_name,
            'total_bookings': len(bookings),
            'completed_bookings': sum(
                1 for b in bookings
                if b.booking_status == 'Completed'
            ),
            'cancelled_bookings': sum(
                1 for b in bookings
                if b.booking_status == 'Cancelled'
            ),
            'evaluations': Evaluation.query.join(Booking).join(
                ExamSlot
            ).filter(
                ExamSlot.exam_id == exam.id
            ).count()
        })

    return jsonify({
        'total_bookings': total_bookings,
        'booked': booked,
        'cancelled': cancelled,
        'completed': completed,
        'exam_reports': exam_reports
    }), 200