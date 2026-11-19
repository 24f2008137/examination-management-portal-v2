from flask import Blueprint, jsonify, request
from datetime import datetime, date, timedelta
from model import db, Exam, ExamExaminer, ExamSlot, Booking, ExamRubric, Evaluation, EvaluationScore
from utils.decorators import examiner_required

examiner_bp = Blueprint('examiner', __name__)


def _slot_is_editable(slot):
    """Slots can be changed/removed only before student booking begins."""
    return slot.exam.exam_status in ('Draft', 'Slot Creation')


def _has_overlap(examiner_id, slot_date, start, end, ignore_id=None):
    query = ExamSlot.query.filter(
        ExamSlot.examiner_id == examiner_id,
        ExamSlot.date == slot_date,
        ExamSlot.status != 'Cancelled',
        ExamSlot.start_time < end,
        ExamSlot.end_time > start
    )
    if ignore_id:
        query = query.filter(ExamSlot.id != ignore_id)
    return query.first() is not None


def _generate_viva_slots(start, end, duration_min, break_start=None, break_end=None):
    
    day = date(2000, 1, 1)
    step = timedelta(minutes=duration_min)
    cursor = datetime.combine(day, start)
    limit = datetime.combine(day, end)
    b_start = datetime.combine(day, break_start) if break_start else None
    b_end = datetime.combine(day, break_end) if break_end else None

    slots = []
    while cursor + step <= limit:
        if b_start and cursor < b_end and cursor + step > b_start:
            cursor = b_end                 # this slot would touch the break: resume after it
            continue
        slots.append((cursor.time(), (cursor + step).time()))
        cursor += step
    return slots


@examiner_bp.route('/api/examiner/slots', methods=['GET'])
@examiner_required
def get_examiner_slots(examiner):

    slots = ExamSlot.query.filter_by(
        examiner_id=examiner.id
    ).all()

    result = []

    for slot in slots:
        result.append({
            'id': slot.id,
            'exam_id': slot.exam_id,
            'exam_name': slot.exam.exam_name,
            'date': str(slot.date),
            'start_time': str(slot.start_time),
            'end_time': str(slot.end_time),
            'maximum_student_capacity': slot.maximum_student_capacity,
            'available_seats': slot.available_seats,
            'status': slot.status,
            'meeting_link': slot.meeting_link,
            'editable': _slot_is_editable(slot) and not slot.bookings
        })

    return jsonify(result), 200


@examiner_bp.route('/api/examiner/slots', methods=['POST'])
@examiner_required
def create_examiner_slot(examiner):

    if examiner.status != 'Active' or examiner.user.status != 'Active':
        return jsonify({'message': 'Examiner is inactive'}), 403

    data = request.get_json()

    exam = Exam.query.get(data['exam_id'])

    if not exam:
        return jsonify({'message': 'Exam not found'}), 404

    assignment = ExamExaminer.query.filter_by(
        exam_id=exam.id,
        examiner_id=examiner.id
    ).first()

    if not assignment:
        return jsonify({
            'message': 'You are not assigned to this exam'
        }), 403

    if exam.exam_status != 'Slot Creation':
        return jsonify({
            'message': 'Slot creation is not open'
        }), 400

    today = date.today()

    if not exam.slot_creation_start_date <= today <= exam.slot_creation_end_date:
        return jsonify({
            'message': 'Outside the slot creation period '
                       f'({exam.slot_creation_start_date} to {exam.slot_creation_end_date})'
        }), 400

    slot_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    start_time = datetime.strptime(data['start_time'], '%H:%M').time()
    end_time = datetime.strptime(data['end_time'], '%H:%M').time()
    capacity = int(data['maximum_student_capacity'])

    if end_time <= start_time:
        return jsonify({'message': 'End time must be after start time'}), 400

    if capacity < 1:
        return jsonify({'message': 'Capacity must be at least 1'}), 400

    #  Viva: one booking window per day -> auto-generated 1-student slots 
    if exam.exam_type == 'Viva':
        break_start = break_end = None
        if data.get('break_start') and data.get('break_end'):
            break_start = datetime.strptime(data['break_start'], '%H:%M').time()
            break_end = datetime.strptime(data['break_end'], '%H:%M').time()
            if break_end <= break_start:
                return jsonify({'message': 'Break end must be after break start'}), 400

        generated = _generate_viva_slots(start_time, end_time, exam.exam_duration, break_start, break_end)

        if not generated:
            return jsonify({
                'message': f'The window is shorter than one {exam.exam_duration}-minute viva'
            }), 400

        created, skipped = [], 0
        for s_start, s_end in generated:
            if _has_overlap(examiner.id, slot_date, s_start, s_end):
                skipped += 1
                continue
            slot = ExamSlot(
                exam_id=exam.id,
                examiner_id=examiner.id,
                date=slot_date,
                start_time=s_start,
                end_time=s_end,
                maximum_student_capacity=1,      # a viva is one student at a time
                available_seats=1,
                status='Available',
                meeting_link=data.get('meeting_link')
            )
            db.session.add(slot)
            created.append(slot)

        if not created:
            return jsonify({'message': 'You already have slots covering this whole window'}), 409

        db.session.commit()

        msg = f'{len(created)} viva slots created'
        if skipped:
            msg += f' ({skipped} skipped because they overlap your existing slots)'
        return jsonify({'message': msg, 'created': len(created), 'skipped': skipped}), 201

    if _has_overlap(examiner.id, slot_date, start_time, end_time):
        return jsonify({'message': 'You already have a slot that overlaps this time'}), 409

    slot = ExamSlot(
        exam_id=exam.id,
        examiner_id=examiner.id,
        date=slot_date,
        start_time=start_time,
        end_time=end_time,
        maximum_student_capacity=capacity,
        available_seats=capacity,
        status='Available',
        meeting_link=data.get('meeting_link')
    )

    db.session.add(slot)
    db.session.commit()

    return jsonify({
        'message': 'Exam slot created successfully',
        'slot_id': slot.id
    }), 201


