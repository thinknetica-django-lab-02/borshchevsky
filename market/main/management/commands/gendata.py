import string

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from random import choices

from main.models import Product


def generate_random_str():
    return ''.join(choices(string.ascii_letters, k=5))


class Command(BaseCommand):
    """
    Generates sample data
    """
    def handle(self, *args, **options):
        username = generate_random_str()
        User.objects.create(username=username)

        product_title = generate_random_str()
        Product.objects.create(title=product_title)
