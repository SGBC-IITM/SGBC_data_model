import json

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError

from app1.utils import compile_json_draft


class Command(BaseCommand):
    help = "Compile a readable JSON draft into a canonical SGBC fixture."

    def add_arguments(self, parser):
        parser.add_argument("source")
        parser.add_argument("-o", "--output", default="-")

    def handle(self, *args, **options):
        try:
            with open(options["source"], encoding="utf-8") as source:
                fixture = compile_json_draft(source)
            output = json.dumps(fixture, indent=2) + "\n"
            if options["output"] == "-":
                self.stdout.write(output, ending="")
            else:
                with open(options["output"], "w", encoding="utf-8") as target:
                    target.write(output)
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValidationError) as error:
            raise CommandError(str(error)) from error
