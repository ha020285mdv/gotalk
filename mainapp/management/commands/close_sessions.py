from django.core.management.base import BaseCommand
from mainapp.models import Profile
from django.contrib.sessions.models import Session


class Command(BaseCommand):
    # to close all active sessions
    # command:            python manage.py close_sessions
    def handle(self, *args, **options):
        sessions = Session.objects.all()
        print(str(len(sessions)), ' active sessions were closed')
        sessions.delete()

