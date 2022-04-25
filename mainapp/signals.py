from django.db.models.signals import post_save
from django.core.signals import request_finished
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile


@receiver(post_save, sender=User)
def post_save_create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

#    education example
# @receiver(request_finished)
# def my_callback(sender, **kwargs):
#     print("Request finished!")
