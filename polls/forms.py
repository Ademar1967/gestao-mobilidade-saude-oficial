import logging
import os
import re
import unicodedata

from django import forms
from django.db.models import Q

from .models import Clinica, Condutor, Enfermagem, Paciente, Transporte, Veiculo

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

logger = logging.getLogger("paciente_form")


def _inferir_tipo_veiculo_por_identificador(valor):
    """
    Classifica o tipo do veículo de forma conservadora:
    - se houver palavra de ambulância/patrimônio -> ambulância
    - se houver placa/van -> van
    - caso contrário -> ambulância
    """
    if not valor:
        return "ambulancia"

    texto = unicodedata.normalize("NFKD", str(valor))
    texto = texto.encode("ASCII", "ignore").decode("ASCII")
    texto = re.sub(r"\s+", " ", texto).strip().upper()

    if re.search(r"(?i)(AMBULANCIA|AMB\.?|PATRIMONIO|PATRIMÔNIO)", texto):
        return "ambulancia"

    if re.search(r"(?i)(VAN|VEICULO|VEÍCULO|PLACA)", texto):
        return "van"

    if re.fullmatch(r"[A-Z]{3}-?\d{4}", texto) or re.fullmatch(
        r"[A-Z]{3}\d[A-Z0-9]\d{2}", texto
    ):
        return "van"

    return "ambulancia"


