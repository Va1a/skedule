from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_login import current_user

from skedule import db
from skedule.models import Alert, Assignment, Day, Shift, Template, User
from skedule.utils import ymdToDateTime, ymdhmToDateTime

api = Blueprint("api", __name__)


def create_assignment_alert(user, alert_type, assignment, additional_data=None):
    content = {
        "title": f"Assignment {alert_type}",
        "message": "",
        "shift_name": assignment.shift.name,
        "shift_id": assignment.shift.id,
        "shift_date": assignment.shift.startTime.strftime("%A, %B %d, %Y"),
        "assignment_id": assignment.id,
    }

    if alert_type == "Updated":
        if assignment.request and assignment.confirmed:
            content["message"] = (
                f'Your shift request for "{assignment.shift.name}" has been approved.'
            )
        elif assignment.request and not assignment.confirmed:
            content["message"] = (
                f'Your shift request for "{assignment.shift.name}" is pending approval.'
            )
        elif not assignment.request and assignment.confirmed:
            content["message"] = f'You have been assigned to "{assignment.shift.name}".'
        else:
            content["message"] = (
                f'Your assignment for "{assignment.shift.name}" has been updated.'
            )
    elif alert_type == "Deleted":
        content["message"] = f'Your assignment for "{assignment.shift.name}" has been removed.'
    elif alert_type == "Created":
        content["message"] = f'You have been assigned to "{assignment.shift.name}".'

    if additional_data:
        content.update(additional_data)

    alert = Alert(recipient_user_id=user.id, content=content)
    db.session.add(alert)


@api.before_request
def beforeApiRequests():
    if not current_user.is_authenticated:
        abort(404)


@api.route("/api/shift/<int:shift_id>")
def apiShift(shift_id):
    shift = db.get_or_404(Shift, shift_id)
    return shift.toJSON()


@api.route("/api/shift/<int:shift_id>/assignment-table")
def apiShiftAssignmentTable(shift_id):
    shift = db.get_or_404(Shift, shift_id)
    return render_template("assignment_table.html", shift=shift)


@api.route("/api/assignment/<int:assignment_id>")
def apiAssignment(assignment_id):
    assignment = db.get_or_404(Assignment, assignment_id)
    return assignment.toJSON()


@api.route("/api/assignment/byUser/<int:user_id>")
def apiUserAssignment(user_id):
    assignments = Assignment.query.filter_by(user_id=user_id).all()
    return {"ids": [assignment.id for assignment in assignments]}


@api.route("/api/template/<int:template_id>")
def apiTemplate(template_id):
    template = db.get_or_404(Template, template_id)
    return template.toJSON()


@api.route("/api/template/byName/<string:name>")
def apiTemplateName(name):
    template = Template.query.filter_by(name=name).first_or_404()
    return template.toJSON()


@api.route("/api/template/all")
def apiListTemplate():
    return {
        "templates": [
            {"id": template.id, "name": template.name}
            for template in Template.query.all()
        ]
    }


@api.route("/api/shift/byDatetime/<string:datetime>")
def apiDatetimeShift(datetime):
    parsed_datetime = ymdhmToDateTime(datetime)
    if not parsed_datetime:
        abort(404)
    shift = Shift.query.filter_by(startTime=parsed_datetime).first_or_404()
    return redirect(url_for("api.apiShift", shift_id=shift.id))


@api.route("/api/day/<int:day_id>")
def apiDay(day_id):
    day = db.get_or_404(Day, day_id)
    return day.toJSON()


@api.route("/api/day/byDate/<string:date>")
def apiDateDay(date):
    parsed_date = ymdToDateTime(date)
    if not parsed_date:
        abort(404)
    day = Day.query.filter_by(date=parsed_date.date()).first_or_404()
    return redirect(url_for("api.apiDay", day_id=day.id))


@api.route("/api/user/byExternalID/<int:external_id>")
def apiUserExternal(external_id):
    user = db.one_or_404(db.select(User).filter(User.external_id == str(external_id)))
    return redirect(url_for("api.apiUser", user_id=user.id))


@api.route("/api/user/<int:user_id>")
def apiUser(user_id):
    user = db.get_or_404(User, user_id)
    return user.toJSON()


@api.route("/api/assignment/<int:assignment_id>/update", methods=["POST"])
def apiUpdateAssignment(assignment_id):
    assignment = db.get_or_404(Assignment, assignment_id)
    data = request.json

    original_request = assignment.request
    original_confirmed = assignment.confirmed

    assignment.request = data["request"]
    assignment.confirmed = data["confirmed"]

    if (
        original_request != assignment.request
        or original_confirmed != assignment.confirmed
    ):
        create_assignment_alert(assignment.user, "Updated", assignment)

    db.session.commit()
    return assignment.toJSON()


@api.route("/api/assignment/<int:assignment_id>/delete", methods=["POST"])
def apiDeleteAssignment(assignment_id):
    assignment = db.get_or_404(Assignment, assignment_id)
    create_assignment_alert(assignment.user, "Deleted", assignment)
    db.session.delete(assignment)
    db.session.commit()
    return {"deleted_id": assignment_id}


@api.route("/api/assignment/create", methods=["POST"])
def apiCreateAssignment():
    data = request.json
    shift = db.session.get(Shift, data["shift_id"])
    user = db.session.get(User, data["user_id"])
    if not shift or not user:
        return {"error": "Shift or user does not exist."}, 400
    if Assignment.query.filter_by(user=user, shift=shift).first():
        return {"error": "Assignment already exists for given shift-user combination."}, 400

    assignment = Assignment(user=user, shift=shift)
    db.session.add(assignment)
    db.session.flush()
    create_assignment_alert(user, "Created", assignment)
    db.session.commit()
    return assignment.toJSON()
