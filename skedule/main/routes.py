from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import and_
from datetime import timedelta

from skedule.features import feature_required, get_feature_config, is_feature_enabled
from skedule.permissions import user_is_admin
from skedule import db
from skedule.models import Alert, Assignment, Day, LogEntry, LogField, Shift, User
from skedule.utils import (
    daysOfCalendarWeek,
    getDayName,
    getLocalizedTime,
    getWeek,
    oneWeekLater,
    oneWeekPrior,
    ymdToDateTime,
)

main = Blueprint("main", __name__)


def duration_to_timedelta(duration):
    duration_value = str(duration).zfill(4)
    hours = int(duration_value[:2])
    minutes = int(duration_value[2:])
    return timedelta(hours=hours, minutes=minutes)


def get_log_context_for_user(user):
    log_config = get_feature_config("logs")
    user_assignments = (
        Assignment.query.join(Shift)
        .filter(Assignment.user_id == user.id)
        .order_by(Shift.startTime.asc())
        .all()
    )
    now = getLocalizedTime().replace(tzinfo=None)
    related_shifts = sorted(
        (assignment.shift for assignment in user_assignments),
        key=lambda shift: abs((shift.startTime - now).total_seconds()),
    )[:50]
    current_shift = next(
        (
            shift
            for shift in related_shifts
            if shift.startTime <= now < shift.startTime + duration_to_timedelta(shift.duration)
        ),
        None,
    )
    return log_config, related_shifts, current_shift


def get_log_field_labels():
    fields = LogField.query.order_by(LogField.position.asc(), LogField.id.asc()).all()
    return {field.field_key: field.label for field in fields}


@main.before_app_request
def load_unseen_notifications():
    if current_user.is_authenticated:
        g.unseen_notifications_count = Alert.query.filter_by(
            recipient_user_id=current_user.id,
            seen=False,
        ).count()
    else:
        g.unseen_notifications_count = 0


@main.route("/")
@login_required
def home():
    current_week = getWeek(getLocalizedTime())
    weekdays = [
        {"name": getDayName(day.weekday()), "date": day.strftime("%m/%d")}
        for day in current_week
    ]
    start_date = current_week[0].date()
    end_date = current_week[-1].date()

    days_dict = {
        day.date: day
        for day in Day.query.filter(Day.date.between(start_date, end_date)).all()
    }
    days = [days_dict.get(day.date()) for day in current_week]

    user_assignments = (
        Assignment.query.join(Shift)
        .join(Day)
        .filter(
            Assignment.user_id == current_user.id,
            Day.date.between(start_date, end_date),
        )
        .all()
    )

    user_shifts = []
    user_shift_ids = set()
    for assignment in user_assignments:
        day_dt = assignment.shift.day.date
        user_shift_ids.add(assignment.shift.id)
        user_shifts.append(
            {
                "shift": assignment.shift,
                "assignment": assignment,
                "day_name": getDayName(day_dt.weekday()),
                "date": day_dt.strftime("%m/%d"),
                "time": assignment.shift.startTime.strftime("%-I:%M %p"),
            }
        )

    total_shifts = sum(len(day.shifts) if day else 0 for day in days)

    return render_template(
        "dashboard.html",
        time=getLocalizedTime(),
        weekdays=weekdays,
        days=days,
        user_shifts=user_shifts,
        user_shift_ids=user_shift_ids,
        total_shifts=total_shifts,
    )


@main.route("/schedule/shift/<int:shift_id>")
@login_required
def viewShift(shift_id):
    shift = db.get_or_404(Shift, shift_id)
    assignment = Assignment.query.filter_by(shift=shift, user=current_user).first()
    cancellable = bool(assignment and assignment.request)
    requestable = assignment is None
    can_manage_shift_logs = user_is_admin(current_user) and is_feature_enabled("logs")
    shift_logs = []
    if can_manage_shift_logs:
        shift_logs = (
            LogEntry.query.filter_by(related_shift_id=shift.id)
            .order_by(LogEntry.created_at.desc())
            .all()
        )
    return render_template(
        "shift.html",
        shift=shift,
        requestable=requestable,
        cancellable=cancellable,
        can_manage_shift_logs=can_manage_shift_logs,
        shift_logs=shift_logs,
    )


