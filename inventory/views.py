from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Exists, OuterRef
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ClientForm, EquipmentForm, InspectionForm, ReservationForm
from .models import AuditLog, Client, Equipment, EquipmentReservation, EquipmentStatus
from .services import (
    OperationContext,
    add_inspection,
    change_equipment_status,
    create_reservation,
    generate_document,
    get_allowed_transition_codes,
    mark_document_signed,
)

STATUS_FLOW = [
    'draft', 'approval', 'approved', 'offered', 'reserved', 'inspected',
    'consent_printed', 'consent_signed', 'transfer_act_printed', 'transferred',
    'receipt_printed', 'sold',
]


@login_required
def dashboard(request):
    status_counts = Equipment.objects.filter(is_deleted=False).values('status__name').annotate(total=Count('id')).order_by('status__name')
    active_reservations = EquipmentReservation.objects.filter(status='active').count()
    recent_actions = AuditLog.objects.select_related('user').order_by('-created_at')[:10]
    return render(request, 'inventory/dashboard.html', {
        'status_counts': status_counts,
        'active_reservations': active_reservations,
        'recent_actions': recent_actions,
    })


@login_required
def approvals_queue(request):
    ctx = OperationContext(user=request.user, ip=request.META.get('REMOTE_ADDR'))
    waiting = Equipment.objects.filter(is_deleted=False, status__code='approval').select_related('company', 'equipment_type', 'status')
    approved_today = Equipment.objects.filter(is_deleted=False, status__code='approved').select_related('company', 'equipment_type')[:100]

    if request.method == 'POST':
        equipment = get_object_or_404(Equipment, pk=request.POST.get('equipment_id'), is_deleted=False)
        action = request.POST.get('action')
        comment = request.POST.get('comment', '')
        try:
            if action == 'approve':
                change_equipment_status(equipment, 'approved', ctx, comment)
                messages.success(request, f'Оборудование {equipment.inventory_number} переведено в "согласовано".')
            elif action == 'cancel':
                change_equipment_status(equipment, 'cancelled', ctx, comment)
                messages.success(request, f'Оборудование {equipment.inventory_number} отменено.')
        except ValidationError as exc:
            messages.error(request, str(exc))
        return redirect('approvals_queue')

    return render(request, 'inventory/approvals_queue.html', {
        'waiting': waiting,
        'approved_today': approved_today,
    })


@login_required
def equipment_list(request):
    active_reservation_subquery = EquipmentReservation.objects.filter(equipment=OuterRef('pk'), status='active')
    qs = Equipment.objects.filter(is_deleted=False).select_related('company', 'equipment_type', 'status').annotate(
        has_active_reservation=Exists(active_reservation_subquery)
    )

    status = request.GET.get('status')
    if status:
        qs = qs.filter(status__code=status)

    search = request.GET.get('q')
    if search:
        qs = qs.filter(name__icontains=search)

    has_reservation = request.GET.get('has_reservation')
    if has_reservation == 'yes':
        qs = qs.filter(has_active_reservation=True)
    elif has_reservation == 'no':
        qs = qs.filter(has_active_reservation=False)

    return render(request, 'inventory/equipment_list.html', {'items': qs[:200], 'statuses': EquipmentStatus.objects.all()})


@login_required
def equipment_create(request):
    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.created_by = request.user
            item.save()
            messages.success(request, 'Оборудование создано.')
            return redirect('equipment_detail', pk=item.pk)
    else:
        form = EquipmentForm()
    return render(request, 'inventory/form.html', {'form': form, 'title': 'Новое оборудование'})


@login_required
def equipment_detail(request, pk):
    item = get_object_or_404(Equipment, pk=pk, is_deleted=False)
    ctx = OperationContext(user=request.user, ip=request.META.get('REMOTE_ADDR'))

    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            if action == 'change_status':
                change_equipment_status(item, request.POST['status_code'], ctx, request.POST.get('comment', ''))
                messages.success(request, 'Статус изменен.')
            elif action == 'to_reserved':
                change_equipment_status(item, 'reserved', ctx, 'Переведено из карточки после создания брони')
                messages.success(request, 'Статус изменен на "забронировано".')
            elif action == 'reserve':
                form = ReservationForm(request.POST)
                if form.is_valid():
                    create_reservation(item, form.cleaned_data['client'], ctx, form.cleaned_data['start_date'], form.cleaned_data['end_date'], form.cleaned_data['comment'])
                    messages.success(request, 'Бронь создана. Теперь можно перевести в статус "забронировано".')
                else:
                    messages.error(request, form.errors.as_text())
            elif action == 'inspect':
                form = InspectionForm(request.POST)
                if form.is_valid():
                    add_inspection(item, form.cleaned_data['client'], ctx, form.cleaned_data['result'], form.cleaned_data['notes'])
                    messages.success(request, 'Осмотр сохранен.')
                else:
                    messages.error(request, form.errors.as_text())
            elif action == 'print_consent':
                with transaction.atomic():
                    change_equipment_status(item, 'consent_printed', ctx)
                    client = item.reservations.filter(status='active').first().client
                    generate_document(item, client, 'consent', ctx)
                messages.success(request, 'Согласие распечатано.')
            elif action == 'sign_consent':
                doc = item.documents.filter(document_type__code='consent').order_by('-created_at').first()
                mark_document_signed(doc, ctx)
                change_equipment_status(item, 'consent_signed', ctx)
                messages.success(request, 'Согласие отмечено подписанным.')
            elif action == 'print_transfer':
                with transaction.atomic():
                    change_equipment_status(item, 'transfer_act_printed', ctx)
                    client = item.reservations.filter(status='active').first().client
                    generate_document(item, client, 'transfer_act', ctx)
                messages.success(request, 'Акт передачи распечатан.')
            elif action == 'mark_receipt':
                with transaction.atomic():
                    change_equipment_status(item, 'receipt_printed', ctx)
                    client = item.reservations.filter(status='active').first().client
                    generate_document(item, client, 'receipt', ctx)
                messages.success(request, 'Чек отмечен как распечатанный.')
        except (ValidationError, AttributeError) as exc:
            messages.error(request, str(exc))
        return redirect('equipment_detail', pk=pk)

    allowed_codes = get_allowed_transition_codes(item.status.code)
    has_active_reservation = item.reservations.filter(status='active').exists()
    has_inspection = item.inspections.exists()
    has_consent = item.documents.filter(document_type__code='consent', is_printed=True).exists()
    has_transfer = item.documents.filter(document_type__code='transfer_act', is_printed=True).exists()

    status_options = []
    for status in EquipmentStatus.objects.filter(code__in=allowed_codes).order_by('name'):
        disabled_reason = ''
        if status.code == 'reserved' and not has_active_reservation:
            disabled_reason = 'Сначала создайте активную бронь'
        status_options.append({'code': status.code, 'name': status.name, 'disabled_reason': disabled_reason})

    progress = 0
    if item.status.code in STATUS_FLOW:
        progress = int((STATUS_FLOW.index(item.status.code) + 1) / len(STATUS_FLOW) * 100)

    return render(request, 'inventory/equipment_detail.html', {
        'item': item,
        'status_options': status_options,
        'reservation_form': ReservationForm(initial={'start_date': timezone.localdate()}),
        'inspection_form': InspectionForm(),
        'has_active_reservation': has_active_reservation,
        'has_inspection': has_inspection,
        'has_consent': has_consent,
        'has_transfer': has_transfer,
        'progress': progress,
    })


@login_required
def clients_list(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('clients_list')
    else:
        form = ClientForm()
    return render(request, 'inventory/clients.html', {'clients': Client.objects.all()[:200], 'form': form})
