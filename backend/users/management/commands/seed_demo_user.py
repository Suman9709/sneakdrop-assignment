import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create the local development demo administrator when it is absent."

    def handle(self, *args, **options):
        username = os.getenv("DEMO_ADMIN_USERNAME", "admin").strip()
        password = os.getenv("DEMO_ADMIN_PASSWORD", "Begusarai@1")

        if not username or not password:
            self.stderr.write("Demo user was not created: username or password is empty.")
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": "admin@example.test",
                "is_staff": True,
                "is_superuser": True,
            },
        )

        if not created:
            self.stdout.write(f"Demo user '{username}' already exists.")
            return

        user.set_password(password)
        user.save(update_fields=["password"])
        self.stdout.write(self.style.SUCCESS(f"Created demo user '{username}'."))
