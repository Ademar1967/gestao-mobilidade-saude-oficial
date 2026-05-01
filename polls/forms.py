from django import forms
from django.db.models import Q
from .models import Transporte, Paciente, Veiculo, Condutor, Clinica, Enfermagem
import requests
import re
import sys
import os
import unicodedata

# Logging para debug de cadastro de paciente
import logging
logger = logging.getLogger("paciente_form")

# --- FORMULÁRIO DE TRANSPORTE ---
# Permite cadastrar um transporte integrando paciente, veículo, condutor, clínica e enfermagem.

class TransporteForm(forms.ModelForm):
    veiculo_livre = forms.CharField(
        required=False,
        label='Veículo (digitar manualmente)',
        help_text='Opcional. Se preencher aqui, será cadastrado ou selecionado automaticamente.',
        widget=forms.TextInput(attrs={
            'placeholder': 'Digite placa ou patrimônio do veículo',
            'list': 'dl_veiculo_livre',
            'autocomplete': 'off',
        })
    )
    clinica_manual = forms.CharField(
        required=False,
        label='Clínica (digitar manualmente)',
        help_text='Opcional. Se preencher aqui, esta clínica será usada no transporte.',
        widget=forms.TextInput(attrs={
            'placeholder': 'Digite o nome da clínica',
            'list': 'dl_clinica_manual',
            'autocomplete': 'off',
        })
    )
    condutor_manual = forms.CharField(
        required=False,
        label='Condutor (digitar manualmente)',
        help_text='Opcional. Se preencher aqui, este nome sera usado no transporte.',
        widget=forms.TextInput(attrs={
            'placeholder': 'Digite o nome do condutor',
            'list': 'dl_condutor_manual',
            'autocomplete': 'off',
        })
    )
    enfermagem_manual = forms.CharField(
        required=False,
        label='Enfermagem (digitar manualmente)',
        help_text='Opcional. Se preencher aqui, este nome será usado no transporte.',
        widget=forms.TextInput(attrs={
            'placeholder': 'Digite o nome da enfermagem',
            'list': 'dl_enfermagem_manual',
            'autocomplete': 'off',
        })
    )

    def clean_data_transporte(self):
        from django.utils import timezone
        data = self.cleaned_data.get('data_transporte')
        if data and data < timezone.localdate():
            raise forms.ValidationError('A data informada já passou. Selecione uma data igual ou posterior a hoje.')
        return data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove o campo 'patrimonio' do form padrão (será tratado manualmente)
        if 'patrimonio' in self.fields:
            self.fields['patrimonio'].widget = forms.HiddenInput()
        if 'clinica' in self.fields:
            self.fields['clinica'].label_from_instance = self._formatar_opcao_clinica
        # Corrige o label do campo hora_saida
        if 'hora_saida' in self.fields:
            self.fields['hora_saida'].label = 'Horário da Consulta'

    @staticmethod
    def _formatar_opcao_clinica(clinica):
        """Formata o label da clinica no select como 'Nome - Endereco - Bairro'."""
        partes = [clinica.nome]
        if clinica.endereco:
            partes.append(clinica.endereco)
        if clinica.bairro:
            partes.append(clinica.bairro)
        return ' - '.join(partes)

    def clean(self):
        """Valida campos e permite cadastro automático de veículo manual."""
        cleaned_data = super().clean()
        paciente = cleaned_data.get('paciente')
        data_transporte = cleaned_data.get('data_transporte')
        veiculo = cleaned_data.get('veiculo')
        van_editavel = self.data.get('van_editavel')
        veiculo_livre = self.data.get('veiculo_livre', '').strip()
        clinica_manual = re.sub(r'\s+', ' ', (cleaned_data.get('clinica_manual') or '').strip())
        cleaned_data['clinica_manual'] = clinica_manual
        condutor_manual = re.sub(r'\s+', ' ', (cleaned_data.get('condutor_manual') or '').strip())
        cleaned_data['condutor_manual'] = condutor_manual

        enfermagem_manual = re.sub(r'\s+', ' ', (cleaned_data.get('enfermagem_manual') or '').strip())
        cleaned_data['enfermagem_manual'] = enfermagem_manual

        if clinica_manual:
            clinica_existente = Clinica.objects.filter(nome__iexact=clinica_manual).first()
            if clinica_existente:
                cleaned_data['clinica'] = clinica_existente
            else:
                cleaned_data['clinica'] = Clinica.objects.create(nome=clinica_manual)

        if condutor_manual:
            condutor_existente = Condutor.objects.filter(nome__iexact=condutor_manual).first()
            if condutor_existente:
                cleaned_data['condutor'] = condutor_existente
            else:
                cleaned_data['condutor'] = Condutor.objects.create(nome=condutor_manual)

        if enfermagem_manual:
            from .models import Enfermagem
            enfermagem_existente = Enfermagem.objects.filter(nome__iexact=enfermagem_manual).first()
            if enfermagem_existente:
                cleaned_data['enfermagem'] = enfermagem_existente
            else:
                cleaned_data['enfermagem'] = Enfermagem.objects.create(nome=enfermagem_manual)

        # Cadastro automático de veículo se preenchido manualmente
        if not veiculo and veiculo_livre:
            # Verifica se já existe veículo com esse patrimônio ou placa
            veiculo_existente = Veiculo.objects.filter(
                Q(patrimonio__iexact=veiculo_livre) | Q(placa__iexact=veiculo_livre)
            ).first()
            if veiculo_existente:
                cleaned_data['veiculo'] = veiculo_existente
                self.novo_veiculo_cadastrado = False
                self.veiculo_ja_existia = True
            else:
                # Decide tipo pelo formato (simples: placa tem letras e números, patrimônio só números)
                if re.match(r'^[A-Za-z]{3}\d[A-Za-z]\d{2}$', veiculo_livre) or re.match(r'^[A-Za-z]{3}-\d{4}$', veiculo_livre):
                    tipo = 'van'
                    novo_veiculo = Veiculo.objects.create(tipo_veiculo=tipo, placa=veiculo_livre)
                else:
                    tipo = 'ambulancia'
                    novo_veiculo = Veiculo.objects.create(tipo_veiculo=tipo, patrimonio=veiculo_livre)
                cleaned_data['veiculo'] = novo_veiculo
                self.novo_veiculo_cadastrado = True
                self.veiculo_ja_existia = False
        else:
            self.novo_veiculo_cadastrado = False
            self.veiculo_ja_existia = False

        if veiculo and hasattr(veiculo, 'tipo_veiculo') and veiculo.tipo_veiculo == 'van':
            # Se for van terceirizada, usa o campo editável
            if van_editavel:
                cleaned_data['patrimonio'] = van_editavel
            else:
                self.add_error('veiculo', 'Informe o identificador da van (campo editável).')

        # Regra operacional orientativa: paciente usuario de O2 deve ser priorizado em ambulancia.
        veiculo_selecionado = cleaned_data.get('veiculo')
        self.alerta_oxigenio_ambulancia = False
        if paciente and getattr(paciente, 'oxigenio', False):
            if not veiculo_selecionado or getattr(veiculo_selecionado, 'tipo_veiculo', '') != 'ambulancia':
                self.alerta_oxigenio_ambulancia = True

        # Evita duplicidade operacional: mesmo paciente no mesmo dia.
        if paciente and data_transporte:
            qs_duplicado = Transporte.objects.filter(
                paciente=paciente,
                data_transporte=data_transporte,
            )
            if self.instance and self.instance.pk:
                qs_duplicado = qs_duplicado.exclude(pk=self.instance.pk)
            if qs_duplicado.exists():
                self.add_error('paciente', 'Este paciente ja possui transporte cadastrado para esta data.')

        return cleaned_data
    class Meta:
        model = Transporte
        fields = '__all__'
        widgets = {
            'data_transporte': forms.DateInput(attrs={'type': 'date'}),
            'hora_saida': forms.TimeInput(attrs={'type': 'time'}),
            'observacoes': forms.Textarea(attrs={'rows':2, 'class':'auto-expand'}),
        }