class TransporteForm(forms.ModelForm):
    tipo_transporte = forms.ChoiceField(
        choices=[
            ("CONSULTA", "Consulta (ida)"),
            ("RETORNO", "Retorno (volta)"),
            ("OUTRO_MUNICIPIO", "Outro/Município"),
            ("OUTRO_FORA", "Outro/Fora do Município"),
        ],
        label="Tipo de Transporte",
        help_text="Selecione se é ida para consulta, retorno, ou outro.",
    )
    veiculo_livre = forms.CharField(
        required=False,
        label="Veículo (digitar manualmente)",
        help_text="Opcional. Se preencher aqui, será cadastrado ou selecionado automaticamente.",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Digite placa ou patrimônio do veículo",
                "list": "dl_veiculo_livre",
                "autocomplete": "off",
            }
        ),
    )
    clinica_manual = forms.CharField(
        required=False,
        label="Clínica (digitar manualmente)",
        help_text="Opcional. Se preencher aqui, esta clínica será usada no transporte.",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Digite o nome da clínica",
                "list": "dl_clinica_manual",
                "autocomplete": "off",
            }
        ),
    )
    condutor_manual = forms.CharField(
        required=False,
        label="Condutor (digitar manualmente)",
        help_text="Opcional. Se preencher aqui, este nome será usado no transporte.",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Digite o nome do condutor",
                "list": "dl_condutor_manual",
                "autocomplete": "off",
            }
        ),
    )
    enfermagem_manual = forms.CharField(
        required=False,
        label="Enfermagem (digitar manualmente)",
        help_text="Opcional. Se preencher aqui, este nome será usado no transporte.",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Digite o nome da enfermagem",
                "list": "dl_enfermagem_manual",
                "autocomplete": "off",
            }
        ),
    )

    def clean_data_transporte(self):
        from django.utils import timezone

        data = self.cleaned_data.get("data_transporte")
        if data and data < timezone.localdate():
            raise forms.ValidationError(
                "A data informada já passou. Selecione uma data igual ou posterior a hoje."
            )
        return data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "patrimonio" in self.fields:
            self.fields["patrimonio"].widget = forms.HiddenInput()

        if "clinica" in self.fields:
            self.fields["clinica"].label_from_instance = self._formatar_opcao_clinica

        if "veiculo" in self.fields:
            self.fields["veiculo"].label_from_instance = self._formatar_opcao_veiculo

        if "hora_saida" in self.fields:
            self.fields["hora_saida"].label = "Horário de Saída"

        if "hora_chegada" in self.fields:
            self.fields["hora_chegada"].label = "Horário de Chegada"

    @staticmethod
    def _formatar_opcao_veiculo(veiculo):
        lotacao_txt = f" (lotação: {getattr(veiculo, 'lotacao', 0) or 0})"

        if veiculo.tipo_veiculo == "ambulancia" and veiculo.patrimonio:
            return f"{veiculo.patrimonio} - Ambulância{lotacao_txt}"

        if veiculo.tipo_veiculo == "van" and veiculo.placa:
            return f"{veiculo.placa} - Van{lotacao_txt}"

        if veiculo.patrimonio:
            return f"{veiculo.patrimonio} - {veiculo.get_tipo_veiculo_display()}{lotacao_txt}"

        if veiculo.placa:
            return f"{veiculo.placa} - {veiculo.get_tipo_veiculo_display()}{lotacao_txt}"

        return f"{veiculo.get_tipo_veiculo_display()} sem identificação{lotacao_txt}"

    @staticmethod
    def _formatar_opcao_clinica(clinica):
        partes = [clinica.nome]
        if clinica.endereco:
            partes.append(clinica.endereco)
        if clinica.bairro:
            partes.append(clinica.bairro)
        return " - ".join(partes)

    def clean(self):
        cleaned_data = super().clean()
        paciente = cleaned_data.get("paciente")
        data_transporte = cleaned_data.get("data_transporte")
        veiculo = cleaned_data.get("veiculo")
        veiculo_livre = self.data.get("veiculo_livre", "").strip()

        clinica_manual = re.sub(r"\s+", " ", (cleaned_data.get("clinica_manual") or "").strip())
        condutor_manual = re.sub(r"\s+", " ", (cleaned_data.get("condutor_manual") or "").strip())
        enfermagem_manual = re.sub(r"\s+", " ", (cleaned_data.get("enfermagem_manual") or "").strip())

        cleaned_data["clinica_manual"] = clinica_manual
        cleaned_data["condutor_manual"] = condutor_manual
        cleaned_data["enfermagem_manual"] = enfermagem_manual

        if clinica_manual:
            clinica_existente = Clinica.objects.filter(nome__iexact=clinica_manual).first()
            if clinica_existente:
                cleaned_data["clinica"] = clinica_existente
            else:
                cleaned_data["clinica"] = Clinica.objects.create(nome=clinica_manual)

        if condutor_manual:
            condutor_existente = Condutor.objects.filter(nome__iexact=condutor_manual).first()
            if condutor_existente:
                cleaned_data["condutor"] = condutor_existente
            else:
                cleaned_data["condutor"] = Condutor.objects.create(nome=condutor_manual)

        if enfermagem_manual:
            enfermagem_existente = Enfermagem.objects.filter(nome__iexact=enfermagem_manual).first()
            if enfermagem_existente:
                cleaned_data["enfermagem"] = enfermagem_existente
            else:
                cleaned_data["enfermagem"] = Enfermagem.objects.create(nome=enfermagem_manual)

        if not veiculo and veiculo_livre:
            veiculo_existente = Veiculo.objects.filter(
                Q(patrimonio__iexact=veiculo_livre) | Q(placa__iexact=veiculo_livre)
            ).first()

            if veiculo_existente:
                cleaned_data["veiculo"] = veiculo_existente
            else:
                tipo = _inferir_tipo_veiculo_por_identificador(veiculo_livre)
                if tipo == "van":
                    novo_veiculo = Veiculo.objects.create(tipo_veiculo=tipo, placa=veiculo_livre)
                else:
                    novo_veiculo = Veiculo.objects.create(tipo_veiculo=tipo, patrimonio=veiculo_livre)
                cleaned_data["veiculo"] = novo_veiculo

        if paciente and data_transporte:
            qs_duplicado = Transporte.objects.filter(
                paciente=paciente,
                data_transporte=data_transporte,
            )
            if self.instance and self.instance.pk:
                qs_duplicado = qs_duplicado.exclude(pk=self.instance.pk)

            if qs_duplicado.exists() and not self.data.get("forcar_duplicado"):
                self.add_error(
                    "paciente",
                    'Este paciente já possui transporte cadastrado para esta data. Se desejar cadastrar mesmo assim, clique em "Cadastrar mesmo assim".',
                )

        return cleaned_data

    class Meta:
        model = Transporte
        exclude = ["lote_id"]
        widgets = {
            "data_transporte": forms.DateInput(attrs={"type": "date"}),
            "hora_saida": forms.TimeInput(attrs={"type": "time"}),
            "hora_chegada": forms.TimeInput(attrs={"type": "time"}),
            "observacoes": forms.Textarea(attrs={"rows": 2, "class": "auto-expand"}),
            "paciente": forms.Select(attrs={"id": "id_paciente_select", "size": "1"}),
        }


