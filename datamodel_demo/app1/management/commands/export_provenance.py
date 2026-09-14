import json

from django.core.management.base import BaseCommand, CommandError
from django.core.serializers.json import DjangoJSONEncoder

from app1.models import Entity
from app1.utils import export_provenance


class Command(BaseCommand):
    help = "Export the complete connected provenance record for an entity as JSON."

    def add_arguments(self, parser):
        parser.add_argument("identifier", help="Root entity identifier")
        parser.add_argument("-o", "--output", help="Write JSON to this file (stdout by default)")

    def handle(self, *args, **options):
        try:
            entity = Entity.objects.get(identifier=options["identifier"])
        except Entity.DoesNotExist as error:
            raise CommandError(f"No entity with identifier {options['identifier']!r}.") from error

        output = json.dumps(export_provenance(entity), cls=DjangoJSONEncoder, indent=2) + "\n"
        if options["output"]:
            with open(options["output"], "w", encoding="utf-8") as destination:
                destination.write(output)
        else:
            self.stdout.write(output, ending="")