@examiner_bp.route('/api/examiner/slots/<int:id>', methods=['PUT'])
@examiner_required
def update_examiner_slot(id, examiner):

    slot = ExamSlot.query.filter_by(
        id=id,
        examiner_id=examiner.id
    ).first()

    if not slot:
        return jsonify({'message': 'Slot not found'}), 404

    if not _slot_is_editable(slot) or slot.bookings:
        return jsonify({
            'message': 'Slots can only be updated before student booking begins'
        }), 400

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

    if slot.exam.exam_type == 'Viva':
        length = (datetime.combine(date.min, slot.end_time) - datetime.combine(date.min, slot.start_time))
        if length != timedelta(minutes=slot.exam.exam_duration):
            db.session.rollback()
            return jsonify({
                'message': f'A viva slot must be exactly {slot.exam.exam_duration} minutes long'
            }), 400
        data.pop('maximum_student_capacity', None)   # always 1 seat

    if _has_overlap(examiner.id, slot.date, slot.start_time, slot.end_time, ignore_id=slot.id):
        db.session.rollback()
        return jsonify({'message': 'You already have a slot that overlaps this time'}), 409

    if 'maximum_student_capacity' in data:
        capacity = int(data['maximum_student_capacity'])
        if capacity < 1:
            db.session.rollback()
            return jsonify({'message': 'Capacity must be at least 1'}), 400
        slot.maximum_student_capacity = capacity
        slot.available_seats = capacity      # safe: a slot with bookings cannot be edited

    if 'meeting_link' in data:
        slot.meeting_link = data['meeting_link']

    if 'status' in data:
        if data['status'] not in ['Available', 'Cancelled']:
            return jsonify({'message': 'Invalid slot status'}), 400

        slot.status = data['status']

    db.session.commit()

    return jsonify({'message': 'Slot updated successfully'}), 200


@examiner_bp.route('/api/examiner/slots/<int:id>', methods=['DELETE'])
@examiner_required
def delete_examiner_slot(id, examiner):

    slot = ExamSlot.query.filter_by(
        id=id,
        examiner_id=examiner.id
    ).first()

    if not slot:
        return jsonify({'message': 'Slot not found'}), 404

    if not _slot_is_editable(slot):
        return jsonify({
            'message': 'Slots can only be removed before student booking begins'
        }), 400

    if slot.bookings:
        return jsonify({
            'message': 'Cannot delete a slot with existing bookings'
        }), 400

    db.session.delete(slot)
    db.session.commit()

    return jsonify({'message': 'Slot deleted successfully'}), 200


