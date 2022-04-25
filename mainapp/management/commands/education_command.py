from django.core.management.base import BaseCommand
from mainapp.models import Profile
from django.contrib.sessions.models import Session


class Command(BaseCommand):
    #show profiles
    help = "I'm learning"

    def handle(self, *args, **options):
        profiles = Profile.objects.all()

        for profile in profiles:
            print(profile.user)
