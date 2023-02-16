from django.core.management.base import BaseCommand, CommandError
from app.factories import TaskFactory


class Command(BaseCommand):
    help = 'Generates n fake Task objects'

    def add_arguments(self, parser):
        parser.add_argument('num_tasks', type=int)

    def handle(self, *args, **options):
        n = options['num_tasks']
        for _ in range(options['num_tasks']):
            TaskFactory()
        self.stdout.write(self.style.SUCCESS(f"Generated {n} Task objects."))
