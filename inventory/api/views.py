from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from inventory.models import AuditLog, Client, Equipment, EquipmentDocument, EquipmentInspection, EquipmentReservation
from inventory.services import OperationContext, add_inspection, change_equipment_status, create_reservation, generate_document, mark_document_signed

from .serializers import ClientSerializer, EquipmentSerializer, InspectionSerializer, ReservationSerializer


class LoginApi(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user = authenticate(request, username=request.data.get('username'), password=request.data.get('password'))
        if not user:
            return Response({'detail': 'invalid credentials'}, status=400)
        login(request, user)
        return Response({'detail': 'ok'})


class LogoutApi(APIView):
    def post(self, request):
        logout(request)
        return Response({'detail': 'ok'})


class MeApi(APIView):
    def get(self, request):
        return Response({'id': request.user.id, 'username': request.user.username})


class EquipmentListCreateApi(generics.ListCreateAPIView):
    queryset = Equipment.objects.filter(is_deleted=False)
    serializer_class = EquipmentSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class EquipmentRetrieveUpdateDestroyApi(generics.RetrieveUpdateDestroyAPIView):
    queryset = Equipment.objects.filter(is_deleted=False)
    serializer_class = EquipmentSerializer

    def perform_destroy(self, instance):
        instance.delete()


class ChangeStatusApi(APIView):
    def post(self, request, pk):
        equipment = get_object_or_404(Equipment, pk=pk, is_deleted=False)
        change_equipment_status(equipment, request.data['status_code'], OperationContext(request.user, request.META.get('REMOTE_ADDR')))
        return Response({'detail': 'ok'})


class ClientListCreateApi(generics.ListCreateAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer


class ClientRetrieveUpdateApi(generics.RetrieveUpdateAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer


class ReservationsListApi(generics.ListAPIView):
    queryset = EquipmentReservation.objects.all()
    serializer_class = ReservationSerializer


class ReserveApi(APIView):
    def post(self, request, pk):
        equipment = get_object_or_404(Equipment, pk=pk)
        client = get_object_or_404(Client, pk=request.data['client_id'])
        reservation = create_reservation(equipment, client, OperationContext(request.user), request.data.get('start_date'), request.data.get('end_date'))
        return Response(ReservationSerializer(reservation).data)


class ReservationCancelApi(APIView):
    def post(self, request, pk):
        res = get_object_or_404(EquipmentReservation, pk=pk)
        res.status = 'cancelled'
        res.save(update_fields=['status', 'updated_at'])
        return Response({'detail': 'ok'})


class ReservationCompleteApi(APIView):
    def post(self, request, pk):
        res = get_object_or_404(EquipmentReservation, pk=pk)
        res.status = 'completed'
        res.save(update_fields=['status', 'updated_at'])
        return Response({'detail': 'ok'})


class InspectionsListApi(generics.ListAPIView):
    queryset = EquipmentInspection.objects.all()
    serializer_class = InspectionSerializer


class InspectApi(APIView):
    def post(self, request, pk):
        equipment = get_object_or_404(Equipment, pk=pk)
        client = get_object_or_404(Client, pk=request.data['client_id'])
        inspection = add_inspection(equipment, client, OperationContext(request.user), request.data.get('result', 'pending'), request.data.get('notes', ''))
        return Response(InspectionSerializer(inspection).data)


class EquipmentDocumentsApi(APIView):
    def get(self, request, pk):
        equipment = get_object_or_404(Equipment, pk=pk)
        docs = equipment.documents.values('id', 'document_number', 'document_type__code', 'document_date', 'is_printed')
        return Response(list(docs))


class GenerateDocumentApi(APIView):
    def post(self, request, pk):
        equipment = get_object_or_404(Equipment, pk=pk)
        client = get_object_or_404(Client, pk=request.data['client_id'])
        doc = generate_document(equipment, client, request.data['document_type'], OperationContext(request.user))
        return Response({'id': doc.id, 'number': doc.document_number})


class MarkSignedApi(APIView):
    def post(self, request, pk):
        doc = get_object_or_404(EquipmentDocument, pk=pk)
        mark_document_signed(doc, OperationContext(request.user))
        return Response({'detail': 'ok'})


class MarkReceiptPrintedApi(APIView):
    def post(self, request, pk):
        equipment = get_object_or_404(Equipment, pk=pk)
        client_id = request.data.get('client_id')
        client = get_object_or_404(Client, pk=client_id) if client_id else equipment.reservations.first().client
        doc = generate_document(equipment, client, 'receipt', OperationContext(request.user))
        change_equipment_status(equipment, 'receipt_printed', OperationContext(request.user))
        return Response({'id': doc.id})


class StatusHistoryApi(APIView):
    def get(self, request, pk):
        equipment = get_object_or_404(Equipment, pk=pk)
        data = equipment.status_history.values('old_status__name', 'new_status__name', 'comment', 'changed_at')
        return Response(list(data))


class AuditLogApi(APIView):
    def get(self, request):
        return Response(list(AuditLog.objects.values('id', 'action', 'entity', 'entity_id', 'created_at').order_by('-created_at')[:200]))
