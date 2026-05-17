import factory

from roles.models import ADMIN_CODE


class AdminRoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "roles.Role"
        django_get_or_create = ("code",)

    code = ADMIN_CODE
    name = "Admin"


class AdminUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "accounts.User"

    username = factory.Sequence(lambda n: f"user_{n}")
    password = factory.Sequence(lambda n: f"password_{n}")
    role = factory.SubFactory(AdminRoleFactory)


class MilitaryUnitFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "accounts.MilitaryUnit"

    name = factory.Sequence(lambda n: f"military_unit_{n}")
