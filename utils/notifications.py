from extensions import db
from models.activity_notification import ActivityNotification


def create_activity_notification(
    user_id,
    title,
    message,
    activity_type="general",
    reference_id=None,
    reference_type=None,
    action_url=None
):
    """
    Create a notification for a user.

    Parameters:
        user_id         -> Notification kis user ko milegi
        title           -> Notification title
        message         -> Notification message
        activity_type   -> message/order/appointment/etc.
        reference_id    -> Related record ka ID
        reference_type  -> Related record ka type
        action_url      -> Click karne par kahan jana hai
    """

    notification = ActivityNotification(
        user_id=user_id,
        title=title,
        message=message,
        activity_type=activity_type,
        reference_id=reference_id,
        reference_type=reference_type,
        action_url=action_url,
        is_read=False
    )

    db.session.add(notification)

    return notification


def create_bulk_activity_notification(
    user_ids,
    title,
    message,
    activity_type="general",
    reference_id=None,
    reference_type=None,
    action_url=None
):
    """
    Create same notification for multiple users.
    """

    notifications = []

    for user_id in user_ids:

        if not user_id:
            continue

        notification = ActivityNotification(
            user_id=user_id,
            title=title,
            message=message,
            activity_type=activity_type,
            reference_id=reference_id,
            reference_type=reference_type,
            action_url=action_url,
            is_read=False
        )

        db.session.add(notification)
        notifications.append(notification)

    return notifications


def mark_notification_as_read(notification):
    """
    Mark a notification as read.
    """

    notification.is_read = True

    return notification


def mark_all_notifications_as_read(user_id):
    """
    Mark all unread notifications of a user as read.
    """

    ActivityNotification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).update(
        {
            "is_read": True
        },
        synchronize_session=False
    )

    return True


def get_unread_notification_count(user_id):
    """
    Get unread notification count.
    """

    return ActivityNotification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).count()


def get_user_notifications(user_id, limit=20):
    """
    Get latest notifications of a user.
    """

    return (
        ActivityNotification.query
        .filter_by(user_id=user_id)
        .order_by(
            ActivityNotification.created_at.desc()
        )
        .limit(limit)
        .all()
    )

