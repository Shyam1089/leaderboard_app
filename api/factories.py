import factory
import random
from .models import User

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    name = factory.Faker('name')
    age = factory.LazyFunction(lambda: random.randint(18, 65))
    address = factory.Faker('address')
    points = factory.LazyFunction(lambda: random.randint(0, 100))

def create_initial_users(count=10):
    """
    Create initial users with random values.
    
    Args:
        count (int): Number of users to create. Default is 10.
    """
    for _ in range(count):
        UserFactory.create() 