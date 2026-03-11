from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import login_required

from skedule import db
from skedule.admin.forms import (
    AddShiftForm,
    AddTemplateForm,
    DeleteShiftForm,
    DeleteWeekScheduleForm,
    EditShiftForm,
    EditTemplateForm,
    NewWeekScheduleForm,
)
from skedule.features import (
    feature_required,
    get_feature_config,
    get_feature_entry,
    get_feature_entries,
    set_feature_config,
    set_feature_enabled,
)
from skedule.models import Day, LogEntry, LogField, Shift, Template, User
from skedule.utils import (
    daysOfCalendarWeek,
    getDayName,
    getLocalizedTime,
    oneWeekLater,
    oneWeekPrior,
    ymdToDateTime,
    ymdhmToDateTime,
)

admin = Blueprint("admin", __name__)
LOG_FIELD_TYPES = {
    "text": "Text",
    "time": "Time",
    "select": "Selection",
}


def hasValidFeatureCsrfToken():
    request_token = request.headers.get("X-Feature-CSRF-Token") or request.form.get(
        "feature_api_token"
    )
    session_token = session.get("feature_api_token")
    return bool(request_token and request_token == session_token)


def getLogFields():
    return LogField.query.order_by(LogField.position.asc(), LogField.id.asc()).all()


@admin.route("/admin/features", methods=["GET", "POST"])
@login_required
def manageFeatures():
    return render_template("features.html", features=get_feature_entries())


@admin.route("/features/<string:feature_name>")
@login_required
def featureDetail(feature_name):
    feature = get_feature_entry(feature_name)
    if feature is None:
        abort(404)

    if feature_name == "logs":
        return redirect(url_for("admin.configureLogFeature"))

    return render_template("feature_detail.html", feature=feature)


@admin.route("/api/admin/features/<string:feature_name>", methods=["POST"])
@login_required
def updateFeature(feature_name):
    if not hasValidFeatureCsrfToken():
        return jsonify({"error": "Invalid CSRF token."}), 403

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("enabled"), bool):
        return jsonify({"error": "Request must include a boolean `enabled` field."}), 400

    feature = set_feature_enabled(feature_name, data["enabled"])
    if feature is None:
        return jsonify({"error": "Unknown feature."}), 404

    return jsonify(
        {
            "feature": feature.toJSON(),
            "message": f"{feature.name} {'enabled' if feature.enabled else 'disabled'}.",
        }
    )


@admin.route("/api/admin/features/log/settings", methods=["POST"])
@login_required
def updateLogFeatureSettings():
    if not hasValidFeatureCsrfToken():
        return jsonify({"error": "Invalid CSRF token."}), 403

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request must include a JSON object."}), 400

    allowed_keys = {"require_relating_shift", "require_current_shift"}
    if not set(data).issubset(allowed_keys):
        return jsonify({"error": "Unknown log setting supplied."}), 400
    if not all(isinstance(value, bool) for value in data.values()):
        return jsonify({"error": "Log settings must be boolean values."}), 400

    feature = set_feature_config("logs", **data)
    return jsonify(
        {
            "feature": feature.toJSON(),
            "config": get_feature_config("logs"),
            "message": "Log settings updated.",
        }
    )


@admin.route("/features/log", methods=["GET", "POST"])
@login_required
def configureLogFeature():
    if request.method == "POST":
        if not hasValidFeatureCsrfToken():
            abort(403)

        label = request.form.get("label", "").strip()
        field_key = request.form.get("field_key", "").strip()
        field_type = request.form.get("field_type", "").strip()
        required = request.form.get("required") == "on"
        raw_options = request.form.get("options", "")

        if not label or not field_key:
            flash("Label and field key are required.", "danger")
            return redirect(url_for("admin.configureLogFeature"))

        if field_type not in LOG_FIELD_TYPES:
            flash("Unsupported field type.", "danger")
            return redirect(url_for("admin.configureLogFeature"))

        if LogField.query.filter_by(field_key=field_key).first():
            flash("Field key already exists.", "danger")
            return redirect(url_for("admin.configureLogFeature"))

        options = [
            option.strip()
            for option in raw_options.split(",")
            if option.strip()
        ]
        if field_type == "select" and not options:
            flash("Selection fields require at least one option.", "danger")
            return redirect(url_for("admin.configureLogFeature"))
        if field_type != "select":
            options = []

        current_position = db.session.scalar(db.select(db.func.max(LogField.position))) or 0
        field = LogField(
            label=label,
            field_key=field_key,
            field_type=field_type,
            required=required,
            options=options,
            position=current_position + 1,
        )
        db.session.add(field)
        db.session.commit()
        flash("Log field added.", "success")
        return redirect(url_for("admin.configureLogFeature"))

    return render_template(
        "feature_log_builder.html",
        feature_name="logs",
        field_types=LOG_FIELD_TYPES,
        fields=getLogFields(),
        log_config=get_feature_config("logs"),
    )


