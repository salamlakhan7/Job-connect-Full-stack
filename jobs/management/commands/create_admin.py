from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management import CommandError
import os

class Command(BaseCommand):
    help = "Create an admin user from ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD."

    def handle(self, *args, **kwargs):
        User = get_user_model()
        username = os.environ.get("ADMIN_USERNAME")
        email = os.environ.get("ADMIN_EMAIL", "")
        password = os.environ.get("ADMIN_PASSWORD")

        if not username or not password:
            raise CommandError(
                "ADMIN_USERNAME and ADMIN_PASSWORD must be set to create an admin user."
            )

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS(f"Admin user '{username}' created."))
        else:
            self.stdout.write(f"Admin user '{username}' already exists.")
