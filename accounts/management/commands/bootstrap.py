import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Bootstrap a default superuser and pharmacy profile using env vars."

    def handle(self, *args, **options):
        email = os.environ.get("SU_EMAIL")
        password = os.environ.get("SU_PASSWORD")
        name = os.environ.get("SU_NAME", "Admin")
        role = os.environ.get("SU_ROLE", "pharmacy")

        if not email or not password:
            self.stdout.write("bootstrap: SU_EMAIL/SU_PASSWORD not set; skipping.")
            return

        User = get_user_model()

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "name": name,
                "role": role,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        if created:
            self.stdout.write(f"bootstrap: created superuser {email}")
        else:
            self.stdout.write(f"bootstrap: found existing user {email}")
            if not user.is_superuser or not user.is_staff:
                user.is_superuser = True
                user.is_staff = True

        # Always ensure password matches provided value
        user.set_password(password)
        user.save()

        # If pharmacy role, ensure Pharmacy profile exists
        try:
            from accounts.models import Pharmacy

            if role == "pharmacy":
                Pharmacy.objects.get_or_create(
                    pharmacy_id=user,
                    defaults={
                        "address": os.environ.get("SU_PHARMACY_ADDRESS", "Cloud"),
                        "license_number": None,
                    },
                )
                self.stdout.write("bootstrap: ensured pharmacy profile")
        except Exception as exc:  # pragma: no cover
            self.stderr.write(f"bootstrap: warning ensuring pharmacy profile: {exc}")

        self.stdout.write(self.style.SUCCESS("bootstrap: done"))

