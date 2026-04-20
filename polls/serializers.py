from rest_framework import serializers
from .models import Paciente, Clinica, Condutor, Enfermagem, Veiculo

class PacienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paciente
        fields = '__all__'

class ClinicaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinica
        fields = '__all__'

class CondutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Condutor
        fields = '__all__'

class EnfermagemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enfermagem
        fields = '__all__'

class VeiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Veiculo
        fields = '__all__'
