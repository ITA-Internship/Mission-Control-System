from rest_framework import serializers
from .models import Drone, DroneSpec
from .services import create_drone_with_spec


class DroneSpecSerializer(serializers.ModelSerializer):

    class Meta:
        model = DroneSpec
        exclude = ("drone",)


class DroneSerializer(serializers.ModelSerializer):
    spec = DroneSpecSerializer()

    class Meta:
        model = Drone
        fields = "__all__"

    def create(self, validated_data):
        spec_data = validated_data.pop("spec")

        return create_drone_with_spec(drone_data=validated_data, spec_data=spec_data)