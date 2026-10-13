"""
One-time backfill: geocodes any existing CookProfile that doesn't
already have latitude/longitude set (e.g. cooks who registered before
this feature existed).

Run with:
    python manage.py geocode_cooks

Safe to run multiple times - it only processes cooks that still have
latitude=None, so already-geocoded cooks are skipped automatically.
"""
import time
from django.core.management.base import BaseCommand
from accounts.models import CookProfile
from accounts.geocoding import geocode_address


class Command(BaseCommand):
    help = "Geocode home_address for cooks that don't have coordinates yet"

    def handle(self, *args, **options):
        cooks = CookProfile.objects.filter(latitude__isnull=True)
        total = cooks.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("All cooks already have coordinates. Nothing to do."))
            return

        self.stdout.write(f"Found {total} cook(s) without coordinates. Geocoding...")

        success_count = 0
        fail_count = 0

        for cook in cooks:
            lat, lng = geocode_address(cook.home_address)

            if lat is not None and lng is not None:
                cook.latitude = lat
                cook.longitude = lng
                cook.save()
                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ {cook.user.username} -> ({lat:.5f}, {lng:.5f})"
                    )
                )
            else:
                fail_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"  ✗ {cook.user.username} - could not geocode "
                        f"'{cook.home_address}'. Fix the address and re-run this command."
                    )
                )

            # Nominatim's usage policy asks for max 1 request/second
            time.sleep(1)

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. {success_count} geocoded successfully, {fail_count} failed."
            )
        )