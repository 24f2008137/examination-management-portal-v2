from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from model import ExaminerProfile, Exam, ExamExaminer, ExamSlot, ExamRubric
from utils.cache import cached, TTL_EXAMS, TTL_EXAM_DETAIL, TTL_RUBRICS, TTL_SLOTS

api_bp = Blueprint('api', __name__)


@api_bp.route('/api/exams', methods=['GET'])
@jwt_required()
@cached('exams', TTL_EXAMS, per_user=('examiner',))
def get_exams():

    role = get_jwt().get('role')
    user_id = int(get_jwt_identity())

    search = request.args.get('q', '')
    exam_type = request.args.get('type')
    status = request.args.get('status')
    course_id = request.args.get('course_id')

    exams = Exam.query

    if role == 'admin':
        pass

    elif role == 'examiner':
        exams = exams.join(
            ExamExaminer,
            Exam.id == ExamExaminer.exam_id
        ).join(
            ExaminerProfile,
            ExamExaminer.examiner_id == ExaminerProfile.id
        ).filter(ExaminerProfile.user_id == user_id)

    elif role == 'student':
        exams = exams.filter(Exam.exam_status != 'Draft')

    else:
        return jsonify({'message': 'Access denied'}), 403

    if search:
        exams = exams.filter(Exam.exam_name.ilike(f'%{search}%'))

    if exam_type:
        exams = exams.filter(Exam.exam_type == exam_type)

    if status:
        exams = exams.filter(Exam.exam_status == status)

    if course_id:
        exams = exams.filter(Exam.course_id == course_id)

    exams = exams.all()

    result = []

    for exam in exams:
        result.append({
            'id': exam.id,
            'course_id': exam.course_id,
            'course_name': exam.course.course_name,
            'exam_name': exam.exam_name,
            'exam_type': exam.exam_type,
            'exam_duration': exam.exam_duration,
            'maximum_marks': exam.maximum_marks,
            'slot_creation_start_date': str(exam.slot_creation_start_date),
            'slot_creation_end_date': str(exam.slot_creation_end_date),
            'slot_booking_start_date': str(exam.slot_booking_start_date),
            'slot_booking_end_date': str(exam.slot_booking_end_date),
            'exam_status': exam.exam_status,
            'results_published': exam.results_published
        })

    return jsonify(result), 200


@api_bp.route('/api/exams/<int:id>', methods=['GET'])
@jwt_required()
@cached('exams', TTL_EXAM_DETAIL)
def get_exam(id):

    exam = Exam.query.get(id)

    if not exam or (get_jwt().get('role') == 'student' and exam.exam_status == 'Draft'):
        return jsonify({'message': 'Exam not found'}), 404

    return jsonify({
        'id': exam.id,
        'course_id': exam.course_id,
        'course_name': exam.course.course_name,
        'exam_name': exam.exam_name,
        'exam_type': exam.exam_type,
        'exam_duration': exam.exam_duration,
        'maximum_marks': exam.maximum_marks,
        'slot_creation_start_date': str(exam.slot_creation_start_date),
        'slot_creation_end_date': str(exam.slot_creation_end_date),
        'slot_booking_start_date': str(exam.slot_booking_start_date),
        'slot_booking_end_date': str(exam.slot_booking_end_date),
        'exam_status': exam.exam_status,
        'results_published': exam.results_published,
        'exam_instructions': exam.exam_instructions
    }), 200


@api_bp.route('/api/exams/<int:id>/rubrics', methods=['GET'])
@jwt_required()
@cached('rubrics', TTL_RUBRICS)
def get_rubrics(id):

    exam = Exam.query.get(id)

    if not exam or (get_jwt().get('role') == 'student' and exam.exam_status == 'Draft'):
        return jsonify({'message': 'Exam not found'}), 404

    rubrics = ExamRubric.query.filter_by(exam_id=id).all()

    result = []

    for rubric in rubrics:
        result.append({
            'id': rubric.id,
            'exam_id': rubric.exam_id,
            'criterion_name': rubric.criterion_name,
            'max_marks': rubric.max_marks,
            'weightage': rubric.weightage,
            'description': rubric.description
        })

    return jsonify(result), 200


@api_bp.route('/api/exams/<int:id>/slots', methods=['GET'])
@jwt_required()
@cached('slots', TTL_SLOTS)
def get_exam_slots(id):

    exam = Exam.query.get(id)

    if not exam:
        return jsonify({'message': 'Exam not found'}), 404

    role = get_jwt().get('role')

    slots = ExamSlot.query.filter_by(exam_id=id)

    if role == 'student':
        
        slots = slots.filter(ExamSlot.status.in_(['Available', 'Full']))

        if exam.exam_status != 'Booking Open':
            return jsonify([]), 200

    elif role not in ['admin', 'examiner']:
        return jsonify({'message': 'Access denied'}), 403

    slots = slots.order_by(ExamSlot.date, ExamSlot.start_time).all()

    result = []

    for slot in slots:
        result.append({
            'id': slot.id,
            'exam_id': slot.exam_id,
            'examiner_id': slot.examiner_id,
            'examiner_name': slot.examiner.name,
            'date': str(slot.date),
            'start_time': str(slot.start_time),
            'end_time': str(slot.end_time),
            'maximum_student_capacity': slot.maximum_student_capacity,
            'available_seats': slot.available_seats,
            'status': slot.status,
            'meeting_link': slot.meeting_link
        })

    return jsonify(result), 200
