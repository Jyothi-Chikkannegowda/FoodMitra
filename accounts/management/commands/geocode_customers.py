"""
One-time backfill: geocodes any existing CustomerProfile that doesn't
already have latitude/longitude set (e.g. customers who registered
before this feature existed, or before address was collected at all).

Run with:
    python manage.py geocode_customers

Safe to run multiple times - it only processes customers that still
have latitude=None, so already-geocoded ones are skipped automatically.

NOTE: customers who registered before the address field existed will
have an empty address - those will simply be skipped (can't geocode
an empty string). They can add an address later via Edit Profile.
"""
import time
from django.core.management.base import BaseCommand
from accounts.models import CustomerProfile
from accounts.geocoding import geocode_address


class Command(BaseCommand):
    help = "Geocode address for customers that don't have coordinates yet"

    def handle(self, *args, **options):
        customers = CustomerProfile.objects.filter(latitude__isnull=True)
        total = customers.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("All customers already have coordinates. Nothing to do."))
            return

        self.stdout.write(f"Found {total} customer(s) without coordinates. Geocoding...")

        success_count = 0
        skip_count = 0
        fail_count = 0

        for customer in customers:
            if not customer.address or not customer.address.strip():
                skip_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"  - {customer.user.username} has no address on file. "
                        f"Skipped - they can add one via Edit Profile."
                    )
                )
                continue

            lat, lng = geocode_address(customer.address)

            if lat is not None and lng is not None:
                customer.latitude = lat
                customer.longitude = lng
                customer.save()
                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ {customer.user.username} -> ({lat:.5f}, {lng:.5f})"
                    )
                )
            else:
                fail_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"  ✗ {customer.user.username} - could not geocode "
                        f"'{customer.address}'. Fix the address and re-run this command."
                    )
                )

            # Nominatim's usage policy asks for max 1 request/second
            time.sleep(1)

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. {success_count} geocoded, {skip_count} skipped (no address), {fail_count} failed."
            )
        )