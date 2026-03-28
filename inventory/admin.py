from django.contrib import admin

from .models import (
    AuditLog,
    Client,
    Company,
    DocumentType,
    Equipment,
    EquipmentDocument,
    EquipmentInspection,
    EquipmentPhoto,
    EquipmentReservation,
    EquipmentStatus,
    EquipmentStatusHistory,
    EquipmentType,
)

admin.site.register(Company)
admin.site.register(EquipmentType)
admin.site.register(EquipmentStatus)
admin.site.register(Equipment)
admin.site.register(EquipmentPhoto)
admin.site.register(Client)
admin.site.register(EquipmentReservation)
admin.site.register(EquipmentInspection)
admin.site.register(DocumentType)
admin.site.register(EquipmentDocument)
admin.site.register(EquipmentStatusHistory)
admin.site.register(AuditLog)
