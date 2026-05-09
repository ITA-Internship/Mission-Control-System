from rest_framework import serializers
from .models import Drone, DroneSpec


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
        drone = Drone.objects.create(**validated_data)
        DroneSpec.objects.create(drone=drone, **spec_data)

        return drone