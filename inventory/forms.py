from django import forms

from .models import Client, Equipment, EquipmentInspection, EquipmentReservation


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        exclude = ('created_by', 'is_deleted')


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = '__all__'


class ReservationForm(forms.ModelForm):
    class Meta:
        model = EquipmentReservation
        fields = ('client', 'start_date', 'end_date', 'comment')


class InspectionForm(forms.ModelForm):
    class Meta:
        model = EquipmentInspection
        fields = ('client', 'result', 'notes')
