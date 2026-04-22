import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import RegularizationRequest, WFHRequest

logger = logging.getLogger("hrms")


@receiver(post_save, sender=RegularizationRequest)
def on_regularization_saved(sender, instance, created, **kwargs):
    """Notify manager on new request; notify employee on status change."""
    try:
        from tasks.attendance_tasks import dispatch_regularization_notification
        dispatch_regularization_notification.delay(instance.pk)
    except Exception:
        logger.exception("Signal failed on_regularization_saved id=%s", instance.pk)


@receiver(post_save, sender=WFHRequest)
def on_wfh_saved(sender, instance, created, **kwargs):
    """Notify manager on new WFH request; notify employee on decision."""
    try:
        from tasks.attendance_tasks import dispatch_wfh_notification
        dispatch_wfh_notification.delay(instance.pk)
    except Exception:
        logger.exception("Signal failed on_wfh_saved id=%s", instance.pk)
