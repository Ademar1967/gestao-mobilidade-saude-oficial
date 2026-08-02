from django import forms
from django.db.models import Q
from .models import Transporte, Paciente, Veiculo, Condutor, Clinica, Enfermagem
import sys
import io
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
try:
    import requests
except ImportError:
    requests = None
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
        help_text="Opcional. Se preencher aqui, este nome sera usado no transporte.",
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
        # Remove o campo 'patrimonio' do form padrão (será tratado manualmente)
        if "patrimonio" in self.fields:
            self.fields["patrimonio"].widget = forms.HiddenInput()
        if "clinica" in self.fields:
            self.fields["clinica"].label_from_instance = self._formatar_opcao_clinica
        if "veiculo" in self.fields:
            self.fields["veiculo"].label_from_instance = self._formatar_opcao_veiculo
        # Horarios do transporte devem ser independentes do horario de consulta do paciente.
        if "hora_saida" in self.fields:
            self.fields["hora_saida"].label = "Horário de Saída"
        if "hora_chegada" in self.fields:
            self.fields["hora_chegada"].label = "Horário de Chegada"

    @staticmethod
    def _formatar_opcao_veiculo(veiculo):
        # Exibe primeiro o patrimônio (ou placa, se van), depois o tipo
        lotacao_txt = f" (lotação: {getattr(veiculo, 'lotacao', 0) or 0})"
        if veiculo.tipo_veiculo == "ambulancia" and veiculo.patrimonio:
            return f"{veiculo.patrimonio} - Ambulância{lotacao_txt}"
        if veiculo.tipo_veiculo == "van" and veiculo.placa:
            return f"{veiculo.placa} - Van{lotacao_txt}"
        if veiculo.patrimonio:
            return f"{veiculo.patrimonio} - {veiculo.get_tipo_veiculo_display()}{lotacao_txt}"
        if veiculo.placa:
            return (
                f"{veiculo.placa} - {veiculo.get_tipo_veiculo_display()}{lotacao_txt}"
            )
        return f"{veiculo.get_tipo_veiculo_display()} sem identificação{lotacao_txt}"

    @staticmethod
    def _formatar_opcao_clinica(clinica):
        """Formata o label da clinica no select como 'Nome - Endereco - Bairro'."""
        partes = [clinica.nome]
        if clinica.endereco:
            partes.append(clinica.endereco)
        if clinica.bairro:
            partes.append(clinica.bairro)
        return " - ".join(partes)

    def clean(self):
        """Valida campos e permite cadastro automático de veículo manual."""
        cleaned_data = super().clean()
        paciente = cleaned_data.get("paciente")
        data_transporte = cleaned_data.get("data_transporte")
        veiculo = cleaned_data.get("veiculo")
        van_editavel = self.data.get("van_editavel")
        veiculo_livre = self.data.get("veiculo_livre", "").strip()
        clinica_manual = re.sub(
            r"\s+", " ", (cleaned_data.get("clinica_manual") or "").strip()
        )
        cleaned_data["clinica_manual"] = clinica_manual
        condutor_manual = re.sub(
            r"\s+", " ", (cleaned_data.get("condutor_manual") or "").strip()
        )
        cleaned_data["condutor_manual"] = condutor_manual

        enfermagem_manual = re.sub(
            r"\s+", " ", (cleaned_data.get("enfermagem_manual") or "").strip()
        )
        cleaned_data["enfermagem_manual"] = enfermagem_manual

        if clinica_manual:
            clinica_existente = Clinica.objects.filter(
                nome__iexact=clinica_manual
            ).first()
            if clinica_existente:
                cleaned_data["clinica"] = clinica_existente
            else:
                cleaned_data["clinica"] = Clinica.objects.create(nome=clinica_manual)

        if condutor_manual:
            condutor_existente = Condutor.objects.filter(
                nome__iexact=condutor_manual
            ).first()
            if condutor_existente:
                cleaned_data["condutor"] = condutor_existente
            else:
                cleaned_data["condutor"] = Condutor.objects.create(nome=condutor_manual)

        if enfermagem_manual:
            from .models import Enfermagem

            enfermagem_existente = Enfermagem.objects.filter(
                nome__iexact=enfermagem_manual
            ).first()
            if enfermagem_existente:
                cleaned_data["enfermagem"] = enfermagem_existente
            else:
                cleaned_data["enfermagem"] = Enfermagem.objects.create(
                    nome=enfermagem_manual
                )

        # Cadastro automático de veículo se preenchido manualmente
        if not veiculo and veiculo_livre:
            # Verifica se já existe veículo com esse patrimônio ou placa
            veiculo_existente = Veiculo.objects.filter(
                Q(patrimonio__iexact=veiculo_livre) | Q(placa__iexact=veiculo_livre)
            ).first()
            if veiculo_existente:
                cleaned_data["veiculo"] = veiculo_existente
                self.novo_veiculo_cadastrado = False
                self.veiculo_ja_existia = True
            else:
                # Decide tipo pelo formato (simples: placa tem letras e números, patrimônio só números)
                if re.match(r"^[A-Za-z]{3}\d[A-Za-z]\d{2}$", veiculo_livre) or re.match(
                    r"^[A-Za-z]{3}-\d{4}$", veiculo_livre
                ):
                    tipo = "van"
                    novo_veiculo = Veiculo.objects.create(
                        tipo_veiculo=tipo, placa=veiculo_livre
                    )
                else:
                    tipo = "ambulancia"
                    novo_veiculo = Veiculo.objects.create(
                        tipo_veiculo=tipo, patrimonio=veiculo_livre
                    )
                cleaned_data["veiculo"] = novo_veiculo
                self.novo_veiculo_cadastrado = True
                self.veiculo_ja_existia = False
        else:
            self.novo_veiculo_cadastrado = False
            self.veiculo_ja_existia = False

        if (
            veiculo
            and hasattr(veiculo, "tipo_veiculo")
            and veiculo.tipo_veiculo == "van"
        ):
            # Se for van terceirizada, usa o campo editável
            if van_editavel:
                cleaned_data["patrimonio"] = van_editavel
            else:
                self.add_error(
                    "veiculo", "Informe o identificador da van (campo editável)."
                )

        # Regra operacional orientativa: paciente usuario de O2 deve ser priorizado em ambulancia.
        veiculo_selecionado = cleaned_data.get("veiculo")
        self.alerta_oxigenio_ambulancia = False
        if paciente and getattr(paciente, "oxigenio", False):
            if (
                not veiculo_selecionado
                or getattr(veiculo_selecionado, "tipo_veiculo", "") != "ambulancia"
            ):
                self.alerta_oxigenio_ambulancia = True

        # Evita duplicidade operacional: mesmo paciente no mesmo dia, mas permite forçar se usuário quiser
        if paciente and data_transporte:
            qs_duplicado = Transporte.objects.filter(
                paciente=paciente,
                data_transporte=data_transporte,
            )
            if self.instance and self.instance.pk:
                qs_duplicado = qs_duplicado.exclude(pk=self.instance.pk)
            # Só bloqueia se não houver forcar_duplicado no POST
            forcar_duplicado = self.data.get("forcar_duplicado")
            if qs_duplicado.exists() and not forcar_duplicado:
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


