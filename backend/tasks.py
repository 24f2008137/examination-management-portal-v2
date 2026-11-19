"""Celery batch jobs.

    emp.send_daily_exam_reminders   scheduled (daily)   -> students (email + Google Chat)
    emp.send_monthly_report         scheduled (monthly) -> admin (HTML email)
    emp.export_student_history      user triggered      -> CSV file + alert
"""
import csv
import logging
import os
from collections import Counter
from datetime import date, datetime, timedelta
from html import escape

from sqlalchemy import func

from celery_app import celery
from model import (db, User, StudentProfile, ExaminerProfile, Exam, ExamSlot,
                   Booking, Evaluation, ExportJob)
from utils.notify import send_email, send_gchat, BASE_DIR

log = logging.getLogger(__name__)

EXPORT_DIR = os.path.join(BASE_DIR, 'instance', 'exports')
REMINDER_DAYS_AHEAD = int(os.environ.get('REMINDER_DAYS_AHEAD', 1))   # today + tomorrow


def _t(value):
    return value.strftime('%I:%M %p').lstrip('0')


# a. Daily examination reminder
def build_reminders(today=None, days_ahead=REMINDER_DAYS_AHEAD):
    """{student_profile: [booking, ...]} for bookings happening from today until
    today + days_ahead. Cancelled bookings and inactive students are skipped."""
    today = today or date.today()
    last = today + timedelta(days=days_ahead)

    bookings = (Booking.query.join(ExamSlot)
                .filter(Booking.booking_status == 'Booked',
                        ExamSlot.date >= today, ExamSlot.date <= last)
                .order_by(ExamSlot.date, ExamSlot.start_time).all())

    grouped = {}
    for b in bookings:
        if b.studentprofile.user.status == 'Active':
            grouped.setdefault(b.studentprofile, []).append(b)
    return grouped


def _reminder_lines(bookings):
    lines = []
    for b in bookings:
        slot, exam = b.examslot, b.examslot.exam
        lines.append({
            'exam': exam.exam_name,
            'when': f"{slot.date:%A, %d %b %Y}, {_t(slot.start_time)} - {_t(slot.end_time)}",
            'examiner': slot.examiner.name,
            'link': slot.meeting_link,
            'instructions': exam.exam_instructions or 'No special instructions.',
        })
    return lines


@celery.task(name='emp.send_daily_exam_reminders')
def send_daily_exam_reminders():
    sent_mail = sent_chat = 0

    for student, bookings in build_reminders().items():
        lines = _reminder_lines(bookings)

        
        text = [f"Exam reminder for {student.name}"]
        for l in lines:
            text.append(f"* {l['exam']} - {l['when']}\n"
                        f"  Examiner: {l['examiner']}\n"
                        f"  Instructions: {l['instructions']}"
                        + (f"\n  Meeting link: {l['link']}" if l['link'] else ''))
        text = '\n'.join(text)


        items = ''.join(
            f"<li><b>{escape(l['exam'])}</b><br>{escape(l['when'])}<br>"
            f"Examiner: {escape(l['examiner'])}<br>"
            f"Instructions: {escape(l['instructions'])}"
            + (f"<br>Meeting link: <a href=\"{escape(l['link'])}\">{escape(l['link'])}</a>" if l['link'] else '')
            + "</li>" for l in lines)
        html = (f"<p>Hello {escape(student.name)},</p>"
                f"<p>You have the following upcoming examination(s):</p><ul>{items}</ul>"
                f"<p>Good luck!<br>Examination Management Portal</p>")

        if send_email(student.user.email, 'Reminder: upcoming examination', html, text):
            sent_mail += 1
        if send_gchat(text):
            sent_chat += 1

    log.info('Daily reminders: %s emails, %s chat messages', sent_mail, sent_chat)
    return {'emails_sent': sent_mail, 'chat_messages_sent': sent_chat}



# b. Monthly examination report
def _month_range(year, month):
    start = date(year, month, 1)
    end = date(year + (month == 12), (month % 12) + 1, 1)      # first day of next month
    return start, end


def collect_monthly_stats(year, month):
    start, end = _month_range(year, month)
    start_dt, end_dt = datetime.combine(start, datetime.min.time()), datetime.combine(end, datetime.min.time())

    exams_conducted = (db.session.query(func.count(func.distinct(ExamSlot.exam_id)))
                       .join(Booking, Booking.slot_id == ExamSlot.id)
                       .filter(ExamSlot.date >= start, ExamSlot.date < end,
                               Booking.booking_status != 'Cancelled').scalar())

    students_evaluated = (db.session.query(func.count(func.distinct(Evaluation.student_id)))
                          .filter(Evaluation.evaluation_date >= start_dt,
                                  Evaluation.evaluation_date < end_dt,
                                  Evaluation.evaluation_status == 'Evaluated').scalar())

    completed_bookings = (Booking.query.join(ExamSlot)
                          .filter(Booking.booking_status == 'Completed',
                                  ExamSlot.date >= start, ExamSlot.date < end).count())

    pending_evaluations = (Booking.query.join(ExamSlot)
                           .filter(Booking.booking_status == 'Booked',
                                   ~Booking.evaluation.has(),
                                   ExamSlot.date < end).count())

    rows = (db.session.query(Evaluation.examiner_id, func.count(Evaluation.id))
            .filter(Evaluation.evaluation_date >= start_dt, Evaluation.evaluation_date < end_dt)
            .group_by(Evaluation.examiner_id).all())
    top = Counter(dict(rows)).most_common(5)
    active_examiners = [{'name': db.session.get(ExaminerProfile, eid).name,
                         'department': db.session.get(ExaminerProfile, eid).department or '-',
                         'evaluations': n} for eid, n in top]

    return {
        'period': f'{start:%B %Y}',
        'exams_conducted': exams_conducted or 0,
        'students_evaluated': students_evaluated or 0,
        'completed_bookings': completed_bookings,
        'pending_evaluations': pending_evaluations,
        'active_examiners': active_examiners,
    }