@admin.route("/features/log/field/<int:field_id>/delete", methods=["POST"])
@login_required
def deleteLogField(field_id):
    if not hasValidFeatureCsrfToken():
        abort(403)

    field = db.get_or_404(LogField, field_id)
    db.session.delete(field)
    db.session.commit()
    flash("Log field deleted.", "success")
    return redirect(url_for("admin.configureLogFeature"))


@admin.route("/api/admin/features/log/field/<int:field_id>", methods=["DELETE"])
@login_required
def deleteLogFieldApi(field_id):
    if not hasValidFeatureCsrfToken():
        return jsonify({"error": "Invalid CSRF token."}), 403

    field = db.get_or_404(LogField, field_id)
    db.session.delete(field)
    db.session.commit()
    return jsonify({"deleted_id": field_id, "message": "Log field deleted."})


@admin.route("/api/admin/features/log/fields/reorder", methods=["POST"])
@login_required
def reorderLogFields():
    if not hasValidFeatureCsrfToken():
        return jsonify({"error": "Invalid CSRF token."}), 403

    data = request.get_json(silent=True)
    ordered_ids = data.get("field_ids") if isinstance(data, dict) else None
    if not isinstance(ordered_ids, list) or not all(
        isinstance(field_id, int) for field_id in ordered_ids
    ):
        return jsonify({"error": "Request must include a list of integer field_ids."}), 400

    fields = LogField.query.order_by(LogField.position.asc(), LogField.id.asc()).all()
    existing_ids = {field.id for field in fields}
    if set(ordered_ids) != existing_ids:
        return jsonify({"error": "field_ids must match the current set of log fields."}), 400

    position_by_id = {field_id: index + 1 for index, field_id in enumerate(ordered_ids)}
    for field in fields:
        field.position = position_by_id[field.id]

    db.session.commit()
    return jsonify(
        {
            "message": "Log fields reordered.",
            "field_ids": ordered_ids,
        }
    )


def getCalendarWeek(inputWeekOf):
    if inputWeekOf:
        weekOf = ymdToDateTime(inputWeekOf)
        if not weekOf:
            abort(404)
        return daysOfCalendarWeek(weekOf)
    return daysOfCalendarWeek(getLocalizedTime())


def getWeekScheduleData(calendarWeek):
    weekdays = [
        {"name": getDayName(day.weekday()), "date": day.strftime("%m/%d")}
        for day in calendarWeek
    ]
    days = []
    unavail = False

    for day in calendarWeek:
        dayRow = Day.query.filter_by(date=day.date()).first()
        if dayRow:
            days.append(dayRow)
        else:
            unavail = True

    return weekdays, days, unavail


def createWeekSchedule(calendarWeek):
    for day in calendarWeek:
        dayRow = Day.query.filter_by(date=day.date()).first()
        if not dayRow:
            newDay = Day(name=day.date().strftime("%m/%d/%Y"), date=day.date())
            db.session.add(newDay)
    db.session.commit()


def deleteWeekSchedule(calendarWeek):
    for day in calendarWeek:
        dayRow = Day.query.filter_by(date=day.date()).first()
        if dayRow:
            for shift in dayRow.shifts:
                db.session.delete(shift)
            db.session.delete(dayRow)
    db.session.commit()