@examiner_bp.route('/api/examiner/slots/<int:id>/bookings', methods=['GET'])
@examiner_required
def get_slot_bookings(id, examiner):

    slot = ExamSlot.query.filter_by(
        id=id,
        examiner_id=examiner.id
    ).first()

    if not slot:
        return jsonify({'message': 'Slot not found'}), 404

    bookings = Booking.query.filter_by(slot_id=id).all()

    result = []

    for booking in bookings:
        result.append({
            'booking_id': booking.id,
            'student_id': booking.student_id,
            'student_name': booking.studentprofile.name,
            'contact_details': booking.studentprofile.contact_details,
            'department': booking.studentprofile.department,
            'booking_status': booking.booking_status,
            'booking_date': str(booking.booking_date),
            'evaluated': booking.evaluation is not None,
            'marks': booking.evaluation.marks if booking.evaluation else None
        })

    return jsonify(result), 200


@examiner_bp.route('/api/examiner/evaluations', methods=['GET'])
@examiner_required
def get_pending_evaluations(examiner):

    status = request.args.get('status', 'pending')

    bookings = Booking.query.join(ExamSlot).filter(
        ExamSlot.examiner_id == examiner.id
    )

    if status == 'pending':
        bookings = bookings.filter(
            Booking.booking_status == 'Booked',
            ~Booking.evaluation.has()
        )

    bookings = bookings.all()

    result = []

    for booking in bookings:
        result.append({
            'booking_id': booking.id,
            'student_id': booking.student_id,
            'student_name': booking.studentprofile.name,
            'exam_id': booking.examslot.exam_id,
            'slot_id': booking.slot_id,
            'exam_name': booking.examslot.exam.exam_name,
            'exam_date': str(booking.examslot.date),
            'booking_status': booking.booking_status
        })

    return jsonify(result), 200


@examiner_bp.route('/api/examiner/bookings/<int:id>/evaluate', methods=['POST'])
@examiner_required
def evaluate_booking(id, examiner):

    booking = Booking.query.get(id)

    if not booking:
        return jsonify({'message': 'Booking not found'}), 404

    if booking.examslot.examiner_id != examiner.id:
        return jsonify({'message': 'Access denied'}), 403

    if booking.booking_status != 'Booked':
        return jsonify({'message': 'Booking is not active'}), 400

    if booking.evaluation:
        return jsonify({'message': 'Already evaluated'}), 409

    data = request.get_json() or {}

    scores = data.get('scores', [])

    if not isinstance(scores, list) or not scores:
        return jsonify({'message': 'Scores are required'}), 400

    rubrics = ExamRubric.query.filter_by(
        exam_id=booking.examslot.exam_id
    ).all()

    rubric_map = {rubric.id: rubric for rubric in rubrics}

    if not rubrics or len(scores) != len(rubrics):
        return jsonify({'message': 'All rubric scores are required'}), 400

    rubric_ids = [score.get('rubric_id') for score in scores]

    if len(set(rubric_ids)) != len(rubric_ids):
        return jsonify({'message': 'Duplicate rubric IDs'}), 400

    if set(rubric_ids) != set(rubric_map.keys()):
        return jsonify({'message': 'Invalid rubric IDs'}), 400

    total_marks = 0

    for score in scores:
        rubric = rubric_map[score['rubric_id']]
        marks = score.get('marks')

        if marks is None:
            return jsonify({'message': 'Marks are required'}), 400

        try:
            marks = float(marks)
        except (ValueError, TypeError):
            return jsonify({'message': 'Invalid marks'}), 400

        if not 0 <= marks <= rubric.max_marks:
            return jsonify({
                'message': f'Invalid marks for {rubric.criterion_name}'
            }), 400

        total_marks += marks

    evaluation = Evaluation(
        booking_id=booking.id,
        student_id=booking.student_id,
        examiner_id=examiner.id,
        marks=total_marks,
        remarks=data.get('remarks'),
        evaluation_status='Evaluated'
    )

    db.session.add(evaluation)
    db.session.flush()

    for score in scores:
        evaluation_score = EvaluationScore(
            evaluation_id=evaluation.id,
            rubric_id=score['rubric_id'],
            marks=float(score['marks'])
        )

        db.session.add(evaluation_score)

    booking.booking_status = 'Completed'

    db.session.commit()

    return jsonify({
        'message': 'Evaluation completed successfully',
        'evaluation_id': evaluation.id,
        'total_marks': total_marks
    }), 201