def render_monthly_report_html(stats):
    cards = ''.join(
        f"<td style='padding:14px;border:1px solid #dee2e6;text-align:center'>"
        f"<div style='font-size:26px;font-weight:bold;color:#0d6efd'>{value}</div>"
        f"<div style='color:#6c757d;font-size:13px'>{label}</div></td>"
        for label, value in [('Examinations conducted', stats['exams_conducted']),
                             ('Students evaluated', stats['students_evaluated']),
                             ('Completed bookings', stats['completed_bookings']),
                             ('Pending evaluations', stats['pending_evaluations'])])

    if stats['active_examiners']:
        rows = ''.join(
            f"<tr><td style='padding:6px 10px;border:1px solid #dee2e6'>{i}</td>"
            f"<td style='padding:6px 10px;border:1px solid #dee2e6'>{escape(e['name'])}</td>"
            f"<td style='padding:6px 10px;border:1px solid #dee2e6'>{escape(e['department'])}</td>"
            f"<td style='padding:6px 10px;border:1px solid #dee2e6;text-align:right'>{e['evaluations']}</td></tr>"
            for i, e in enumerate(stats['active_examiners'], 1))
        examiners = (f"<table style='border-collapse:collapse;width:100%'>"
                     f"<tr style='background:#f8f9fa'><th style='padding:6px 10px;border:1px solid #dee2e6'>#</th>"
                     f"<th style='padding:6px 10px;border:1px solid #dee2e6;text-align:left'>Examiner</th>"
                     f"<th style='padding:6px 10px;border:1px solid #dee2e6;text-align:left'>Department</th>"
                     f"<th style='padding:6px 10px;border:1px solid #dee2e6;text-align:right'>Evaluations</th></tr>"
                     f"{rows}</table>")
    else:
        examiners = '<p style="color:#6c757d">No evaluations were recorded this month.</p>'

    return (f"<div style='font-family:Arial,Helvetica,sans-serif;max-width:640px;margin:auto'>"
            f"<h2 style='color:#212529'>Monthly Examination Report - {escape(stats['period'])}</h2>"
            f"<table style='border-collapse:collapse;width:100%;margin-bottom:24px'><tr>{cards}</tr></table>"
            f"<h3>Most active examiners</h3>{examiners}"
            f"<p style='color:#6c757d;font-size:12px;margin-top:24px'>Generated automatically on "
            f"{datetime.now():%d %b %Y %H:%M} by the Examination Management Portal.</p></div>")


@celery.task(name='emp.send_monthly_report')
def send_monthly_report(year=None, month=None):
    """Report for the previous calendar month unless year/month are given."""
    if not (year and month):
        last_month_end = date.today().replace(day=1) - timedelta(days=1)
        year, month = last_month_end.year, last_month_end.month

    stats = collect_monthly_stats(int(year), int(month))
    html = render_monthly_report_html(stats)

    admins = User.query.filter_by(role='admin', status='Active').all()
    sent = sum(send_email(a.email, f"Monthly Examination Report - {stats['period']}", html) for a in admins)
    return {'period': stats['period'], 'sent_to': sent, 'stats': stats}



def _csv_safe(value):
    value = '' if value is None else str(value)
    return "'" + value if value[:1] in ('=', '+', '-', '@') else value


@celery.task(bind=True, name='emp.export_student_history')
def export_student_history(self, job_id):
    job = db.session.get(ExportJob, job_id)
    if job is None:
        return {'status': 'Failed', 'error': 'job not found'}

    try:
        job.status = 'Processing'
        db.session.commit()

        student = db.session.get(StudentProfile, job.student_id)
        bookings = (Booking.query.join(ExamSlot)
                    .filter(Booking.student_id == student.id)
                    .order_by(ExamSlot.date).all())

        os.makedirs(EXPORT_DIR, exist_ok=True)
        path = os.path.join(EXPORT_DIR, f'history_student{student.id}_job{job.id}.csv')

        with open(path, 'w', newline='', encoding='utf-8-sig') as fh:   # utf-8-sig: opens cleanly in Excel
            w = csv.writer(fh)
            w.writerow(['Student ID', 'Examination Name', 'Course', 'Examination Date',
                        'Examiner', 'Marks Obtained', 'Booking Status'])
            for b in bookings:
                slot, exam, ev = b.examslot, b.examslot.exam, b.evaluation
                if ev is None or ev.evaluation_status != 'Evaluated':
                    marks = ''
                elif exam.results_published:
                    marks = ev.marks
                else:
                    marks = 'Result not published'
                w.writerow([student.id, _csv_safe(exam.exam_name), _csv_safe(exam.course.course_name),
                            slot.date, _csv_safe(slot.examiner.name), marks, b.booking_status])

        job.file_path = path
        job.status = 'Completed'
        job.completed_at = datetime.now()
        db.session.commit()

        #  alert the student 
        msg = f"Hello {student.name}, your examination history export is ready. Open the dashboard to download it."
        send_email(student.user.email, 'Your examination history export is ready',
                   f"<p>{escape(msg)}</p>", msg)
        send_gchat(f"{student.name}: your examination history export is ready.")
        return {'status': 'Completed', 'rows': len(bookings)}

    except Exception as exc:                                  # noqa: BLE001
        db.session.rollback()
        job = db.session.get(ExportJob, job_id)
        job.status, job.error = 'Failed', str(exc)[:500]
        db.session.commit()
        log.exception('CSV export failed for job %s', job_id)
        return {'status': 'Failed', 'error': str(exc)}