@admin.route("/schedule/configure", methods=["GET", "POST"])
@login_required
def configureSchedule():
    newWeekScheduleForm = NewWeekScheduleForm()
    deleteWeekScheduleForm = DeleteWeekScheduleForm()
    calendarWeek = getCalendarWeek(request.args.get("week"))
    weekOf = calendarWeek[0]
    weekdays, days, unavail = getWeekScheduleData(calendarWeek)

    if newWeekScheduleForm.submitNewWeek.data and newWeekScheduleForm.validate():
        createWeekSchedule(calendarWeek)
        flash(
            f"Schedule created for the week of {weekOf.strftime('%B %d, %Y')}",
            "success",
        )
        return redirect(
            url_for("admin.configureSchedule", week=weekOf.strftime("%Y-%m-%d"))
        )

    if (
        deleteWeekScheduleForm.submitDeleteWeek.data
        and deleteWeekScheduleForm.validate()
    ):
        deleteWeekSchedule(calendarWeek)
        flash(
            f"Schedule deleted for the week of {weekOf.strftime('%B %d, %Y')}",
            "success",
        )
        return redirect(
            url_for("admin.configureSchedule", week=weekOf.strftime("%Y-%m-%d"))
        )

    return render_template(
        "configure_schedule.html",
        deleteWeekScheduleForm=deleteWeekScheduleForm,
        newWeekScheduleForm=newWeekScheduleForm,
        unavail=unavail,
        weekdays=weekdays,
        weekOf=weekOf,
        days=days,
        owp=oneWeekPrior(weekOf),
        owl=oneWeekLater(weekOf),
        hours=[str(i).zfill(4) for i in range(800, 2400, 100)],
    )


@admin.route("/schedule/configure/add-shift", methods=["GET", "POST"])
@login_required
def addShift():
    inputDateTime = request.args.get("datetime")
    dateTime = ymdhmToDateTime(inputDateTime)
    if not dateTime:
        abort(404)
    if not Day.query.filter_by(date=dateTime.date()).first():
        abort(404)

    form = AddShiftForm()

    if form.validate_on_submit():
        startTime = ymdhmToDateTime(
            f"{dateTime.strftime('%Y-%m-%d-')}{form.startTime.data}"
        )
        if not startTime:
            flash("Invalid Start DateTime!", "danger")
            return redirect(url_for("admin.addShift", datetime=inputDateTime))

        day = Day.query.filter_by(date=dateTime.date()).first()
        shift = Shift(
            name=form.shiftName.data,
            startTime=startTime,
            duration=form.duration.data,
            maxEmployees=form.maxEmployees.data,
            minEmployees=form.minEmployees.data,
            day_id=day.id,
        )
        db.session.add(shift)
        db.session.commit()
        if form.employees.data:
            empToAdd = form.employees.data.replace(" ", "").split(",")
            for emp in empToAdd:
                if not emp.isdigit():
                    flash("Invalid Employee List!", "danger")
                    return redirect(url_for("admin.addShift", datetime=inputDateTime))
                employee = db.session.scalar(
                    db.select(User).filter(User.external_id == emp)
                )
                if not employee:
                    flash(f'Employee "{emp}" not found!', "danger")
                    return redirect(url_for("admin.addShift", datetime=inputDateTime))
                shift.employees.append(employee)
                db.session.commit()

        flash("Shift Added!", "success")
        return redirect(url_for("admin.configureSchedule", week=dateTime.date()))
    form.startTime.data = dateTime.strftime("%H%M")
    return render_template(
        "add_shift.html",
        form=form,
        startDate=dateTime.strftime("%m/%d/%Y"),
        startTime=form.startTime.data,
    )


@admin.route("/schedule/configure/shift/<int:shift_id>", methods=["GET", "POST"])
@login_required
def editShift(shift_id):
    shift = db.get_or_404(Shift, shift_id)
    date = shift.day.date
    form = EditShiftForm()
    deleteShiftForm = DeleteShiftForm()

    if request.method == "GET":
        form.shiftName.data = shift.name
        form.startTime.data = shift.startTime.strftime("%H%M")
        form.duration.data = str(shift.duration).zfill(4)
        form.maxEmployees.data = shift.maxEmployees
        form.minEmployees.data = shift.minEmployees

    if form.validate_on_submit():
        shift.name = form.shiftName.data
        shift.startTime = ymdhmToDateTime(
            f"{date.strftime('%Y-%m-%d-')}{form.startTime.data}"
        )
        shift.duration = form.duration.data
        shift.maxEmployees = form.maxEmployees.data
        shift.minEmployees = form.minEmployees.data
        db.session.commit()

        flash("Shift Updated!", "success")
        return redirect(url_for("main.viewShift", shift_id=shift.id))

    return render_template(
        "edit_shift.html",
        shift=shift,
        shift_id=shift_id,
        form=form,
        deleteShiftForm=deleteShiftForm,
        startDate=date.strftime("%m/%d/%Y"),
    )


