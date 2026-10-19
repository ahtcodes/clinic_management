from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    jsonify
)

from flask_login import login_required, current_user

from extensions import db

from models.activity_notification import ActivityNotification


notifications_bp = Blueprint(
    "notifications",
    __name__,
    url_prefix="/notifications"
)


# =========================================================
# NOTIFICATION LIST
# =========================================================

@notifications_bp.route("/")
@login_required
def list_notifications():

    notifications = (
        ActivityNotification.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            ActivityNotification.created_at.desc()
        )
        .all()
    )

    unread_count = (
        ActivityNotification.query
        .filter_by(
            user_id=current_user.id,
            is_read=False
        )
        .count()
    )

    return render_template(
        "notifications/list.html",
        notifications=notifications,
        unread_count=unread_count
    )


# =========================================================
# MARK SINGLE NOTIFICATION AS READ
# =========================================================
#
# Supports BOTH:
# GET  -> normal browser request
# POST -> AJAX request from notification dropdown
#
# =========================================================

@notifications_bp.route(
    "/<int:notification_id>/read",
    methods=["GET", "POST"]
)
@login_required
def mark_as_read(notification_id):

    notification = (
        ActivityNotification.query
        .filter_by(
            id=notification_id,
            user_id=current_user.id
        )
        .first_or_404()
    )

    # -----------------------------------------------------
    # MARK AS READ
    # -----------------------------------------------------

    if not notification.is_read:

        notification.is_read = True

        db.session.commit()

    # -----------------------------------------------------
    # AJAX / FETCH REQUEST
    # -----------------------------------------------------

    if request.method == "POST" or request.headers.get(
        "X-Requested-With"
    ) == "XMLHttpRequest":

        unread_count = (
            ActivityNotification.query
            .filter_by(
                user_id=current_user.id,
                is_read=False
            )
            .count()
        )

        return jsonify({
            "success": True,
            "notification_id": notification.id,
            "is_read": True,
            "unread_count": unread_count
        })

    # -----------------------------------------------------
    # NORMAL BROWSER REQUEST
    # -----------------------------------------------------

    if notification.action_url:

        return redirect(
            notification.action_url
        )

    return redirect(
        url_for(
            "notifications.list_notifications"
        )
    )


# =========================================================
# MARK ALL AS READ
# =========================================================

@notifications_bp.route(
    "/read-all",
    methods=["GET", "POST"]
)
@login_required
def mark_all_as_read():

    ActivityNotification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update(
        {
            "is_read": True
        },
        synchronize_session=False
    )

    db.session.commit()

    # -----------------------------------------------------
    # AJAX RESPONSE
    # -----------------------------------------------------

    if request.method == "POST" or request.headers.get(
        "X-Requested-With"
    ) == "XMLHttpRequest":

        return jsonify({
            "success": True,
            "unread_count": 0
        })

    # -----------------------------------------------------
    # NORMAL RESPONSE
    # -----------------------------------------------------

    return redirect(
        url_for(
            "notifications.list_notifications"
        )
    )


# =========================================================
# DELETE SINGLE NOTIFICATION
# =========================================================

@notifications_bp.route(
    "/<int:notification_id>/delete",
    methods=["GET", "POST"]
)
@login_required
def delete_notification(notification_id):

    notification = (
        ActivityNotification.query
        .filter_by(
            id=notification_id,
            user_id=current_user.id
        )
        .first_or_404()
    )

    db.session.delete(notification)

    db.session.commit()

    if request.method == "POST" or request.headers.get(
        "X-Requested-With"
    ) == "XMLHttpRequest":

        unread_count = (
            ActivityNotification.query
            .filter_by(
                user_id=current_user.id,
                is_read=False
            )
            .count()
        )

        return jsonify({
            "success": True,
            "unread_count": unread_count
        })

    return redirect(
        url_for(
            "notifications.list_notifications"
        )
    )


# =========================================================
# UNREAD COUNT
# =========================================================

@notifications_bp.route(
    "/unread-count"
)
@login_required
def unread_count():

    count = (
        ActivityNotification.query
        .filter_by(
            user_id=current_user.id,
            is_read=False
        )
        .count()
    )

    return jsonify({
        "count": count
    })


# =========================================================
# LATEST NOTIFICATIONS
# =========================================================

@notifications_bp.route(
    "/latest"
)
@login_required
def latest_notifications():

    notifications = (
        ActivityNotification.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            ActivityNotification.created_at.desc()
        )
        .limit(10)
        .all()
    )

    data = []

    for notification in notifications:

        data.append(
            {
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "activity_type": notification.activity_type,
                "reference_id": notification.reference_id,
                "reference_type": notification.reference_type,
                "action_url": notification.action_url,
                "is_read": notification.is_read,
                "created_at": (
                    notification.created_at.isoformat()
                    if notification.created_at
                    else None
                )
            }
        )

    return jsonify({
        "notifications": data
    })