# Formulário para Enfermagem
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
        widget=forms.TextInput(
            attrs={"placeholder": "DDD", "style": "max-width:50px;"}
        ),
    )
    cartao_sis = forms.CharField(
        label="Cartão SIS",
        max_length=10,
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Cartão SIS", "style": "max-width:110px;"}
        ),
    )
    destino_preferencial_manual = forms.CharField(
        label="Ou digite a clínica manualmente",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Ex: Hospital Municipal Central"}),
    )
    destino_preferencial_limpar = forms.BooleanField(
        required=False, widget=forms.HiddenInput()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        tabindexes = [
            ("nome", 1),
            ("cartao_sis", 2),
            ("horario_consulta", 3),
            ("destino_preferencial_manual", 4),
            ("destino_preferencial", 5),
            ("idade", 6),
            ("peso", 7),
            ("ddd", 8),
            ("telefone", 9),
            ("referencia", 10),
            ("rua", 11),
            ("numero", 12),
            ("bairro", 13),
            ("estado", 14),
            ("cidade", 15),
            ("cep", 16),
            ("oxigenio", 17),
            ("oxigenio_litros_min", 18),
            ("maca", 19),
            ("cadeirante", 20),
            ("acompanhantes", 21),
            ("evolucao", 22),
            ("observacoes", 23),
            ("servico_status",),
            ("servico_ativo",),
            ("data_inativacao",),
            ("motivo_inativacao",),
            ("observacao_inativacao",),
            ("data_prevista_retorno",),
            ("consentimento_lgpd", 24),
        ]

        # Aplica tabindex com fallback automático para itens sem índice explícito
        current_idx = 0
        for item in tabindexes:
            if isinstance(item, tuple):
                if len(item) == 2:
                    field, idx = item
                elif len(item) == 1:
                    field = item[0]
                    current_idx += 1
                    idx = current_idx
                else:
                    continue
            else:
                field = item
                current_idx += 1
                idx = current_idx

            if idx is not None:
                current_idx = idx

            if field in self.fields:
                self.fields[field].widget.attrs["tabindex"] = str(idx)

        # Widgets customizados
        widgets = {
            "observacoes": forms.Textarea(attrs={"rows": 3}),
            "evolucao": forms.Textarea(attrs={"rows": 3}),
        }

        if "horario_consulta" in self.fields:
            self.fields["horario_consulta"].widget.attrs["placeholder"] = "Ex: 14:30"
            self.fields["horario_consulta"].widget.attrs[
                "aria-label"
            ] = "Horário da consulta (opcional)"
        if "destino_preferencial" in self.fields:
            self.fields["destino_preferencial"].required = False
            self.fields["destino_preferencial"].label = "Clinica de Destino"
            self.fields["destino_preferencial"].help_text = (
                "Clínica sugerida como destino habitual do paciente (opcional)."
            )
        if "destino_preferencial_manual" in self.fields:
            self.fields["destino_preferencial_manual"].help_text = (
                "Se a clínica não existir na lista, digite aqui para cadastrar automaticamente."
            )
        if "latitude" in self.fields:
            self.fields["latitude"].required = False
        if "longitude" in self.fields:
            self.fields["longitude"].required = False
        if "oxigenio_litros_min" in self.fields:
            self.fields["oxigenio_litros_min"].widget.attrs[
                "placeholder"
            ] = "Ex: 2.0 L/min"
            self.fields["oxigenio_litros_min"].widget.attrs[
                "aria-label"
            ] = "Litros por minuto de oxigenio"
        if "cartao_sis" in self.fields:
            self.fields["cartao_sis"].widget.attrs["autocomplete"] = "off"
        if (
            "servico_status" in self.fields
            and not self.is_bound
            and not getattr(self.instance, "pk", None)
        ):
            self.fields["servico_status"].initial = "ativo"
        if "servico_status" in self.fields:
            self.fields["servico_status"].label = "Servico status"
            self.fields["servico_status"].choices = [
                ("ativo", "Ativo (padrao)"),
                ("suspenso", "Inativo temporario (suspenso)"),
                ("encerrado", "Inativo definitivo (encerrado)"),
            ]
        if "data_inativacao" in self.fields:
            self.fields["data_inativacao"].label = "Data inativacao"
            self.fields["data_inativacao"].required = False
        if "motivo_inativacao" in self.fields:
            self.fields["motivo_inativacao"].label = "Motivo inativacao"
            self.fields["motivo_inativacao"].required = False
        if "observacao_inativacao" in self.fields:
            self.fields["observacao_inativacao"].label = "Observacao inativacao"
            self.fields["observacao_inativacao"].required = False
        if "data_prevista_retorno" in self.fields:
            self.fields["data_prevista_retorno"].label = "Data prevista retorno"
            self.fields["data_prevista_retorno"].required = False
        # Placeholders explicativos adicionais
        if "nome" in self.fields:
            self.fields["nome"].widget.attrs[
                "placeholder"
            ] = "Nome completo do paciente"
            self.fields["nome"].widget.attrs["aria-label"] = "Nome completo do paciente"
        if "telefone" in self.fields:
            self.fields["telefone"].widget.attrs["placeholder"] = "Ex: 99999-9999"
            self.fields["telefone"].widget.attrs["aria-label"] = "Telefone do paciente"
        if "referencia" in self.fields:
            self.fields["referencia"].widget.attrs[
                "placeholder"
            ] = "Ponto de referência (opcional)"
            self.fields["referencia"].widget.attrs[
                "aria-label"
            ] = "Ponto de referência do endereço"

        # Esconde o campo cadeira_dobravel se não for cadeirante (feito no template)

    def _validar_texto_simples(self, valor, campo):
        """Rejeita caracteres especiais que não aparecem em nomes e endereços reais."""
        import re

        if valor and re.search(r'[<>"\';\\|{}()\[\]@#~!$%^*=+`]', valor):
            raise forms.ValidationError(f"O campo {campo} contém caracteres inválidos.")
        return valor

    def clean_nome(self):
        return self._validar_texto_simples(self.cleaned_data.get("nome", ""), "Nome")

    def clean_rua(self):
        return self._validar_texto_simples(self.cleaned_data.get("rua", ""), "Rua")

    def clean_bairro(self):
        return self._validar_texto_simples(
            self.cleaned_data.get("bairro", ""), "Bairro"
        )

    def clean_cidade(self):
        return self._validar_texto_simples(
            self.cleaned_data.get("cidade", ""), "Cidade"
        )

    def save(self, commit=True):
        """Salva o paciente montando o campo endereco legado, separando DDD e Cartão SIS."""
        instance = super().save(commit=False)
        is_new = not bool(getattr(instance, "pk", None))
        # Garante que o consentimento LGPD seja salvo corretamente
        instance.consentimento_lgpd = self.cleaned_data.get("consentimento_lgpd", False)

        # Regra de negocio: inicia ativo por padrao, mas respeita selecao explicita no formulario.
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

        # Monta o campo endereco legado para compatibilidade
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
        # Salva DDD separado
        instance.ddd = self.cleaned_data.get("ddd", "")
        # Salva Cartão SIS
        instance.cartao_sis = self.cleaned_data.get("cartao_sis", "")

        # Permite limpar destino selecionado ou cadastrar clínica nova por digitação manual.
        if self.cleaned_data.get("destino_preferencial_limpar"):
            instance.destino_preferencial = None
        else:
            destino_manual = (
                self.cleaned_data.get("destino_preferencial_manual") or ""
            ).strip()
            if destino_manual:
                destino_manual = self._validar_texto_simples(
                    destino_manual, "Destino preferencial manual"
                )
                clinica = Clinica.objects.filter(nome__iexact=destino_manual).first()
                if clinica is None:
                    clinica = Clinica.objects.create(nome=destino_manual)
                instance.destino_preferencial = clinica

        if commit:
            instance.save()
        return instance

    def clean(self):
        """Valida endereco completo, tenta geocodificar e impede cadastro de pacientes duplicados."""
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
        logger.info(
            f"Dados recebidos: rua={rua}, numero={numero}, bairro={bairro}, cidade={cidade}, estado={estado}, cep={cep}, latitude={latitude}, longitude={longitude}"
        )

        # Regra de negocio: se usa O2, exige fluxo em L/min; se nao usa, limpa o campo.
        if oxigenio:
            if oxigenio_litros_min is None:
                self.add_error(
                    "oxigenio_litros_min",
                    "Informe a quantidade de O2 em litros por minuto.",
                )
            elif oxigenio_litros_min <= 0:
                self.add_error(
                    "oxigenio_litros_min", "O valor de O2 deve ser maior que zero."
                )
        else:
            cleaned_data["oxigenio_litros_min"] = None

        # Regras de ciclo de vida do servico no cadastro/edicao.
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
                self.add_error(
                    "data_inativacao",
                    "Informe a data de inativacao para status suspenso/encerrado.",
                )
            if not motivo_inativacao:
                self.add_error("motivo_inativacao", "Selecione o motivo da inativacao.")
            if servico_status != "suspenso":
                cleaned_data["data_prevista_retorno"] = None

        # Validação: endereço detalhado (UF e CEP não obrigatórios)
        if not (rua and numero and bairro and cidade):
            logger.warning("Endereço incompleto!")
            raise forms.ValidationError(
                "Preencha todos os campos de endereço: rua, número, bairro e cidade."
            )
        # Monta endereço completo para geocodificação
        endereco_completo = f"{rua}, {numero}, {bairro}, {cidade}, {estado}"
        if cep:
            endereco_completo += f", {cep}"
        # Se latitude/longitude não preenchidos, tenta geocodificar
        if not latitude or not longitude:
            # Em produção (Render), desabilita geocodificação para evitar timeout
            # Apenas tenta em ambiente local
            if requests is not None and (
                "test" in sys.argv or os.environ.get("DEBUG") == "True"
            ):
                try:
                    logger.info(f"Buscando geolocalização para: {endereco_completo}")
                    url = f"https://nominatim.openstreetmap.org/search"
                    params = {"q": endereco_completo, "format": "json", "limit": 1}
                    response = requests.get(
                        url,
                        params=params,
                        headers={"User-Agent": "transporte-pacientes-app"},
                        timeout=3,  # Reduzido de 5 para 3 segundos
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if data:
                            lat = round(float(data[0]["lat"]), 6)
                            lon = round(float(data[0]["lon"]), 6)
                            cleaned_data["latitude"] = lat
                            cleaned_data["longitude"] = lon
                            logger.info(
                                f"Geolocalização encontrada: lat={lat}, lon={lon}"
                            )
                        else:
                            logger.warning(
                                "Endereço não encontrado no serviço de geolocalização. Salvando sem latitude/longitude."
                            )
                    else:
                        logger.warning(
                            f"Erro HTTP ao consultar geolocalização: status={response.status_code}. Salvando sem latitude/longitude."
                        )
                except Exception as e:
                    logger.warning(
                        f"Exceção ao tentar geocodificar: {e}. Salvando sem latitude/longitude."
                    )
            else:
                logger.info(
                    "Ambiente de produção: geocodificação desabilitada para evitar timeout."
                )
        # Permite nomes iguais, mas bloqueia apenas se nome E telefone coincidirem
        if nome and telefone:
            qs = Paciente.objects.filter(nome=nome, telefone=telefone)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            # Fallback de seguranca: quando o frontend envia paciente_existente_id,
            # exclui esse ID da busca de duplicidade mesmo se instance nao foi montada.
            paciente_existente_id = (
                self.data.get("paciente_existente_id") or ""
            ).strip()
            if paciente_existente_id and paciente_existente_id.isdigit():
                qs = qs.exclude(pk=int(paciente_existente_id))

            if qs.exists():
                logger.warning("Paciente duplicado!")
                # Mensagem de erro mais clara e visível
                self.add_error(
                    "nome",
                    "Já existe um paciente cadastrado com este nome e telefone. Caso seja outro paciente, altere o telefone.",
                )
                self.add_error(
                    "telefone",
                    "Já existe um paciente cadastrado com este nome e telefone. Caso seja outro paciente, altere o telefone.",
                )
                raise forms.ValidationError(
                    "Já existe um paciente cadastrado com este nome e telefone. Caso seja outro paciente, altere o telefone."
                )
        # Garante que latitude/longitude tenham no máximo 6 casas decimais, mas nunca bloqueia o cadastro
        if cleaned_data.get("latitude") is not None:
            try:
                # Garante string formatada para o DecimalField
                cleaned_data["latitude"] = format(
                    round(float(cleaned_data["latitude"]), 6), ".6f"
                )
            except Exception:
                cleaned_data["latitude"] = None
        if cleaned_data.get("longitude") is not None:
            try:
                cleaned_data["longitude"] = format(
                    round(float(cleaned_data["longitude"]), 6), ".6f"
                )
            except Exception:
                cleaned_data["longitude"] = None
        return cleaned_data

    def clean_ddd(self):
        """Valida que o DDD contenha exatamente 2 digitos numericos."""
        ddd = (self.cleaned_data.get("ddd") or "").strip()
        if ddd and not re.fullmatch(r"\d{2}", ddd):
            raise forms.ValidationError("DDD deve conter exatamente 2 numeros.")
        return ddd

    def clean_telefone(self):
        """Valida telefone (8-9 digitos). Aceita 10-11 digitos separando DDD automaticamente."""
        telefone = (self.cleaned_data.get("telefone") or "").strip()
        if telefone:
            telefone_numerico = re.sub(r"\D", "", telefone)
            if (
                len(telefone_numerico) in (10, 11)
                and not (self.cleaned_data.get("ddd") or "").strip()
            ):
                # Compatibilidade: se usuario informar DDD+telefone juntos, separa automaticamente.
                self.cleaned_data["ddd"] = telefone_numerico[:2]
                telefone_numerico = telefone_numerico[2:]
            if len(telefone_numerico) < 8 or len(telefone_numerico) > 9:
                raise forms.ValidationError(
                    "Telefone deve conter 8 ou 9 numeros (ou 10/11 com DDD)."
                )
            return telefone_numerico
        return telefone

    def clean_cep(self):
        """Valida e formata CEP no padrao XXXXX-XXX."""
        cep = (self.cleaned_data.get("cep") or "").strip()
        if cep:
            cep_numerico = re.sub(r"\D", "", cep)
            if len(cep_numerico) != 8:
                raise forms.ValidationError("CEP deve conter 8 numeros.")
            return f"{cep_numerico[:5]}-{cep_numerico[5:]}"
        return cep

    def clean_estado(self):
        """Valida UF com exatamente 2 letras e converte para maiusculo."""
        estado = (self.cleaned_data.get("estado") or "").strip().upper()
        if estado and not re.fullmatch(r"[A-Z]{2}", estado):
            raise forms.ValidationError("UF deve conter 2 letras (ex.: SP).")
        return estado

    class Meta:
        model = Paciente
        fields = "__all__"
        widgets = {
            "peso": forms.NumberInput(
                attrs={
                    "placeholder": "Peso (kg)",
                    "step": "0.01",
                    "min": "0",
                    "style": "width: 120px;",
                }
            ),
            "oxigenio_litros_min": forms.NumberInput(
                attrs={"placeholder": "Ex: 2.0 L/min", "step": "0.1", "min": "0.1"}
            ),
            "rua": forms.TextInput(attrs={"placeholder": "Rua"}),
            "numero": forms.TextInput(attrs={"placeholder": "Número"}),
            "bairro": forms.TextInput(attrs={"placeholder": "Bairro"}),
            "cidade": forms.TextInput(attrs={"placeholder": "Cidade"}),
            "estado": forms.TextInput(
                attrs={"placeholder": "UF", "maxlength": 2, "style": "width: 60px;"}
            ),
            "cep": forms.TextInput(attrs={"placeholder": "CEP"}),
            "maca": forms.CheckboxInput(),
            "cadeirante": forms.CheckboxInput(),
            "acompanhantes": forms.NumberInput(
                attrs={
                    "placeholder": "Qtd. acompanhantes",
                    "min": "0",
                    "max": "10",
                    "style": "width: 90px;",
                }
            ),
            "evolucao": forms.Textarea(attrs={"rows": 2, "class": "auto-expand"}),
            "observacoes": forms.Textarea(attrs={"rows": 2, "class": "auto-expand"}),
            "latitude": forms.HiddenInput(),
            "longitude": forms.HiddenInput(),
            "ddd": forms.TextInput(
                attrs={"placeholder": "DDD", "style": "max-width:50px;"}
            ),
            "servico_status": forms.Select(attrs={"class": "form-select"}),
            "servico_ativo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "data_inativacao": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "motivo_inativacao": forms.Select(attrs={"class": "form-select"}),
            "observacao_inativacao": forms.Textarea(
                attrs={"rows": 2, "class": "form-control auto-expand"}
            ),
            "data_prevista_retorno": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }


class PacienteSimplesForm(PacienteForm):
    """Versao enxuta para cadastro rapido de paciente."""

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
        if "status" in self.fields:
            self.fields["status"].label = "Situacao"
            self.fields["status"].widget.attrs["placeholder"] = "Selecionar"
        if "nome" in self.fields:
            self.fields["nome"].widget.attrs["placeholder"] = "Ex: Joao da Silva"
        if "idade" in self.fields:
            self.fields["idade"].widget.attrs["placeholder"] = "Ex: 65"
        if "peso" in self.fields:
            self.fields["peso"].widget.attrs["placeholder"] = "Ex: 75"
        if "cartao_sis" in self.fields:
            self.fields["cartao_sis"].widget.attrs["placeholder"] = "Opcional"
        if "tratamento" in self.fields:
            self.fields["tratamento"].widget.attrs["placeholder"] = "Ex: Oncologia"
        if "acompanhantes" in self.fields:
            self.fields["acompanhantes"].label = "Acompanhantes"
            self.fields["acompanhantes"].widget.attrs["placeholder"] = "0"
        if "destino_preferencial_manual" in self.fields:
            self.fields["destino_preferencial_manual"].widget.attrs[
                "placeholder"
            ] = "Digite a clinica de destino (opcional)"
        if "ddd" in self.fields:
            self.fields["ddd"].widget.attrs["placeholder"] = "11"
        if "telefone" in self.fields:
            self.fields["telefone"].widget.attrs["placeholder"] = "99999-9999"
        if "rua" in self.fields:
            self.fields["rua"].label = "Rua"
            self.fields["rua"].widget.attrs["placeholder"] = "Rua"
        if "numero" in self.fields:
            self.fields["numero"].label = "Numero"
            self.fields["numero"].widget.attrs["placeholder"] = "Numero"
        if "bairro" in self.fields:
            self.fields["bairro"].label = "Bairro"
            self.fields["bairro"].widget.attrs["placeholder"] = "Bairro"
        if "cidade" in self.fields:
            self.fields["cidade"].label = "Cidade"
            self.fields["cidade"].widget.attrs["placeholder"] = "Cidade"
        if "estado" in self.fields:
            self.fields["estado"].label = "Estado"
            self.fields["estado"].widget.attrs["placeholder"] = "UF"
        if "cep" in self.fields:
            self.fields["cep"].label = "Cep"
            self.fields["cep"].widget.attrs["placeholder"] = "CEP"
        if "referencia" in self.fields:
            self.fields["referencia"].label = "Referencia"
            self.fields["referencia"].widget.attrs[
                "placeholder"
            ] = "Ponto de referencia"
        if "observacoes" in self.fields:
            self.fields["observacoes"].widget.attrs[
                "placeholder"
            ] = "Observacoes gerais (opcional)"


class VeiculoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["placa"].required = False
        self.fields["placa"].help_text = "Preencha apenas para vans terceirizadas."
        self.fields["lotacao"].label = "Lotação operacional total"
        self.fields["lotacao"].help_text = (
            "Informe o total de pessoas permitido no veículo, incluindo o motorista."
        )

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
            raise forms.ValidationError("Ja existe um condutor com este nome.")
        return nome

    class Meta:
        model = Condutor
        fields = "__all__"


class ClinicaForm(forms.ModelForm):
    # Campo extra para autocomplete, valor será salvo em 'endereco' do modelo
    endereco_completo = forms.CharField(required=False, label="Endereço completo")
    logradouro = forms.CharField(required=False, label="Logradouro")
    numero = forms.CharField(required=False, label="Número")
    cep = forms.CharField(required=False, label="CEP")

    @staticmethod
    def _normalize_text(value):
        if not value:
            return ""
        value = (
            unicodedata.normalize("NFKD", str(value))
            .encode("ASCII", "ignore")
            .decode("ASCII")
        )
        value = re.sub(r"\s+", " ", value).strip().lower()
        return value

    def clean(self):
        cleaned_data = super().clean()
        nome = cleaned_data.get("nome")
        endereco = cleaned_data.get("endereco_completo") or cleaned_data.get("endereco")
        from .models import Clinica

        nome_norm = self._normalize_text(nome)
        endereco_norm = self._normalize_text(endereco)
        queryset = Clinica.objects.all().only("id", "nome", "endereco")
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        # Verificar duplicatas por NOME e ENDEREÇO
        for clinica in queryset:
            clinica_nome_norm = self._normalize_text(clinica.nome)
            clinica_endereco_norm = self._normalize_text(clinica.endereco or "")

            # Validar NOME duplicado
            if nome_norm and clinica_nome_norm == nome_norm:
                self.add_error("nome", "Ja existe uma clinica com este nome.")

            # Validar ENDEREÇO duplicado
            if (
                endereco_norm
                and clinica_endereco_norm
                and clinica_endereco_norm == endereco_norm
            ):
                self.add_error(
                    "endereco_completo", "Ja existe uma clinica com este endereco."
                )

        # Remove campos bairro, cidade, telefone do cleaned_data se existirem
        for campo in ["bairro", "cidade", "telefone"]:
            if campo in cleaned_data:
                cleaned_data.pop(campo)
        return cleaned_data

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
        widgets = {
            "endereco": forms.TextInput(attrs={"data-autocomplete-endereco": "true"}),
        }