@admin.route("/schedule/configure/shift/<int:shift_id>/delete", methods=["POST"])
@login_required
def deleteShift(shift_id):
    shift = db.get_or_404(Shift, shift_id)
    url = url_for("admin.configureSchedule", week=shift.day.date.strftime("%Y-%m-%d"))
    flash(f'Shift "{shift.name}" Deleted!', "success")
    db.session.delete(shift)
    db.session.commit()

    return redirect(url)


@admin.route("/schedule/configure/add-template", methods=["GET", "POST"])
@login_required
def templateManager():
    form = AddTemplateForm()
    hour = request.args.get("hour")
    if form.validate_on_submit():
        template = Template(
            name=form.shiftName.data,
            startTime=form.startTime.data,
            duration=form.duration.data,
            minEmployees=form.minEmployees.data,
            maxEmployees=form.maxEmployees.data,
        )
        db.session.add(template)
        db.session.commit()
        if form.employees.data:
            empToAdd = form.employees.data.replace(" ", "").split(",")
            for emp in empToAdd:
                if not emp.isdigit():
                    flash("Invalid Employee List!", "danger")
                    return redirect(url_for("admin.templateManager"))
                employee = db.session.scalar(
                    db.select(User).filter(User.external_id == emp)
                )
                if not employee:
                    flash(f'Employee "{emp}" not found!', "danger")
                    return redirect(url_for("admin.templateManager"))
                template.employees.append(employee)
                db.session.commit()
        flash("Template created", "success")
        return redirect(url_for("admin.viewTemplates"))
    if hour:
        form.startTime.data = hour
    return render_template("template_manager.html", form=form)


@admin.route("/schedule/configure/templates")
def viewTemplates():
    templates = Template.query.all()
    return render_template(
        "view_templates.html",
        templates=templates,
        hours=[str(i).zfill(4) for i in range(800, 2400, 100)],
    )


@admin.route("/admin/logs")
@login_required
@feature_required("logs")
def viewLogs():
    log_entries = LogEntry.query.order_by(LogEntry.created_at.desc()).all()
    return render_template(
        "view_logs.html",
        log_entries=log_entries,
    )


@admin.route("/schedule/configure/template/<int:template_id>", methods=["GET", "POST"])
@login_required
def editTemplate(template_id):
    template = db.get_or_404(Template, template_id)
    form = EditTemplateForm()
    if request.method == "GET":
        form.shiftName.data = template.name
        form.startTime.data = template.startTime
        form.duration.data = str(template.duration).zfill(4)
        form.maxEmployees.data = template.maxEmployees
        form.minEmployees.data = template.minEmployees
        form.employees.data = ", ".join(
            [str(emp.external_id) for emp in template.employees]
        )
    if form.validate_on_submit():
        template.name = form.shiftName.data
        template.startTime = form.startTime.data
        template.duration = form.duration.data
        template.maxEmployees = form.maxEmployees.data
        template.minEmployees = form.minEmployees.data

        if form.employees.data:
            empToAdd = form.employees.data.replace(" ", "").split(",")
            for emp in empToAdd:
                if not emp.isdigit():
                    flash("Invalid Employee List!", "danger")
                    return redirect(url_for("admin.editTemplate", template_id=template.id))
                employee = db.session.scalar(
                    db.select(User).filter(User.external_id == emp)
                )
                if not employee:
                    flash(f'Employee "{emp}" not found!', "danger")
                    return redirect(url_for("admin.editTemplate", template_id=template.id))
                template.employees.append(employee)
                db.session.commit()
        else:
            template.employees.clear()

        db.session.commit()
        flash("Template Updated!", "success")
        return redirect(url_for("admin.viewTemplates"))
    return render_template(
        "edit_template.html",
        form=form,
        template_id=template_id,
    )


@admin.route("/schedule/configure/template/<int:template_id>/delete", methods=["POST"])
@login_required
def deleteTemplate(template_id):
    template = db.get_or_404(Template, template_id)
    url = url_for("admin.viewTemplates")
    flash(f'Template "{template.name}" Deleted!', "success")
    db.session.delete(template)
    db.session.commit()

    return redirect(url)
