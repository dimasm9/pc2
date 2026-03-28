from dataclasses import dataclass
from typing import Optional

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import (
    AuditLog,
    DocumentType,
    Equipment,
    EquipmentDocument,
    EquipmentInspection,
    EquipmentReservation,
    EquipmentStatus,
    EquipmentStatusHistory,
    ReservationStatus,
)

STATUS_TRANSITIONS = {
    'draft': {'approval'},
    'approval': {'approved', 'cancelled'},
    'approved': {'offered', 'cancelled'},
    'offered': {'reserved', 'cancelled'},
    'reserved': {'inspected', 'cancelled'},
    'inspected': {'consent_printed', 'cancelled'},
    'consent_printed': {'consent_signed', 'cancelled'},
    'consent_signed': {'transfer_act_printed', 'cancelled'},
    'transfer_act_printed': {'transferred', 'cancelled'},
    'transferred': {'receipt_printed', 'cancelled'},
    'receipt_printed': {'sold', 'cancelled'},
}


@dataclass
class OperationContext:
    user: object
    ip: Optional[str] = None


def get_allowed_transition_codes(status_code: str) -> set[str]:
    return set(STATUS_TRANSITIONS.get(status_code, set()))


def write_audit(action: str, entity: str, entity_id: int, ctx: OperationContext, data=None):
    AuditLog.objects.create(
        user=ctx.user,
        action=action,
        entity=entity,
        entity_id=entity_id,
        data=data or {},
        ip=ctx.ip,
    )


def validate_required_equipment_fields(equipment: Equipment):
    if not equipment.company_id or not equipment.equipment_type_id or not equipment.inventory_number or not equipment.name:
        raise ValidationError('Для операции заполните обязательные поля оборудования.')


@transaction.atomic
def change_equipment_status(equipment: Equipment, new_status_code: str, ctx: OperationContext, comment: str = ''):
    old_status = equipment.status
    new_status = EquipmentStatus.objects.get(code=new_status_code)

    allowed = get_allowed_transition_codes(old_status.code)
    if new_status_code not in allowed and new_status_code != 'cancelled':
        raise ValidationError(f'Недопустимый переход: {old_status.code} -> {new_status_code}.')

    if new_status_code == 'approved':
        validate_required_equipment_fields(equipment)
    if new_status_code == 'reserved' and not equipment.reservations.filter(status=ReservationStatus.ACTIVE).exists():
        raise ValidationError('Нельзя перевести в "забронировано" без активной брони.')
    if new_status_code == 'consent_printed' and not equipment.inspections.exists():
        raise ValidationError('Нельзя печатать согласие без осмотра.')
    if new_status_code == 'transfer_act_printed' and not equipment.documents.filter(document_type__code='consent', is_printed=True).exists():
        raise ValidationError('Нельзя печатать акт без распечатанного согласия.')
    if new_status_code == 'receipt_printed' and not equipment.documents.filter(document_type__code='transfer_act', is_printed=True).exists():
        raise ValidationError('Нельзя отмечать чек без распечатанного акта передачи.')

    equipment.status = new_status
    equipment.save(update_fields=['status', 'updated_at'])

    EquipmentStatusHistory.objects.create(
        equipment=equipment,
        old_status=old_status,
        new_status=new_status,
        changed_by=ctx.user,
        comment=comment,
    )
    write_audit('status_change', 'equipment', equipment.id, ctx, {'from': old_status.code, 'to': new_status.code})
    return equipment


@transaction.atomic
def create_reservation(equipment: Equipment, client, ctx: OperationContext, start_date, end_date=None, comment=''):
    if equipment.reservations.filter(status=ReservationStatus.ACTIVE).exists():
        raise ValidationError('У оборудования уже есть активная бронь.')
    reservation = EquipmentReservation.objects.create(
        equipment=equipment,
        client=client,
        start_date=start_date,
        end_date=end_date,
        comment=comment,
        created_by=ctx.user,
    )
    write_audit('reservation_create', 'reservation', reservation.id, ctx, {'equipment_id': equipment.id, 'client_id': client.id})
    return reservation


def add_inspection(equipment: Equipment, client, ctx: OperationContext, result='pending', notes=''):
    inspection = EquipmentInspection.objects.create(
        equipment=equipment,
        client=client,
        result=result,
        notes=notes,
        created_by=ctx.user,
    )
    write_audit('inspection_create', 'inspection', inspection.id, ctx, {'equipment_id': equipment.id, 'client_id': client.id})
    return inspection


def generate_document(equipment: Equipment, client, document_type_code: str, ctx: OperationContext):
    doctype = DocumentType.objects.get(code=document_type_code)
    number = f'{document_type_code.upper()}-{equipment.id}-{timezone.now().strftime("%Y%m%d%H%M%S")}'
    doc = EquipmentDocument.objects.create(
        equipment=equipment,
        client=client,
        document_type=doctype,
        document_number=number,
        is_printed=True,
        printed_at=timezone.now(),
        status='printed',
        created_by=ctx.user,
    )
    write_audit('document_print', 'document', doc.id, ctx, {'type': document_type_code})
    return doc


def mark_document_signed(document: EquipmentDocument, ctx: OperationContext):
    document.signed_at = timezone.now()
    document.status = 'signed'
    document.save(update_fields=['signed_at', 'status', 'updated_at'])
    write_audit('document_sign', 'document', document.id, ctx)
    return document
