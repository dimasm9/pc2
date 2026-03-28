from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('client_type', models.CharField(choices=[('person', 'Физлицо'), ('company', 'Юрлицо')], max_length=20)),
                ('name', models.CharField(max_length=255)),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('passport_data', models.TextField(blank=True)),
                ('inn', models.CharField(blank=True, max_length=12)),
                ('kpp', models.CharField(blank=True, max_length=9)),
                ('address', models.TextField(blank=True)),
                ('comment', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True)),
                ('full_name', models.CharField(max_length=255)),
                ('short_name', models.CharField(max_length=100)),
                ('inn', models.CharField(max_length=12, unique=True)),
                ('kpp', models.CharField(blank=True, max_length=9)),
                ('ogrn', models.CharField(blank=True, max_length=13)),
                ('address', models.TextField(blank=True)),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('email', models.EmailField(blank=True, max_length=254)),
            ],
        ),
        migrations.CreateModel(
            name='DocumentType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='EquipmentStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='EquipmentType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=120)),
                ('code', models.CharField(max_length=40, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Equipment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('inventory_number', models.CharField(max_length=120)),
                ('serial_number', models.CharField(blank=True, max_length=120)),
                ('name', models.CharField(max_length=255)),
                ('brand', models.CharField(blank=True, max_length=120)),
                ('model', models.CharField(blank=True, max_length=120)),
                ('manufacture_year', models.PositiveIntegerField(blank=True, null=True)),
                ('condition', models.CharField(blank=True, max_length=255)),
                ('description', models.TextField(blank=True)),
                ('purchase_price', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('sale_price', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('approved_price', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('currency', models.CharField(default='RUB', max_length=3)),
                ('location', models.CharField(blank=True, max_length=255)),
                ('comment', models.TextField(blank=True)),
                ('main_photo', models.ImageField(blank=True, null=True, upload_to='equipment/main/')),
                ('is_deleted', models.BooleanField(default=False)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='equipment', to='inventory.company')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('equipment_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventory.equipmenttype')),
                ('status', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventory.equipmentstatus')),
            ],
            options={'indexes': [models.Index(fields=['status'], name='inventory_eq_status_067a0f_idx'), models.Index(fields=['name'], name='inventory_eq_name_97ed66_idx'), models.Index(fields=['updated_at'], name='inventory_eq_updated_10d4e3_idx')]},
        ),
        migrations.CreateModel(
            name='EquipmentPhoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.ImageField(upload_to='equipment/photos/')),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('equipment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photos', to='inventory.equipment')),
            ],
        ),
        migrations.CreateModel(
            name='EquipmentInspection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inspected_at', models.DateTimeField()),
                ('result', models.CharField(choices=[('approved', 'Одобрено'), ('rejected', 'Отклонено'), ('pending', 'Ожидание')], default='pending', max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventory.client')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('equipment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inspections', to='inventory.equipment')),
            ],
        ),
        migrations.CreateModel(
            name='EquipmentReservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('active', 'Активна'), ('cancelled', 'Отменена'), ('completed', 'Завершена')], default='active', max_length=20)),
                ('comment', models.TextField(blank=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reservations', to='inventory.client')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('equipment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='inventory.equipment')),
            ],
        ),
        migrations.CreateModel(
            name='EquipmentDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('document_number', models.CharField(max_length=50)),
                ('document_date', models.DateField()),
                ('pdf_file', models.FileField(blank=True, upload_to='documents/')),
                ('is_printed', models.BooleanField(default=False)),
                ('printed_at', models.DateTimeField(blank=True, null=True)),
                ('signed_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(default='created', max_length=50)),
                ('comment', models.TextField(blank=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventory.client')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('document_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventory.documenttype')),
                ('equipment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='inventory.equipment')),
            ],
        ),
        migrations.CreateModel(
            name='EquipmentStatusHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField(blank=True)),
                ('changed_at', models.DateTimeField(auto_now_add=True)),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('equipment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status_history', to='inventory.equipment')),
                ('new_status', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='inventory.equipmentstatus')),
                ('old_status', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='inventory.equipmentstatus')),
            ],
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=100)),
                ('entity', models.CharField(max_length=100)),
                ('entity_id', models.PositiveBigIntegerField()),
                ('data', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('ip', models.GenericIPAddressField(blank=True, null=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(model_name='equipment', constraint=models.UniqueConstraint(fields=('company', 'inventory_number'), name='uniq_inv_per_company')),
        migrations.AddConstraint(model_name='equipment', constraint=models.UniqueConstraint(condition=~Q(('serial_number', '')), fields=('company', 'serial_number'), name='uniq_serial_per_company_when_present')),
        migrations.AddConstraint(model_name='equipmentreservation', constraint=models.UniqueConstraint(condition=Q(('status', 'active')), fields=('equipment',), name='one_active_reservation_per_equipment')),
    ]