@examiner_bp.route('/api/examiner/bookings/<int:id>/evaluation', methods=['GET'])
@examiner_required
def get_booking_evaluation(id, examiner):

    booking = Booking.query.get(id)

    if not booking:
        return jsonify({'message': 'Booking not found'}), 404

    if booking.examslot.examiner_id != examiner.id:
        return jsonify({'message': 'Access denied'}), 403

    evaluation = booking.evaluation

    if not evaluation:
        return jsonify({'message': 'Evaluation not found'}), 404

    result = {
        'evaluation_id': evaluation.id,
        'booking_id': evaluation.booking_id,
        'student_id': evaluation.student_id,
        'marks': evaluation.marks,
        'remarks': evaluation.remarks,
        'evaluation_status': evaluation.evaluation_status,
        'scores': []
    }

    for score in evaluation.score:
        result['scores'].append({
            'rubric_id': score.rubric_id,
            'criterion_name': score.exam_rubric.criterion_name,
            'max_marks': score.exam_rubric.max_marks,
            'marks': score.marks
        })

    return jsonify(result), 200


@examiner_bp.route('/api/examiner/dashboard', methods=['GET'])
@examiner_required
def examiner_dashboard(examiner):

    total_exams = ExamExaminer.query.filter_by(
        examiner_id=examiner.id
    ).count()

    total_slots = ExamSlot.query.filter_by(
        examiner_id=examiner.id
    ).count()

    bookings = Booking.query.join(ExamSlot).filter(
        ExamSlot.examiner_id == examiner.id
    ).all()

    total_bookings = len(bookings)

    pending_evaluations = sum(
        1 for b in bookings
        if b.booking_status == 'Booked' and not b.evaluation
    )

    completed_evaluations = Evaluation.query.filter_by(
        examiner_id=examiner.id,
        evaluation_status='Evaluated'
    ).count()

    return jsonify({
        'examiner_name': examiner.name,
        'total_assigned_exams': total_exams,
        'total_slots': total_slots,
        'total_bookings': total_bookings,
        'pending_evaluations': pending_evaluations,
        'completed_evaluations': completed_evaluations
    }), 200


@examiner_bp.route('/api/examiner/exams', methods=['GET'])
@examiner_required
def get_assigned_exams(examiner):

    assignments = ExamExaminer.query.filter_by(examiner_id=examiner.id).all()

    result = []

    for assignment in assignments:
        exam = assignment.exam

        my_slots = [s for s in exam.examslot if s.examiner_id == examiner.id]
        my_bookings = [b for s in my_slots for b in s.bookings if b.booking_status != 'Cancelled']

        result.append({
            'id': exam.id,
            'exam_name': exam.exam_name,
            'course_name': exam.course.course_name,
            'exam_type': exam.exam_type,
            'exam_duration': exam.exam_duration,
            'maximum_marks': exam.maximum_marks,
            'exam_status': exam.exam_status,
            'slot_creation_start_date': str(exam.slot_creation_start_date),
            'slot_creation_end_date': str(exam.slot_creation_end_date),
            'my_slots': len(my_slots),
            'booked_students': len(my_bookings),
            'pending_evaluations': sum(
                1 for b in my_bookings if b.booking_status == 'Booked' and not b.evaluation
            )
        })

    return jsonify(result), 200


@examiner_bp.route('/api/examiner/exams/<int:id>/complete', methods=['PUT'])
@examiner_required
def complete_exam(id, examiner):

    assignment = ExamExaminer.query.filter_by(
        exam_id=id,
        examiner_id=examiner.id
    ).first()

    if not assignment:
        return jsonify({'message': 'You are not assigned to this exam'}), 403

    exam = assignment.exam

    if exam.exam_status == 'Completed':
        return jsonify({'message': 'Exam is already completed'}), 409

    if exam.exam_status != 'Closed':
        return jsonify({
            'message': 'An exam can be completed only after booking is closed'
        }), 400

    pending = Booking.query.join(ExamSlot).filter(
        ExamSlot.exam_id == exam.id,
        Booking.booking_status == 'Booked',
        ~Booking.evaluation.has()
    ).count()

    if pending:
        return jsonify({
            'message': f'{pending} evaluation(s) are still pending'
        }), 400

    exam.exam_status = 'Completed'

    for slot in exam.examslot:
        if slot.status != 'Cancelled':
            slot.status = 'Completed'

    db.session.commit()

    return jsonify({
        'message': 'Exam marked as completed',
        'exam_status': exam.exam_status
    }), 200
