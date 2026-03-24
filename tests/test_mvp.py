import pytest
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError

from inventory.models import Client, Company, DocumentType, Equipment, EquipmentStatus, EquipmentType
from inventory.services import OperationContext, add_inspection, change_equipment_status, create_reservation, generate_document


@pytest.fixture
def user(db):
    u = User.objects.create_user(username='manager', password='123')
    g, _ = Group.objects.get_or_create(name='manager')
    u.groups.add(g)
    return u


@pytest.fixture
def base_data(db, user):
    company = Company.objects.create(full_name='ООО Тест', short_name='Тест', inn='1234567890')
    etype = EquipmentType.objects.create(name='Ноутбук', code='NB')
    statuses = ['draft', 'approval', 'approved', 'offered', 'reserved', 'inspected', 'consent_printed', 'consent_signed', 'transfer_act_printed', 'transferred', 'receipt_printed', 'sold', 'cancelled']
    for s in statuses:
        EquipmentStatus.objects.get_or_create(code=s, defaults={'name': s})
    for code in ['consent', 'transfer_act', 'receipt']:
        DocumentType.objects.get_or_create(code=code, defaults={'name': code})
    eq = Equipment.objects.create(company=company, equipment_type=etype, status=EquipmentStatus.objects.get(code='draft'), inventory_number='INV-1', name='Lenovo', created_by=user)
    client = Client.objects.create(client_type='person', name='Иван Иванов')
    return {'company': company, 'etype': etype, 'eq': eq, 'client': client}


def test_create_equipment_required_fields(db, user):
    company = Company.objects.create(full_name='ООО Ромашка', short_name='Ромашка', inn='9876543210')
    etype = EquipmentType.objects.create(name='ПК', code='PC')
    status = EquipmentStatus.objects.create(code='draft', name='Черновик')
    eq = Equipment.objects.create(company=company, equipment_type=etype, status=status, inventory_number='X1', name='ПК', created_by=user)
    assert eq.id


def test_forbid_invalid_transition(base_data, user):
    eq = base_data['eq']
    with pytest.raises(ValidationError):
        change_equipment_status(eq, 'sold', OperationContext(user))


def test_active_reservation_uniqueness(base_data, user):
    eq, client = base_data['eq'], base_data['client']
    create_reservation(eq, client, OperationContext(user), start_date='2026-01-01')
    with pytest.raises(ValidationError):
        create_reservation(eq, client, OperationContext(user), start_date='2026-01-02')


def test_consent_requires_inspection(base_data, user):
    eq, client = base_data['eq'], base_data['client']
    create_reservation(eq, client, OperationContext(user), start_date='2026-01-01')
    change_equipment_status(eq, 'approval', OperationContext(user))
    change_equipment_status(eq, 'approved', OperationContext(user))
    change_equipment_status(eq, 'offered', OperationContext(user))
    change_equipment_status(eq, 'reserved', OperationContext(user))
    change_equipment_status(eq, 'inspected', OperationContext(user))
    with pytest.raises(ValidationError):
        change_equipment_status(eq, 'consent_printed', OperationContext(user))
    add_inspection(eq, client, OperationContext(user), result='approved')
    generate_document(eq, client, 'consent', OperationContext(user))
    change_equipment_status(eq, 'consent_printed', OperationContext(user))
    assert eq.status.code == 'consent_printed'


def test_transfer_requires_consent(base_data, user):
    eq, client = base_data['eq'], base_data['client']
    create_reservation(eq, client, OperationContext(user), start_date='2026-01-01')
    add_inspection(eq, client, OperationContext(user), result='approved')
    for status in ['approval', 'approved', 'offered', 'reserved', 'inspected', 'consent_printed', 'consent_signed']:
        if status == 'consent_printed':
            generate_document(eq, client, 'consent', OperationContext(user))
        change_equipment_status(eq, status, OperationContext(user))
    with pytest.raises(ValidationError):
        change_equipment_status(eq, 'transfer_act_printed', OperationContext(user))
    generate_document(eq, client, 'transfer_act', OperationContext(user))
    change_equipment_status(eq, 'transfer_act_printed', OperationContext(user))
    assert eq.status.code == 'transfer_act_printed'