@main.route("/schedule/shift/<int:shift_id>/request", methods=["POST"])
@login_required
def requestShift(shift_id):
    shift = db.get_or_404(Shift, shift_id)
    if Assignment.query.filter_by(shift=shift, user=current_user).first():
        flash("You already have a request/assignment for this shift.", "danger")
    else:
        shift_request = Assignment(
            user=current_user,
            shift=shift,
            confirmed=True,
            request=True,
        )
        db.session.add(shift_request)
        db.session.commit()
        flash("Shift request submitted.", "success")
    return redirect(url_for("main.viewShift", shift_id=shift.id))


@main.route("/schedule/shift/<int:shift_id>/remove-request", methods=["POST"])
@login_required
def removeShiftRequest(shift_id):
    shift = db.get_or_404(Shift, shift_id)
    assignment = Assignment.query.filter_by(shift=shift, user=current_user).first()
    if not assignment:
        flash("You do not have a pending request for this shift.", "danger")
    else:
        db.session.delete(assignment)
        db.session.commit()
        flash("Shift request removed.", "success")
    return redirect(url_for("main.viewShift", shift_id=shift.id))


@main.route("/schedule")
@login_required
def schedule():
    unavail = False
    inputWeekOf = request.args.get("week")
    highlight = request.args.get("hl")
    if inputWeekOf:
        weekOf = ymdToDateTime(inputWeekOf)
        if not weekOf:
            abort(404)
        calendarWeek = daysOfCalendarWeek(weekOf)
    else:
        calendarWeek = daysOfCalendarWeek(getLocalizedTime())
    weekOf = calendarWeek[0]
    weekdays = [
        {"name": getDayName(day.weekday()), "date": day.strftime("%m/%d")}
        for day in calendarWeek
    ]
    days = []
    for day in calendarWeek:
        dayRow = Day.query.filter_by(date=day.date()).first()
        if dayRow:
            days.append(dayRow)
        else:
            unavail = True
    return render_template(
        "schedule.html",
        unavail=unavail,
        highlight=highlight,
        weekdays=weekdays,
        weekOf=weekOf,
        days=days,
        owp=oneWeekPrior(weekOf),
        owl=oneWeekLater(weekOf),
        hours=[str(i).zfill(4) for i in range(800, 2400, 100)],
    )


@main.route("/log")
@login_required
@feature_required("logs")
def log():
    fields = LogField.query.order_by(LogField.position.asc(), LogField.id.asc()).all()
    log_config, related_shifts, current_shift = get_log_context_for_user(current_user)

    return render_template(
        "log.html",
        fields=fields,
        log_config=log_config,
        related_shifts=related_shifts,
        current_shift=current_shift,
    )


@main.route("/log", methods=["POST"])
@login_required
@feature_required("logs")
def submitLog():
    fields = LogField.query.order_by(LogField.position.asc(), LogField.id.asc()).all()
    log_config, related_shifts, current_shift = get_log_context_for_user(current_user)
    related_shift_ids = {shift.id for shift in related_shifts}
    field_data = {}

    for field in fields:
        value = request.form.get(field.field_key, "").strip()
        if field.required and not value:
            flash(f'"{field.label}" is required.', "danger")
            return render_template(
                "log.html",
                fields=fields,
                log_config=log_config,
                related_shifts=related_shifts,
                current_shift=current_shift,
            )
        if value and field.field_type == "select" and value not in field.options:
            flash(f'Invalid value supplied for "{field.label}".', "danger")
            return render_template(
                "log.html",
                fields=fields,
                log_config=log_config,
                related_shifts=related_shifts,
                current_shift=current_shift,
            )
        field_data[field.field_key] = value

    related_shift_id = None
    if log_config.get("require_relating_shift"):
        if log_config.get("require_current_shift"):
            if not current_shift:
                flash("You must currently be within one of your assigned shifts to submit a log.", "danger")
                return render_template(
                    "log.html",
                    fields=fields,
                    log_config=log_config,
                    related_shifts=related_shifts,
                    current_shift=current_shift,
                )
            related_shift_id = current_shift.id
        else:
            selected_shift_id = request.form.get("related_shift_id", type=int)
            if not selected_shift_id or selected_shift_id not in related_shift_ids:
                flash("Please select one of your assigned shifts.", "danger")
                return render_template(
                    "log.html",
                    fields=fields,
                    log_config=log_config,
                    related_shifts=related_shifts,
                    current_shift=current_shift,
                )
            related_shift_id = selected_shift_id

    log_entry = LogEntry(
        user_id=current_user.id,
        related_shift_id=related_shift_id,
        field_data=field_data,
    )
    db.session.add(log_entry)
    db.session.commit()
    flash("Log entry submitted.", "success")
    return redirect(url_for("main.log"))