class EnfermagemForm(forms.ModelForm):
    class Meta:
        model = Enfermagem
        fields = "__all__"
        widgets = {
            "nome": forms.TextInput(
                attrs={"required": "required", "placeholder": "Nome da enfermagem"}
            )
        }


class PacienteForm(forms.ModelForm):
    horario_consulta = forms.TimeField(
        label="Horário da Consulta",
        required=False,
        widget=forms.TimeInput(
            attrs={
                "placeholder": "Ex: 14:30",
                "type": "time",
                "aria-label": "Horário da consulta (opcional)",
            }
        ),
        help_text="Se souber, informe o horário da consulta (opcional).",
    )
    consentimento_lgpd = forms.BooleanField(
        label="Li e concordo com o tratamento dos dados pessoais conforme a LGPD",
        required=True,
        help_text="O paciente ou responsável autoriza o uso dos dados para transporte e atendimento em saúde.",
    )
    ddd = forms.CharField(
        label="DDD",
        max_length=2,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "DDD", "style": "max-width:50px;"}),
    )
    cartao_sis = forms.CharField(
        label="Cartão SIS",
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Cartão SIS", "style": "max-width:110px;"}),
    )
    destino_preferencial_manual = forms.CharField(
        label="Clínica de Destino",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Ex: Hospital Municipal Central"}),
    )
    destino_preferencial_limpar = forms.BooleanField(
        required=False,
        widget=forms.HiddenInput(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "idade" in self.fields:
            self.fields["idade"].widget = forms.TextInput(
                attrs={
                    "inputmode": "numeric",
                    "pattern": "[0-9]*",
                    "placeholder": "Ex: 45",
                }
            )

        if "servico_status" in self.fields and not self.is_bound and not getattr(self.instance, "pk", None):
            self.fields["servico_status"].initial = "ativo"

    def _validar_texto_simples(self, valor, campo):
        if valor and re.search(r'[<>"\';\\|{}()\[\]@#~!$%^*=+`]', valor):
            raise forms.ValidationError(f"O campo {campo} contém caracteres inválidos.")
        return valor

    def clean_nome(self):
        return self._validar_texto_simples(self.cleaned_data.get("nome", ""), "Nome")

    def clean_rua(self):
        return self._validar_texto_simples(self.cleaned_data.get("rua", ""), "Rua")

    def clean_bairro(self):
        return self._validar_texto_simples(self.cleaned_data.get("bairro", ""), "Bairro")

    def clean_cidade(self):
        return self._validar_texto_simples(self.cleaned_data.get("cidade", ""), "Cidade")

    def save(self, commit=True):
        instance = super().save(commit=False)
        is_new = not bool(getattr(instance, "pk", None))

        instance.consentimento_lgpd = self.cleaned_data.get("consentimento_lgpd", False)

        status_servico = self.cleaned_data.get("servico_status") or (
            "ativo" if is_new else instance.servico_status
        )
        instance.servico_status = status_servico
        instance.servico_ativo = status_servico == "ativo"

        if status_servico == "ativo":
            instance.data_inativacao = None
            instance.motivo_inativacao = ""
            instance.observacao_inativacao = ""
            instance.data_prevista_retorno = None

        rua = self.cleaned_data.get("rua", "")
        numero = self.cleaned_data.get("numero", "")
        bairro = self.cleaned_data.get("bairro", "")
        cidade = self.cleaned_data.get("cidade", "")
        estado = self.cleaned_data.get("estado", "")
        cep = self.cleaned_data.get("cep", "")

        endereco_legado = f"{rua}, {numero}, {bairro}, {cidade}, {estado}"
        if cep:
            endereco_legado += f", {cep}"
        instance.endereco = endereco_legado

        instance.ddd = self.cleaned_data.get("ddd", "")
        instance.cartao_sis = self.cleaned_data.get("cartao_sis", "")

        if self.cleaned_data.get("destino_preferencial_limpar"):
            instance.destino_preferencial = None
        else:
            destino_manual = (self.cleaned_data.get("destino_preferencial_manual") or "").strip()
            if destino_manual:
                destino_manual = self._validar_texto_simples(destino_manual, "Destino preferencial manual")
                clinica = Clinica.objects.filter(nome__iexact=destino_manual).first()
                if clinica is None:
                    clinica = Clinica.objects.create(nome=destino_manual)
                instance.destino_preferencial = clinica

        if commit:
            instance.save()
        return instance

    def clean(self):
        cleaned_data = super().clean()
        nome = cleaned_data.get("nome")
        telefone = cleaned_data.get("telefone")
        rua = cleaned_data.get("rua")
        numero = cleaned_data.get("numero")
        bairro = cleaned_data.get("bairro")
        cidade = cleaned_data.get("cidade")
        estado = cleaned_data.get("estado")
        cep = cleaned_data.get("cep")
        latitude = cleaned_data.get("latitude")
        longitude = cleaned_data.get("longitude")
        oxigenio = cleaned_data.get("oxigenio")
        oxigenio_litros_min = cleaned_data.get("oxigenio_litros_min")

        if oxigenio:
            if oxigenio_litros_min is None:
                self.add_error("oxigenio_litros_min", "Informe a quantidade de O2 em litros por minuto.")
            elif oxigenio_litros_min <= 0:
                self.add_error("oxigenio_litros_min", "O valor de O2 deve ser maior que zero.")
        else:
            cleaned_data["oxigenio_litros_min"] = None

        servico_status = cleaned_data.get("servico_status") or "ativo"
        motivo_inativacao = cleaned_data.get("motivo_inativacao")
        data_inativacao = cleaned_data.get("data_inativacao")

        if servico_status == "ativo":
            cleaned_data["servico_ativo"] = True
            cleaned_data["data_inativacao"] = None
            cleaned_data["motivo_inativacao"] = ""
            cleaned_data["observacao_inativacao"] = ""
            cleaned_data["data_prevista_retorno"] = None
        else:
            cleaned_data["servico_ativo"] = False
            if not data_inativacao:
                self.add_error("data_inativacao", "Informe a data de inativacao para status suspenso/encerrado.")
            if not motivo_inativacao:
                self.add_error("motivo_inativacao", "Selecione o motivo da inativacao.")
            if servico_status != "suspenso":
                cleaned_data["data_prevista_retorno"] = None

        if not (rua and numero and bairro and cidade):
            raise forms.ValidationError(
                "Preencha todos os campos de endereço: rua, número, bairro e cidade."
            )

        if nome and telefone:
            qs = Paciente.objects.filter(nome=nome, telefone=telefone)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            paciente_existente_id = (self.data.get("paciente_existente_id") or "").strip()
            if paciente_existente_id and paciente_existente_id.isdigit():
                qs = qs.exclude(pk=int(paciente_existente_id))

            if qs.exists():
                self.add_error(
                    "nome",
                    "Já existe um paciente cadastrado com este nome e telefone.",
                )
                self.add_error(
                    "telefone",
                    "Já existe um paciente cadastrado com este nome e telefone.",
                )
                raise forms.ValidationError(
                    "Já existe um paciente cadastrado com este nome e telefone."
                )

        if not latitude or not longitude:
            if requests is not None and os.environ.get("DEBUG") == "True":
                try:
                    endereco_completo = f"{rua}, {numero}, {bairro}, {cidade}, {estado}"
                    if cep:
                        endereco_completo += f", {cep}"

                    url = "https://nominatim.openstreetmap.org/search"
                    params = {"q": endereco_completo, "format": "json", "limit": 1}
                    response = requests.get(
                        url,
                        params=params,
                        headers={"User-Agent": "transporte-pacientes-app"},
                        timeout=3,
                    )

                    if response.status_code == 200:
                        data = response.json()
                        if data:
                            cleaned_data["latitude"] = round(float(data[0]["lat"]), 6)
                            cleaned_data["longitude"] = round(float(data[0]["lon"]), 6)
                except Exception:
                    pass

        if cleaned_data.get("latitude") is not None:
            try:
                cleaned_data["latitude"] = format(round(float(cleaned_data["latitude"]), 6), ".6f")
            except Exception:
                cleaned_data["latitude"] = None

        if cleaned_data.get("longitude") is not None:
            try:
                cleaned_data["longitude"] = format(round(float(cleaned_data["longitude"]), 6), ".6f")
            except Exception:
                cleaned_data["longitude"] = None

        return cleaned_data

    def clean_ddd(self):
        ddd = (self.cleaned_data.get("ddd") or "").strip()
        if ddd and not re.fullmatch(r"\d{2}", ddd):
            raise forms.ValidationError("DDD deve conter exatamente 2 numeros.")
        return ddd

    def clean_telefone(self):
        telefone = (self.cleaned_data.get("telefone") or "").strip()
        if telefone:
            telefone_numerico = re.sub(r"\D", "", telefone)
            if len(telefone_numerico) in (10, 11) and not (self.cleaned_data.get("ddd") or "").strip():
                self.cleaned_data["ddd"] = telefone_numerico[:2]
                telefone_numerico = telefone_numerico[2:]
            if len(telefone_numerico) < 8 or len(telefone_numerico) > 9:
                raise forms.ValidationError(
                    "Telefone deve conter 8 ou 9 numeros (ou 10/11 com DDD)."
                )
            return telefone_numerico
        return telefone

    def clean_cep(self):
        cep = (self.cleaned_data.get("cep") or "").strip()
        if cep:
            cep_numerico = re.sub(r"\D", "", cep)
            if len(cep_numerico) != 8:
                raise forms.ValidationError("CEP deve conter 8 numeros.")
            return f"{cep_numerico[:5]}-{cep_numerico[5:]}"
        return cep

    def clean_estado(self):
        estado = (self.cleaned_data.get("estado") or "").strip().upper()
        if estado and not re.fullmatch(r"[A-Z]{2}", estado):
            raise forms.ValidationError("UF deve conter 2 letras (ex.: SP).")
        return estado

    class Meta:
        model = Paciente
        fields = "__all__"
        widgets = {
            "peso": forms.NumberInput(attrs={"placeholder": "Peso (kg)", "step": "0.01", "min": "0", "style": "width: 120px;"}),
            "oxigenio_litros_min": forms.NumberInput(attrs={"placeholder": "Ex: 2.0 L/min", "step": "0.1", "min": "0.1"}),
            "rua": forms.TextInput(attrs={"placeholder": "Rua"}),
            "numero": forms.TextInput(attrs={"placeholder": "Número"}),
            "bairro": forms.TextInput(attrs={"placeholder": "Bairro"}),
            "cidade": forms.TextInput(attrs={"placeholder": "Cidade"}),
            "estado": forms.TextInput(attrs={"placeholder": "UF", "maxlength": 2, "style": "width: 60px;"}),
            "cep": forms.TextInput(attrs={"placeholder": "CEP"}),
            "maca": forms.CheckboxInput(),
            "cadeirante": forms.CheckboxInput(),
            "acompanhantes": forms.NumberInput(attrs={"placeholder": "Qtd. acompanhantes", "min": "0", "max": "10", "style": "width: 90px;"}),
            "evolucao": forms.Textarea(attrs={"rows": 2, "class": "auto-expand"}),
            "observacoes": forms.Textarea(attrs={"rows": 2, "class": "auto-expand"}),
            "latitude": forms.HiddenInput(),
            "longitude": forms.HiddenInput(),
            "ddd": forms.TextInput(attrs={"placeholder": "DDD", "style": "max-width:50px;"}),
            "servico_status": forms.Select(attrs={"class": "form-select"}),
            "servico_ativo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "data_inativacao": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "motivo_inativacao": forms.Select(attrs={"class": "form-select"}),
            "observacao_inativacao": forms.Textarea(attrs={"rows": 2, "class": "form-control auto-expand"}),
            "data_prevista_retorno": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }


class PacienteSimplesForm(PacienteForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        campos_opcionais = [
            "status",
            "idade",
            "peso",
            "cartao_sis",
            "horario_consulta",
            "tratamento",
            "acompanhantes",
            "destino_preferencial_manual",
            "ddd",
            "telefone",
            "rua",
            "numero",
            "bairro",
            "cidade",
            "estado",
            "cep",
            "referencia",
            "observacoes",
        ]
        for campo in campos_opcionais:
            if campo in self.fields:
                self.fields[campo].required = False

    def clean(self):
        cleaned_data = super().clean()
        nome = cleaned_data.get("nome")
        telefone = cleaned_data.get("telefone")
        oxigenio = cleaned_data.get("oxigenio")
        oxigenio_litros_min = cleaned_data.get("oxigenio_litros_min")

        if oxigenio:
            if oxigenio_litros_min is None:
                self.add_error("oxigenio_litros_min", "Informe a quantidade de O2 em litros por minuto.")
            elif oxigenio_litros_min <= 0:
                self.add_error("oxigenio_litros_min", "O valor de O2 deve ser maior que zero.")
        else:
            cleaned_data["oxigenio_litros_min"] = None

        if nome and telefone:
            qs = Paciente.objects.filter(nome=nome, telefone=telefone)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            paciente_existente_id = (self.data.get("paciente_existente_id") or "").strip()
            if paciente_existente_id and paciente_existente_id.isdigit():
                qs = qs.exclude(pk=int(paciente_existente_id))
            if qs.exists():
                self.add_error("nome", "Já existe um paciente cadastrado com este nome e telefone.")

        return cleaned_data


class VeiculoForm(forms.ModelForm):
    class Meta:
        model = Veiculo
        fields = "__all__"
        widgets = {
            "lotacao": forms.NumberInput(attrs={"min": 1}),
        }


class CondutorForm(forms.ModelForm):
    def clean_nome(self):
        nome = re.sub(r"\s+", " ", (self.cleaned_data.get("nome") or "").strip())
        if not nome:
            raise forms.ValidationError("Informe o nome do condutor.")

        qs = Condutor.objects.filter(nome__iexact=nome)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Já existe um condutor com este nome.")
        return nome

    class Meta:
        model = Condutor
        fields = "__all__"


class ClinicaForm(forms.ModelForm):
    endereco_completo = forms.CharField(required=False, label="Endereço completo")

    def clean(self):
        cleaned_data = super().clean()
        nome = cleaned_data.get("nome")
        endereco = cleaned_data.get("endereco_completo") or cleaned_data.get("endereco")

        if not nome:
            raise forms.ValidationError("Informe o nome da clínica.")

        nome_norm = self._normalize_text(nome)
        endereco_norm = self._normalize_text(endereco)

        queryset = Clinica.objects.all()
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        for clinica in queryset:
            if nome_norm and self._normalize_text(clinica.nome) == nome_norm:
                self.add_error("nome", "Já existe uma clínica com este nome.")
            if endereco_norm and clinica.endereco and self._normalize_text(clinica.endereco) == endereco_norm:
                self.add_error("endereco_completo", "Já existe uma clínica com este endereço.")

        return cleaned_data

    @staticmethod
    def _normalize_text(value):
        if not value:
            return ""
        value = unicodedata.normalize("NFKD", str(value)).encode("ASCII", "ignore").decode("ASCII")
        value = re.sub(r"\s+", " ", value).strip().lower()
        return value

    def save(self, commit=True):
        instance = super().save(commit=False)
        endereco_completo = self.cleaned_data.get("endereco_completo")
        if endereco_completo:
            instance.endereco = endereco_completo
        if commit:
            instance.save()
        return instance

    class Meta:
        model = Clinica
        fields = "__all__"