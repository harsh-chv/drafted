from os import environ

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.db.models import Q

from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = "Create or update the Google OAuth SocialApp from environment variables."

    def handle(self, *args, **options):
        client_id = environ.get("GOOGLE_CLIENT_ID", "").strip()
        secret = environ.get("GOOGLE_CLIENT_SECRET", "").strip()

        if not client_id or not secret:
            self.stdout.write(
                self.style.WARNING(
                    "GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET is missing; skipped Google SocialApp sync."
                )
            )
            return

        domain = environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()
        if not domain:
            domain = next(
                (
                    host.strip().lstrip(".")
                    for host in settings.ALLOWED_HOSTS
                    if host.strip() and "*" not in host
                ),
                "localhost",
            )

        site, _ = Site.objects.update_or_create(
            id=settings.SITE_ID,
            defaults={"domain": domain, "name": "Drafted"},
        )

        google_apps = SocialApp.objects.filter(Q(provider="google") | Q(provider_id="google"))
        app = google_apps.filter(sites=site).order_by("id").first() or google_apps.order_by("id").first()

        if app is None:
            app = SocialApp(provider="google", name="Google")

        app.provider = "google"
        app.provider_id = ""
        app.name = "Google"
        app.client_id = client_id
        app.secret = secret
        app.key = ""
        app.save()
        app.sites.set([site])

        duplicate_ids = list(
            google_apps.exclude(id=app.id).filter(sites=site).values_list("id", flat=True)
        )
        if duplicate_ids:
            SocialApp.objects.filter(id__in=duplicate_ids).delete()

        self.stdout.write(self.style.SUCCESS("Google SocialApp synced."))
