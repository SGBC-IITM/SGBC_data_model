import json
import sys

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError

from app1.utils import load_json_fixture


class Command(BaseCommand):
    help = "Load an SGBC JSON fixture transactionally."

    def add_arguments(self, parser):
        parser.add_argument("path", help="JSON fixture path, or - for stdin")

    def handle(self, *args, **options):
        try:
            if options["path"] == "-":
                result = load_json_fixture(sys.stdin)
            else:
                with open(options["path"], encoding="utf-8") as fixture:
                    result = load_json_fixture(fixture)
        except (OSError, json.JSONDecodeError, ValueError, TypeError, ValidationError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(self.style.SUCCESS(f"Loaded {len(result)} objects."))
