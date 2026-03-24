from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class ActiveModel(models.Model):
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Role(models.TextChoices):
    ADMIN = 'admin', 'Администратор'
    MANAGER = 'manager', 'Менеджер'
    APPROVER = 'approver', 'Согласующий'
    OPERATOR = 'operator', 'Оператор'


class Company(ActiveModel):
    full_name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=100)
    inn = models.CharField(max_length=12, unique=True)
    kpp = models.CharField(max_length=9, blank=True)
    ogrn = models.CharField(max_length=13, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.short_name


class EquipmentType(ActiveModel):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=40, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class EquipmentStatus(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Equipment(TimeStampedModel, ActiveModel):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='equipment')
    equipment_type = models.ForeignKey(EquipmentType, on_delete=models.PROTECT)
    status = models.ForeignKey(EquipmentStatus, on_delete=models.PROTECT)
    inventory_number = models.CharField(max_length=120)
    serial_number = models.CharField(max_length=120, blank=True)
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=120, blank=True)
    model = models.CharField(max_length=120, blank=True)
    manufacture_year = models.PositiveIntegerField(null=True, blank=True)
    condition = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    approved_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='RUB')
    location = models.CharField(max_length=255, blank=True)
    comment = models.TextField(blank=True)
    main_photo = models.ImageField(upload_to='equipment/main/', null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['company', 'inventory_number'], name='uniq_inv_per_company'),
            models.UniqueConstraint(
                fields=['company', 'serial_number'],
                condition=~Q(serial_number=''),
                name='uniq_serial_per_company_when_present',
            ),
        ]
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['name']),
            models.Index(fields=['updated_at']),
        ]

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save(update_fields=['is_deleted', 'updated_at'])

    def __str__(self):
        return f'{self.inventory_number} - {self.name}'


class EquipmentPhoto(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='photos')
    file = models.ImageField(upload_to='equipment/photos/')
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class ClientType(models.TextChoices):
    PERSON = 'person', 'Физлицо'
    COMPANY = 'company', 'Юрлицо'


class Client(TimeStampedModel):
    client_type = models.CharField(max_length=20, choices=ClientType.choices)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    passport_data = models.TextField(blank=True)
    inn = models.CharField(max_length=12, blank=True)
    kpp = models.CharField(max_length=9, blank=True)
    address = models.TextField(blank=True)
    comment = models.TextField(blank=True)

    def __str__(self):
        return self.name


class ReservationStatus(models.TextChoices):
    ACTIVE = 'active', 'Активна'
    CANCELLED = 'cancelled', 'Отменена'
    COMPLETED = 'completed', 'Завершена'


class EquipmentReservation(TimeStampedModel):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='reservations')
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='reservations')
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=ReservationStatus.choices, default=ReservationStatus.ACTIVE)
    comment = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['equipment'],
                condition=Q(status=ReservationStatus.ACTIVE),
                name='one_active_reservation_per_equipment',
            )
        ]


class InspectionResult(models.TextChoices):
    APPROVED = 'approved', 'Одобрено'
    REJECTED = 'rejected', 'Отклонено'
    PENDING = 'pending', 'Ожидание'


class EquipmentInspection(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='inspections')
    client = models.ForeignKey(Client, on_delete=models.PROTECT)
    inspected_at = models.DateTimeField(default=timezone.now)
    result = models.CharField(max_length=20, choices=InspectionResult.choices, default=InspectionResult.PENDING)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)


class DocumentType(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class EquipmentDocument(TimeStampedModel):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='documents')
    client = models.ForeignKey(Client, on_delete=models.PROTECT)
    document_type = models.ForeignKey(DocumentType, on_delete=models.PROTECT)
    document_number = models.CharField(max_length=50)
    document_date = models.DateField(default=timezone.localdate)
    pdf_file = models.FileField(upload_to='documents/', blank=True)
    is_printed = models.BooleanField(default=False)
    printed_at = models.DateTimeField(null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default='created')
    comment = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)


class EquipmentStatusHistory(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.ForeignKey(EquipmentStatus, on_delete=models.PROTECT, related_name='+')
    new_status = models.ForeignKey(EquipmentStatus, on_delete=models.PROTECT, related_name='+')
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    comment = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)


class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    entity = models.CharField(max_length=100)
    entity_id = models.PositiveBigIntegerField()
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
