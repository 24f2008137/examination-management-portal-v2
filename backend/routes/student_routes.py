from flask import Blueprint, jsonify, request
from datetime import datetime, date
from model import db, Exam, ExamSlot, Booking, Evaluation
from utils.decorators import student_required

student_bp = Blueprint('student', __name__)


def _can_cancel(booking):
    exam = booking.examslot.exam
    return (
        booking.booking_status == 'Booked'
        and exam.exam_status == 'Booking Open'
        and date.today() <= exam.slot_booking_end_date
    )


@student_bp.route('/api/student/bookings', methods=['GET'])
@student_required
def get_student_bookings(student):

    bookings = Booking.query.filter_by(
        student_id=student.id
    ).all()

    result = []

    for booking in bookings:
        result.append({
            'booking_id': booking.id,
            'slot_id': booking.slot_id,
            'exam_id': booking.examslot.exam_id,
            'exam_name': booking.examslot.exam.exam_name,
            'examiner_name': booking.examslot.examiner.name,
            'exam_date': str(booking.examslot.date),
            'start_time': str(booking.examslot.start_time),
            'end_time': str(booking.examslot.end_time),
            'meeting_link': booking.examslot.meeting_link,
            'booking_status': booking.booking_status,
            'booking_date': str(booking.booking_date),
            'can_cancel': _can_cancel(booking)
        })

    return jsonify(result), 200


@student_bp.route('/api/student/bookings', methods=['POST'])
@student_required
def create_student_booking(student):

    data = request.get_json() or {}

    slot = ExamSlot.query.get(data.get('slot_id'))

    if not slot:
        return jsonify({'message': 'Slot not found'}), 404

    exam = Exam.query.get(slot.exam_id)

    if exam.exam_status != 'Booking Open':
        return jsonify({'message': 'Booking is not open'}), 400

    today = date.today()

    if today < exam.slot_booking_start_date:
        return jsonify({'message': 'Booking has not started yet'}), 400

    if today > exam.slot_booking_end_date:
        return jsonify({'message': 'Booking period is over'}), 400

    existing_booking = Booking.query.join(ExamSlot).filter(
        Booking.student_id == student.id,
        ExamSlot.exam_id == exam.id,
        Booking.booking_status == 'Booked'
    ).first()

    if existing_booking:
        return jsonify({'message': 'Already booked for this exam'}), 409

    if slot.status != 'Available' or slot.available_seats <= 0:
        return jsonify({'message': 'No available seats'}), 400

    # Claim a seat with ONE atomic UPDATE. Two students clicking at the same
    # moment can never both get the last seat: the WHERE clause is re-checked
    # by the database, and only the first UPDATE matches a row.
    claimed = ExamSlot.query.filter(
        ExamSlot.id == slot.id,
        ExamSlot.status == 'Available',
        ExamSlot.available_seats > 0
    ).update(
        {'available_seats': ExamSlot.available_seats - 1},
        synchronize_session=False
    )

    if not claimed:
        db.session.rollback()
        return jsonify({'message': 'No available seats'}), 400

    booking = Booking(
        slot_id=slot.id,
        student_id=student.id
    )
    db.session.add(booking)
    db.session.flush()

    db.session.refresh(slot)

    if slot.available_seats == 0:
        slot.status = 'Full'

    db.session.commit()

    return jsonify({
        'message': 'Booking successful',
        'booking_id': booking.id
    }), 201


@student_bp.route('/api/student/bookings/<int:id>', methods=['DELETE'])
@student_required
def cancel_student_booking(id, student):

    booking = Booking.query.filter_by(
        id=id,
        student_id=student.id
    ).first()

    if not booking:
        return jsonify({'message': 'Booking not found'}), 404

    if booking.booking_status != 'Booked':
        return jsonify({'message': 'Booking cannot be cancelled'}), 400

    if not _can_cancel(booking):
        return jsonify({'message': 'The booking deadline has passed'}), 400

    booking.booking_status = 'Cancelled'

    slot = booking.examslot

    ExamSlot.query.filter(ExamSlot.id == slot.id).update(
        {'available_seats': ExamSlot.available_seats + 1},
        synchronize_session=False
    )
    db.session.flush()
    db.session.refresh(slot)

    if slot.status == 'Full':
        slot.status = 'Available'

    db.session.commit()

    return jsonify({'message': 'Booking cancelled successfully'}), 200


@student_bp.route('/api/student/results', methods=['GET'])
@student_required
def get_student_results(student):

    evaluations = Evaluation.query.join(
        Booking
    ).join(
        ExamSlot
    ).join(
        Exam
    ).filter(
        Evaluation.student_id == student.id,
        Evaluation.evaluation_status == 'Evaluated',
        Exam.results_published.is_(True)
    ).all()

    result = []

    for evaluation in evaluations:

        scores = []

        for score in evaluation.score:
            scores.append({
                'criterion_name': score.exam_rubric.criterion_name,
                'max_marks': score.exam_rubric.max_marks,
                'marks_obtained': score.marks
            })

        result.append({
            'exam_name': evaluation.booking.examslot.exam.exam_name,
            'exam_date': str(evaluation.booking.examslot.date),
            'marks': evaluation.marks,
            'remarks': evaluation.remarks,
            'scores': scores
        })

    return jsonify(result), 200


@student_bp.route('/api/student/dashboard', methods=['GET'])
@student_required
def student_dashboard(student):

    bookings = Booking.query.filter_by(
        student_id=student.id
    ).all()

    total_bookings = len(bookings)

    upcoming_exams = []
    completed_exams = 0

    for booking in bookings:

        slot = booking.examslot

        if booking.booking_status == 'Completed':
            completed_exams += 1

        if (
            booking.booking_status == 'Booked'
            and slot.date >= datetime.now().date()
        ):
            upcoming_exams.append({
                'booking_id': booking.id,
                'exam_name': slot.exam.exam_name,
                'exam_date': str(slot.date),
                'start_time': str(slot.start_time),
                'examiner_name': slot.examiner.name
            })

    results_count = Evaluation.query.join(
        Booking
    ).join(
        ExamSlot
    ).join(
        Exam
    ).filter(
        Evaluation.student_id == student.id,
        Exam.results_published.is_(True)
    ).count()

    already_booked = {
        b.examslot.exam_id for b in bookings
        if b.booking_status in ('Booked', 'Completed')
    }

    open_exams = Exam.query.filter(Exam.exam_status == 'Booking Open').all()
    open_exam_ids = [e.id for e in open_exams if e.id not in already_booked]

    available_slots = ExamSlot.query.filter(
        ExamSlot.exam_id.in_(open_exam_ids),
        ExamSlot.status == 'Available',
        ExamSlot.available_seats > 0
    ).count() if open_exam_ids else 0

    return jsonify({
        'student_name': student.name,
        'total_bookings': total_bookings,
        'available_exams': len(open_exam_ids),
        'available_slots': available_slots,
        'upcoming_exams': upcoming_exams,
        'completed_exams': completed_exams,
        'published_results': results_count
    }), 200