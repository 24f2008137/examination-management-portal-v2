import os

from flask import Blueprint, jsonify, request, send_file

from model import db, ExportJob
from utils.decorators import roles_required, student_required
from tasks import EXPORT_DIR, export_student_history, send_daily_exam_reminders, send_monthly_report

jobs_bp = Blueprint('jobs', __name__)


def _job_json(job):
    return {
        'id': job.id,
        'status': job.status,                       # Pending / Processing / Completed / Failed
        'created_at': str(job.created_at),
        'completed_at': str(job.completed_at) if job.completed_at else None,
        'error': job.error,
        'download_url': f'/api/student/exports/{job.id}/download' if job.status == 'Completed' else None
    }


# Student: export exam history (user triggered async job)
@jobs_bp.route('/api/student/exports', methods=['POST'])
@student_required
def start_export(student):

    running = ExportJob.query.filter(
        ExportJob.student_id == student.id,
        ExportJob.status.in_(['Pending', 'Processing'])
    ).first()

    if running:
        return jsonify({
            'message': 'An export is already in progress',
            'job': _job_json(running)
        }), 409

    job = ExportJob(student_id=student.id)
    db.session.add(job)
    db.session.commit()

    try:
        result = export_student_history.delay(job.id)
        job.task_id = result.id
        db.session.commit()
    except Exception:                                   # broker (Redis) unreachable
        job.status, job.error = 'Failed', 'Background worker is unavailable'
        db.session.commit()
        return jsonify({'message': 'Could not queue the export. Is Redis / Celery running?'}), 503

    return jsonify({
        'message': 'Export started. You will be notified when it is ready.',
        'job': _job_json(job)
    }), 202


@jobs_bp.route('/api/student/exports', methods=['GET'])
@student_required
def list_exports(student):

    jobs = ExportJob.query.filter_by(
        student_id=student.id
    ).order_by(ExportJob.id.desc()).limit(10).all()

    return jsonify([_job_json(j) for j in jobs]), 200


@jobs_bp.route('/api/student/exports/<int:id>', methods=['GET'])
@student_required
def get_export(id, student):

    job = ExportJob.query.filter_by(id=id, student_id=student.id).first()

    if not job:
        return jsonify({'message': 'Export not found'}), 404

    return jsonify(_job_json(job)), 200


@jobs_bp.route('/api/student/exports/<int:id>/download', methods=['GET'])
@student_required
def download_export(id, student):

    job = ExportJob.query.filter_by(id=id, student_id=student.id).first()

    if not job:
        return jsonify({'message': 'Export not found'}), 404

    if job.status != 'Completed' or not job.file_path:
        return jsonify({'message': 'Export is not ready'}), 400


    filename = os.path.basename(job.file_path.replace('\\', '/'))
    path = os.path.join(EXPORT_DIR, filename)

    if not os.path.exists(path):
        return jsonify({'message': 'Export file not found on the server'}), 404

    return send_file(
        path,
        mimetype='text/csv',
        as_attachment=True,
        download_name='examination_history.csv'
    )


# Admin: run the scheduled jobs on demand (handy for demos / the viva)
@jobs_bp.route('/api/admin/jobs/daily-reminders', methods=['POST'])
@roles_required('admin')
def run_daily_reminders():
    try:
        result = send_daily_exam_reminders.delay()
    except Exception:
        return jsonify({'message': 'Could not queue the job. Is Redis / Celery running?'}), 503

    return jsonify({'message': 'Daily reminder job queued', 'task_id': result.id}), 202


@jobs_bp.route('/api/admin/jobs/monthly-report', methods=['POST'])
@roles_required('admin')
def run_monthly_report():

    data = request.get_json(silent=True) or {}
    year, month = data.get('year'), data.get('month')

    if (year or month):
        try:
            year, month = int(year), int(month)
            if not 1 <= month <= 12 or year < 2000:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({'message': 'Provide a valid year and month (1-12)'}), 400

    try:
        result = send_monthly_report.delay(year, month)
    except Exception:
        return jsonify({'message': 'Could not queue the job. Is Redis / Celery running?'}), 503

    return jsonify({'message': 'Monthly report job queued', 'task_id': result.id}), 202