from django import forms
from .models import Paciente, Veiculo, Condutor, Clinica, Enfermagem

# Formulário para Enfermagem
class EnfermagemForm(forms.ModelForm):
    class Meta:
        model = Enfermagem
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs={'required': 'required', 'placeholder': 'Nome da enfermagem'})
        }

class PacienteForm(forms.ModelForm):
    ddd = forms.CharField(label='DDD', max_length=2, required=False, widget=forms.TextInput(attrs={'placeholder': 'DDD', 'style': 'max-width:50px;'}))
    cartao_sis = forms.CharField(label='Cartão SIS', max_length=10, required=False, widget=forms.TextInput(attrs={'placeholder': 'Cartão SIS', 'style': 'max-width:110px;'}))
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'latitude' in self.fields:
            self.fields['latitude'].required = False
        if 'longitude' in self.fields:
            self.fields['longitude'].required = False
        if 'oxigenio_litros_min' in self.fields:
            self.fields['oxigenio_litros_min'].widget.attrs['placeholder'] = 'Ex: 2.0 L/min'
            self.fields['oxigenio_litros_min'].widget.attrs['aria-label'] = 'Litros por minuto de oxigenio'
        if 'cartao_sis' in self.fields:
            self.fields['cartao_sis'].widget.attrs['autocomplete'] = 'off'
        # Placeholders explicativos adicionais
        if 'nome' in self.fields:
            self.fields['nome'].widget.attrs['placeholder'] = 'Nome completo do paciente'
            self.fields['nome'].widget.attrs['aria-label'] = 'Nome completo do paciente'
            self.fields['nome'].widget.attrs['tabindex'] = 1
        if 'telefone' in self.fields:
            self.fields['telefone'].widget.attrs['placeholder'] = 'Ex: 99999-9999'
            self.fields['telefone'].widget.attrs['aria-label'] = 'Telefone do paciente'
            self.fields['telefone'].widget.attrs['tabindex'] = 2
        if 'referencia' in self.fields:
            self.fields['referencia'].widget.attrs['placeholder'] = 'Ponto de referência (opcional)'
            self.fields['referencia'].widget.attrs['aria-label'] = 'Ponto de referência do endereço'
            self.fields['referencia'].widget.attrs['tabindex'] = 3
        # Esconde o campo cadeira_dobravel se não for cadeirante (feito no template)
    def save(self, commit=True):
        """Salva o paciente montando o campo endereco legado, separando DDD e Cartão SIS."""
        instance = super().save(commit=False)
        # Monta o campo endereco legado para compatibilidade
        rua = self.cleaned_data.get('rua', '')
        numero = self.cleaned_data.get('numero', '')
        bairro = self.cleaned_data.get('bairro', '')
        cidade = self.cleaned_data.get('cidade', '')
        estado = self.cleaned_data.get('estado', '')
        cep = self.cleaned_data.get('cep', '')
        endereco_legado = f"{rua}, {numero}, {bairro}, {cidade}, {estado}"
        if cep:
            endereco_legado += f", {cep}"
        instance.endereco = endereco_legado
        # Salva DDD separado
        instance.ddd = self.cleaned_data.get('ddd', '')
        # Salva Cartão SIS
        instance.cartao_sis = self.cleaned_data.get('cartao_sis', '')
        if commit:
            instance.save()
        return instance

    def clean(self):
        """Valida endereco completo, tenta geocodificar e impede cadastro de pacientes duplicados."""
        cleaned_data = super().clean()
        nome = cleaned_data.get('nome')
        telefone = cleaned_data.get('telefone')
        rua = cleaned_data.get('rua')
        numero = cleaned_data.get('numero')
        bairro = cleaned_data.get('bairro')
        cidade = cleaned_data.get('cidade')
        estado = cleaned_data.get('estado')
        cep = cleaned_data.get('cep')
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')
        oxigenio = cleaned_data.get('oxigenio')
        oxigenio_litros_min = cleaned_data.get('oxigenio_litros_min')
        logger.info(f"Dados recebidos: rua={rua}, numero={numero}, bairro={bairro}, cidade={cidade}, estado={estado}, cep={cep}, latitude={latitude}, longitude={longitude}")

        # Regra de negocio: se usa O2, exige fluxo em L/min; se nao usa, limpa o campo.
        if oxigenio:
            if oxigenio_litros_min is None:
                self.add_error('oxigenio_litros_min', 'Informe a quantidade de O2 em litros por minuto.')
            elif oxigenio_litros_min <= 0:
                self.add_error('oxigenio_litros_min', 'O valor de O2 deve ser maior que zero.')
        else:
            cleaned_data['oxigenio_litros_min'] = None

        # Validação: endereço detalhado (UF e CEP não obrigatórios)
        if not (rua and numero and bairro and cidade):
            logger.warning("Endereço incompleto!")
            raise forms.ValidationError('Preencha todos os campos de endereço: rua, número, bairro e cidade.')
        # Monta endereço completo para geocodificação
        endereco_completo = f"{rua}, {numero}, {bairro}, {cidade}, {estado}"
        if cep:
            endereco_completo += f", {cep}"
        # Se latitude/longitude não preenchidos, tenta geocodificar
        if not latitude or not longitude:
            # Em produção (Render), desabilita geocodificação para evitar timeout
            # Apenas tenta em ambiente local
            if 'test' in sys.argv or os.environ.get('DEBUG') == 'True':
                try:
                    logger.info(f"Buscando geolocalização para: {endereco_completo}")
                    url = f'https://nominatim.openstreetmap.org/search'
                    params = {'q': endereco_completo, 'format': 'json', 'limit': 1}
                    response = requests.get(
                        url,
                        params=params,
                        headers={'User-Agent': 'transporte-pacientes-app'},
                        timeout=3,  # Reduzido de 5 para 3 segundos
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if data:
                            lat = round(float(data[0]['lat']), 6)
                            lon = round(float(data[0]['lon']), 6)
                            cleaned_data['latitude'] = lat
                            cleaned_data['longitude'] = lon
                            logger.info(f"Geolocalização encontrada: lat={lat}, lon={lon}")
                        else:
                            logger.warning("Endereço não encontrado no serviço de geolocalização. Salvando sem latitude/longitude.")
                    else:
                        logger.warning(f"Erro HTTP ao consultar geolocalização: status={response.status_code}. Salvando sem latitude/longitude.")
                except Exception as e:
                    logger.warning(f"Exceção ao tentar geocodificar: {e}. Salvando sem latitude/longitude.")
            else:
                logger.info("Ambiente de produção: geocodificação desabilitada para evitar timeout.")
        # Duplicidade de paciente (só se telefone for informado)
        if nome and telefone:
            qs = Paciente.objects.filter(nome=nome, telefone=telefone)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                logger.warning("Paciente duplicado!")
                raise forms.ValidationError('Já existe um paciente com este nome e telefone.')
        # Garante que latitude/longitude tenham no máximo 6 casas decimais, mas nunca bloqueia o cadastro
        if cleaned_data.get('latitude') is not None:
            try:
                # Garante string formatada para o DecimalField
                cleaned_data['latitude'] = format(round(float(cleaned_data['latitude']), 6), '.6f')
            except Exception:
                cleaned_data['latitude'] = None
        if cleaned_data.get('longitude') is not None:
            try:
                cleaned_data['longitude'] = format(round(float(cleaned_data['longitude']), 6), '.6f')
            except Exception:
                cleaned_data['longitude'] = None
        return cleaned_data

    def clean_ddd(self):
        """Valida que o DDD contenha exatamente 2 digitos numericos."""
        ddd = (self.cleaned_data.get('ddd') or '').strip()
        if ddd and not re.fullmatch(r'\d{2}', ddd):
            raise forms.ValidationError('DDD deve conter exatamente 2 numeros.')
        return ddd

    def clean_telefone(self):
        """Valida telefone (8-9 digitos). Aceita 10-11 digitos separando DDD automaticamente."""
        telefone = (self.cleaned_data.get('telefone') or '').strip()
        if telefone:
            telefone_numerico = re.sub(r'\D', '', telefone)
            if len(telefone_numerico) in (10, 11) and not (self.cleaned_data.get('ddd') or '').strip():
                # Compatibilidade: se usuario informar DDD+telefone juntos, separa automaticamente.
                self.cleaned_data['ddd'] = telefone_numerico[:2]
                telefone_numerico = telefone_numerico[2:]
            if len(telefone_numerico) < 8 or len(telefone_numerico) > 9:
                raise forms.ValidationError('Telefone deve conter 8 ou 9 numeros (ou 10/11 com DDD).')
            return telefone_numerico
        return telefone

    def clean_cep(self):
        """Valida e formata CEP no padrao XXXXX-XXX."""
        cep = (self.cleaned_data.get('cep') or '').strip()
        if cep:
            cep_numerico = re.sub(r'\D', '', cep)
            if len(cep_numerico) != 8:
                raise forms.ValidationError('CEP deve conter 8 numeros.')
            return f"{cep_numerico[:5]}-{cep_numerico[5:]}"
        return cep

    def clean_estado(self):
        """Valida UF com exatamente 2 letras e converte para maiusculo."""
        estado = (self.cleaned_data.get('estado') or '').strip().upper()
        if estado and not re.fullmatch(r'[A-Z]{2}', estado):
            raise forms.ValidationError('UF deve conter 2 letras (ex.: SP).')
        return estado

    class Meta:
        model = Paciente
        fields = '__all__'
        widgets = {
            'peso': forms.NumberInput(attrs={'placeholder': 'Peso (kg)', 'step': '0.01', 'min': '0', 'style': 'width: 120px;'}),
            'oxigenio_litros_min': forms.NumberInput(attrs={'placeholder': 'Ex: 2.0 L/min', 'step': '0.1', 'min': '0.1'}),
            'rua': forms.TextInput(attrs={'placeholder': 'Rua'}),
            'numero': forms.TextInput(attrs={'placeholder': 'Número'}),
            'bairro': forms.TextInput(attrs={'placeholder': 'Bairro'}),
            'cidade': forms.TextInput(attrs={'placeholder': 'Cidade'}),
            'estado': forms.TextInput(attrs={'placeholder': 'UF', 'maxlength': 2, 'style': 'width: 60px;'}),
            'cep': forms.TextInput(attrs={'placeholder': 'CEP'}),
            'maca': forms.CheckboxInput(),
            'cadeirante': forms.CheckboxInput(),
            'acompanhante': forms.CheckboxInput(),
            'evolucao': forms.Textarea(attrs={'rows':2, 'class':'auto-expand'}),
            'observacoes': forms.Textarea(attrs={'rows':2, 'class':'auto-expand'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'ddd': forms.TextInput(attrs={'placeholder': 'DDD', 'style': 'max-width:50px;'}),
        }

class VeiculoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['placa'].required = False
        self.fields['placa'].help_text = 'Preencha apenas para vans terceirizadas.'
    class Meta:
        model = Veiculo
        fields = '__all__'
        widgets = {
            'lotacao': forms.NumberInput(attrs={'min': 1}),
        }

class CondutorForm(forms.ModelForm):
    def clean_nome(self):
        nome = re.sub(r'\s+', ' ', (self.cleaned_data.get('nome') or '').strip())
        if not nome:
            raise forms.ValidationError('Informe o nome do condutor.')

        qs = Condutor.objects.filter(nome__iexact=nome)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Ja existe um condutor com este nome.')
        return nome

    class Meta:
        model = Condutor
        fields = '__all__'

class ClinicaForm(forms.ModelForm):
    # Campo extra para autocomplete, valor será salvo em 'endereco' do modelo
    endereco_completo = forms.CharField(required=False, label='Endereço completo')
    logradouro = forms.CharField(required=False, label='Logradouro')
    numero = forms.CharField(required=False, label='Número')
    cep = forms.CharField(required=False, label='CEP')

    @staticmethod
    def _normalize_text(value):
        if not value:
            return ''
        value = unicodedata.normalize('NFKD', str(value)).encode('ASCII', 'ignore').decode('ASCII')
        value = re.sub(r'\s+', ' ', value).strip().lower()
        return value

    def clean(self):
        cleaned_data = super().clean()
        nome = cleaned_data.get('nome')
        endereco = cleaned_data.get('endereco_completo') or cleaned_data.get('endereco')
        from .models import Clinica
        nome_norm = self._normalize_text(nome)
        endereco_norm = self._normalize_text(endereco)
        queryset = Clinica.objects.all().only('id', 'nome', 'endereco')
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        # Verificar duplicatas por NOME e ENDEREÇO
        for clinica in queryset:
            clinica_nome_norm = self._normalize_text(clinica.nome)
            clinica_endereco_norm = self._normalize_text(clinica.endereco or '')
            
            # Validar NOME duplicado
            if nome_norm and clinica_nome_norm == nome_norm:
                self.add_error('nome', 'Ja existe uma clinica com este nome.')
            
            # Validar ENDEREÇO duplicado
            if endereco_norm and clinica_endereco_norm and clinica_endereco_norm == endereco_norm:
                self.add_error('endereco_completo', 'Ja existe uma clinica com este endereco.')

        # Remove campos bairro, cidade, telefone do cleaned_data se existirem
        for campo in ['bairro', 'cidade', 'telefone']:
            if campo in cleaned_data:
                cleaned_data.pop(campo)
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        endereco_completo = self.cleaned_data.get('endereco_completo')
        if endereco_completo:
            instance.endereco = endereco_completo
        if commit:
            instance.save()
        return instance

    class Meta:
        model = Clinica
        fields = '__all__'
        widgets = {
            'endereco': forms.TextInput(attrs={'data-autocomplete-endereco': 'true'}),
        }