@main.route("/log/<int:log_id>")
@login_required
@feature_required("logs")
def viewLogEntry(log_id):
    log_entry = db.get_or_404(LogEntry, log_id)
    if log_entry.user_id != current_user.id and not user_is_admin(current_user):
        abort(403)

    return render_template(
        "log_detail.html",
        log_entry=log_entry,
        field_labels=get_log_field_labels(),
    )


@main.route("/leaderboard")
@login_required
@feature_required("leaderboard")
def leaderboard():
    return render_template("leaderboard.html")


@main.route("/discussion")
@login_required
@feature_required("discussion")
def discussion():
    return render_template("discussion.html")


@main.route("/upcoming")
@login_required
def upcoming():
    page = request.args.get("page", 1, type=int)
    no_pending = request.args.get("no-pending", False, type=bool)
    per_page = 10

    request_filter = Assignment.request.is_(False) if no_pending else True
    upcoming_assignments = (
        Assignment.query.join(Shift)
        .join(Day)
        .filter(
            and_(
                Assignment.user_id == current_user.id,
                request_filter,
            ),
            Day.date >= getLocalizedTime().date(),
        )
        .order_by(Shift.startTime.asc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return render_template(
        "upcoming.html",
        assignments=upcoming_assignments,
        no_pending=no_pending,
    )


@main.route("/pending-requests")
@login_required
def pendingRequests():
    page = request.args.get("page", 1, type=int)
    per_page = 10

    pending_assignments = (
        Assignment.query.join(Shift)
        .join(Day)
        .filter(and_(Assignment.user_id == current_user.id, Assignment.request.is_(True)))
        .order_by(Shift.startTime.asc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return render_template("pending_requests.html", assignments=pending_assignments)


@main.route("/roster")
@login_required
def roster():
    users = User.query.all()
    return render_template("roster.html", users=users)


@main.route("/alerts")
@login_required
def notifications():
    page = request.args.get("page", 1, type=int)
    per_page = 20

    alerts = Alert.query.filter_by(recipient_user_id=current_user.id).order_by(
        Alert.timestamp.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    unseen_alert_ids = {alert.id for alert in alerts.items if not alert.seen}

    alert_ids = [alert.id for alert in alerts.items]
    if alert_ids:
        Alert.query.filter(
            Alert.id.in_(alert_ids),
            Alert.seen.is_(False),
        ).update({"seen": True}, synchronize_session=False)
        db.session.commit()

    return render_template(
        "notifications.html",
        alerts=alerts,
        unseen_alert_ids=unseen_alert_ids,
    )


@main.route("/alerts/<int:alert_id>/dismiss", methods=["POST"])
@login_required
def dismiss_alert(alert_id):
    alert = db.get_or_404(Alert, alert_id)
    if alert.recipient_user_id != current_user.id:
        abort(403)

    db.session.delete(alert)
    db.session.commit()
    flash("Alert dismissed.", "success")

    return redirect(url_for("main.notifications"))


@main.route("/static/<path:path>")
def staticFiles(path):
    return send_from_directory("static", path)
