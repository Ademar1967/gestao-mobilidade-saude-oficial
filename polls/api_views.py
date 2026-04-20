from rest_framework import viewsets, permissions
from .models import Paciente, Clinica, Condutor, Enfermagem, Veiculo
from .serializers import PacienteSerializer, ClinicaSerializer, CondutorSerializer, EnfermagemSerializer, VeiculoSerializer

class PacienteViewSet(viewsets.ModelViewSet):
    queryset = Paciente.objects.all()
    serializer_class = PacienteSerializer
    permission_classes = [permissions.IsAuthenticated]

class ClinicaViewSet(viewsets.ModelViewSet):
    queryset = Clinica.objects.all()
    serializer_class = ClinicaSerializer
    permission_classes = [permissions.IsAuthenticated]

class CondutorViewSet(viewsets.ModelViewSet):
    queryset = Condutor.objects.all()
    serializer_class = CondutorSerializer
    permission_classes = [permissions.IsAuthenticated]

class EnfermagemViewSet(viewsets.ModelViewSet):
    queryset = Enfermagem.objects.all()
    serializer_class = EnfermagemSerializer
    permission_classes = [permissions.IsAuthenticated]

class VeiculoViewSet(viewsets.ModelViewSet):
    queryset = Veiculo.objects.all()
    serializer_class = VeiculoSerializer
    permission_classes = [permissions.IsAuthenticated]
