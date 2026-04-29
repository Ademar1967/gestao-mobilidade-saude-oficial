
from django.db import models

class MensagemWhatsApp(models.Model):
    numero = models.CharField(max_length=30)
    corpo = models.TextField()
    data_recebimento = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.numero} - {self.data_recebimento:%d/%m/%Y %H:%M}" 

class Enfermagem(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome

class Paciente(models.Model):
    nome = models.CharField(max_length=100)
    cartao_sis = models.CharField("Cartão SIS", max_length=10, blank=True, help_text="Número do cartão do SUS/SIS de Mogi das Cruzes")
    idade = models.PositiveIntegerField(null=True, blank=True)
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    rua = models.CharField(max_length=100, blank=True)
    numero = models.CharField(max_length=10, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=2, blank=True, help_text="UF")
    cep = models.CharField(max_length=10, blank=True)
    endereco = models.CharField(max_length=200, blank=True)  # legado, pode ser removido depois
    referencia = models.CharField(max_length=200, blank=True)
    ddd = models.CharField(max_length=2, blank=True, help_text="DDD do telefone")
    telefone = models.CharField(max_length=20, blank=True)
    tratamento = models.CharField(max_length=100, blank=True)
    oxigenio = models.BooleanField(default=False)
    oxigenio_litros_min = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, help_text="Fluxo de O2 em litros por minuto")
    observacoes = models.TextField(blank=True)
    evolucao = models.TextField(blank=True)
    status = models.CharField(max_length=30, blank=True)
    maca = models.BooleanField(default=False, help_text="Paciente usa maca?")
    cadeirante = models.BooleanField(default=False, help_text="Paciente é cadeirante?")
    acompanhante = models.BooleanField(default=False, help_text="Paciente tem acompanhante?")
    data_cadastro = models.DateTimeField(auto_now_add=True, null=True, blank=True, help_text="Data/hora do cadastro do paciente")
    # Campos de geolocalização
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Latitude do paciente")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Longitude do paciente")

    def __str__(self):
        return self.nome

    def contato_formatado(self):
        """Retorna telefone formatado como '(DDD) Numero', ou apenas o numero se DDD ausente."""
        if self.ddd and self.telefone:
            return f"({self.ddd}) {self.telefone}"
        return self.telefone or ''

    def logradouro_formatado(self):
        """Retorna logradouro resumido no formato 'Rua, Numero'."""
        if self.rua and self.numero:
            return f"{self.rua}, {self.numero}"
        return self.rua or ''

    def endereco_formatado(self):
        """Retorna endereco completo formatado, incluindo CEP se disponivel."""
        partes = [self.rua, self.numero, self.bairro, self.cidade, self.estado]
        partes = [p for p in partes if p]
        endereco = ', '.join(partes)
        if self.cep:
            endereco = f"{endereco} - {self.cep}" if endereco else self.cep
        return endereco

    @property
    def ja_alocado(self):
        """Retorna True se o paciente já possui transporte associado."""
        return self.transportes.exists()

class Veiculo(models.Model):
    TIPO_CHOICES = [
        ("ambulancia", "Ambulância Prefeitura"),
        ("van", "Van Terceirizada"),
    ]
    tipo_veiculo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="ambulancia")
    placa = models.CharField(max_length=20, blank=True)
    patrimonio = models.CharField(max_length=30, unique=True, blank=True)
    lotacao = models.PositiveIntegerField(default=1, help_text="Lotação máxima do veículo")

    def __str__(self):
        # Ambulância Prefeitura: mostrar só patrimônio
        if self.tipo_veiculo == "ambulancia" and self.patrimonio:
            return f"{self.patrimonio}"
        # Van Terceirizada: mostrar só placa
        if self.tipo_veiculo == "van" and self.placa:
            return f"{self.placa}"
        # Fallback: mostra patrimônio ou placa se existir
        if self.patrimonio:
            return self.patrimonio
        if self.placa:
            return self.placa
        return "Veículo sem identificação"

class Condutor(models.Model):
	nome = models.CharField(max_length=100)

	def __str__(self):
		return self.nome

class Clinica(models.Model):
	nome = models.CharField(max_length=100)
	endereco = models.CharField(max_length=200, blank=True)
	bairro = models.CharField(max_length=100, blank=True)
	cidade = models.CharField(max_length=100, blank=True)
	telefone = models.CharField(max_length=20, blank=True)

	# Campos de geolocalização
	latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Latitude da clínica")
	longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Longitude da clínica")

	def __str__(self):
		return self.nome

	def endereco_resumido(self):
		"""Retorna endereco resumido da clinica no formato 'Logradouro - Bairro - Cidade'."""
		partes = [self.endereco, self.bairro, self.cidade]
		return ' - '.join([p for p in partes if p])

# --- MODELO DE INTEGRAÇÃO: TRANSPORTE ---
# Este modelo integra todas as entidades principais do app e registra cada transporte realizado.
class Transporte(models.Model):
	paciente = models.ForeignKey('Paciente', on_delete=models.CASCADE, related_name='transportes')
	veiculo = models.ForeignKey('Veiculo', on_delete=models.SET_NULL, null=True, blank=True, related_name='transportes')
	condutor = models.ForeignKey('Condutor', on_delete=models.SET_NULL, null=True, blank=True, related_name='transportes')
	clinica = models.ForeignKey('Clinica', on_delete=models.SET_NULL, null=True, blank=True, related_name='transportes')
	enfermagem = models.ForeignKey('Enfermagem', on_delete=models.SET_NULL, null=True, blank=True, related_name='transportes')
	data_transporte = models.DateField()
	hora_saida = models.TimeField(null=True, blank=True)
	hora_chegada = models.TimeField(null=True, blank=True)
	observacoes = models.TextField(blank=True)

	def __str__(self):
		return f"Transporte de {self.paciente} para {self.clinica} em {self.data_transporte}"

	def resumo_operacional(self):
		"""Retorna resumo do transporte no formato 'Data | Paciente -> Clinica | Veiculo'."""
		paciente_nome = self.paciente.nome if self.paciente else 'Paciente nao informado'
		clinica_nome = self.clinica.nome if self.clinica else 'Clinica nao informada'
		veiculo_nome = str(self.veiculo) if self.veiculo else 'Veiculo nao informado'
		return f"{self.data_transporte} | {paciente_nome} -> {clinica_nome} | {veiculo_nome}"
from django.db import models

# Create your models here.
