from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ClientForm, EquipmentForm, InspectionForm, ReservationForm
from .models import AuditLog, Client, Equipment, EquipmentStatus
from .services import OperationContext, add_inspection, change_equipment_status, create_reservation, generate_document, mark_document_signed


@login_required
def dashboard(request):
    status_counts = Equipment.objects.filter(is_deleted=False).values('status__name').annotate(total=Count('id')).order_by('status__name')
    active_reservations = sum(e.reservations.filter(status='active').count() for e in Equipment.objects.filter(is_deleted=False))
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
    qs = Equipment.objects.filter(is_deleted=False).select_related('company', 'equipment_type', 'status')
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status__code=status)
    search = request.GET.get('q')
    if search:
        qs = qs.filter(name__icontains=search)
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
            elif action == 'reserve':
                form = ReservationForm(request.POST)
                if form.is_valid():
                    create_reservation(item, form.cleaned_data['client'], ctx, form.cleaned_data['start_date'], form.cleaned_data['end_date'], form.cleaned_data['comment'])
                    messages.success(request, 'Бронь создана.')
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
                client = item.reservations.filter(status='active').first().client
                generate_document(item, client, 'consent', ctx)
                change_equipment_status(item, 'consent_printed', ctx)
            elif action == 'sign_consent':
                doc = item.documents.filter(document_type__code='consent').order_by('-created_at').first()
                mark_document_signed(doc, ctx)
                change_equipment_status(item, 'consent_signed', ctx)
            elif action == 'print_transfer':
                client = item.reservations.filter(status='active').first().client
                generate_document(item, client, 'transfer_act', ctx)
                change_equipment_status(item, 'transfer_act_printed', ctx)
            elif action == 'mark_receipt':
                client = item.reservations.filter(status='active').first().client
                generate_document(item, client, 'receipt', ctx)
                change_equipment_status(item, 'receipt_printed', ctx)
        except (ValidationError, AttributeError) as exc:
            messages.error(request, str(exc))
        return redirect('equipment_detail', pk=pk)

    return render(request, 'inventory/equipment_detail.html', {
        'item': item,
        'status_options': EquipmentStatus.objects.all(),
        'reservation_form': ReservationForm(initial={'start_date': timezone.localdate()}),
        'inspection_form': InspectionForm(),
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
