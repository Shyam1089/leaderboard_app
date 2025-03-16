from django.core.management.base import BaseCommand
from api.factories import create_initial_users

class Command(BaseCommand):
    help = 'Populate the database with initial users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of users to create'
        )

    def handle(self, *args, **options):
        count = options['count']
        create_initial_users(count)
        self.stdout.write(self.style.SUCCESS(f'Successfully created {count} users')) 