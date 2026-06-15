import factory

from missions.factories import MissionFactory, OperatorUserFactory

from .models import FileType, MissionArtifact

__all__ = ["MissionArtifactFactory"]


class MissionArtifactFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MissionArtifact

    mission = factory.SubFactory(MissionFactory)
    uploaded_by = factory.SubFactory(OperatorUserFactory)
    title = factory.Sequence(lambda n: f"Artifact {n}")
    description = factory.Faker("text")
    storage_backend = "local"

    class Params:
        is_image = factory.Trait(
            file=factory.django.FileField(
                filename="test_image.jpg", data=b"test image data"
            ),
            file_type=FileType.IMAGE,
            original_filename="test_image.jpg",
            file_size=1024,
        )
        is_video = factory.Trait(
            file=factory.django.FileField(
                filename="flight.mp4", data=b"test video data"
            ),
            file_type=FileType.VIDEO,
            original_filename="flight.mp4",
            file_size=1024,
        )
        is_data = factory.Trait(
            file=factory.django.FileField(
                filename="telemetry.csv", data=b"test csv data"
            ),
            file_type=FileType.DATA,
            original_filename="telemetry.csv",
            file_size=1024,
        )
