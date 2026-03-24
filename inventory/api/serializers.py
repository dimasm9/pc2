from rest_framework import serializers

from inventory.models import Client, Equipment, EquipmentInspection, EquipmentReservation


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        exclude = ('is_deleted',)
        read_only_fields = ('created_by',)


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentReservation
        fields = '__all__'
        read_only_fields = ('created_by',)


class InspectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentInspection
        fields = '__all__'
        read_only_fields = ('created_by',)
