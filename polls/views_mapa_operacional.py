"""
Modulo: Mapa Operacional de Viagem
Gera escala no formato frente/verso inspirado no modelo fisico da CASEM.
"""

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.dateparse import parse_date

NUMERO_MAXIMO_VIAGENS = 10
LINHAS_POR_BLOCO = 20
CAPACIDADE_LOTE_PADRAO = 30


@login_required
def mapa_operacional(request):
    from django.utils import timezone
    from .models import Condutor, Veiculo

    condutores = Condutor.objects.order_by("nome")
    veiculos = Veiculo.objects.order_by("tipo_veiculo", "patrimonio", "placa")
    hoje = timezone.localdate().isoformat()
    numeros_viagem = [f"{i}a Viagem" for i in range(1, NUMERO_MAXIMO_VIAGENS + 1)]
    paciente_ids_param = (request.GET.get("paciente_ids") or "").strip()

    return render(
        request,
        "transporte_pacientes/mapa_operacional_selecao.html",
        {
            "condutores": condutores,
            "veiculos": veiculos,
            "hoje": hoje,
            "numeros_viagem": numeros_viagem,
            "form_values": {
                "origem": (request.GET.get("origem") or "nem").strip().lower(),
                "empresa": (request.GET.get("empresa") or "").strip().upper(),
                "numero_viagem": (
                    request.GET.get("numero_viagem") or "1a Viagem"
                ).strip(),
                "condutor": (request.GET.get("condutor") or "").strip(),
                "veiculo": (request.GET.get("veiculo") or "").strip(),
                "horario_consulta": (request.GET.get("horario_consulta") or "").strip(),
                "paciente_ids": paciente_ids_param,
            },
        },
    )


def _capacidade_lote(veiculo_obj, qs=None) -> int:
    if not veiculo_obj or not getattr(veiculo_obj, "lotacao", None):
        # Sem veículo específico, usa a maior lotação real dos veículos
        # presentes no filtro para não limitar artificialmente em 10.
        if qs is not None:
            lotacoes = []
            for t in qs:
                v = getattr(t, "veiculo", None)
                lot = getattr(v, "lotacao", None) if v else None
                if lot:
                    try:
                        lotacoes.append(int(lot))
                    except Exception:
                        pass
            if lotacoes:
                return max(1, max(lotacoes) - 1)
        return CAPACIDADE_LOTE_PADRAO
    try:
        lotacao_total = int(veiculo_obj.lotacao)
        return max(1, lotacao_total - 1)  # reserva 1 para motorista
    except Exception:
        return CAPACIDADE_LOTE_PADRAO


def _preencher_destino_compartilhado_em_bloco(bloco: dict) -> None:
    """Preenche o verso com o destino comum quando várias linhas compartilham o mesmo hospital."""
    linhas = bloco.get("linhas", []) or []
    linhas_normais = [linha for linha in linhas if not linha.get("separador")]
    if not linhas_normais:
        return

    destinos_preenchidos = [
        (linha.get("destino") or "").strip() for linha in linhas_normais if (linha.get("destino") or "").strip()
    ]
    if not destinos_preenchidos:
        return

    destinos_unicos = set(destinos_preenchidos)
    if len(destinos_unicos) != 1:
        return

    destino_comum = next(iter(destinos_unicos))
    enderecos_preenchidos = [
        (linha.get("endereco_clinica") or "").strip()
        for linha in linhas_normais
        if (linha.get("endereco_clinica") or "").strip()
    ]
    enderecos_unicos = set(enderecos_preenchidos)
    endereco_comum = next(iter(enderecos_unicos)) if len(enderecos_unicos) == 1 else ""

    for linha in linhas_normais:
        if not (linha.get("destino") or "").strip():
            linha["destino"] = destino_comum
        if not (linha.get("endereco_clinica") or "").strip() and endereco_comum:
            linha["endereco_clinica"] = endereco_comum


def _blocos_espelhados(linhas: list[dict], capacidade_lote: int) -> list[dict]:
    """
    Separa em lotes operacionais pela capacidade e depois em blocos de impressao.
    Inclui linhas separadoras para iniciar novo lote sem perder alinhamento frente/verso.
    """
    linhas_com_lote = []
    lote_atual = 1
    ocupacao_atual = 0

    for linha in linhas:
        acompanhantes = int(linha.get("acompanhantes") or 0)
        ocupacao_item = 1 + max(0, acompanhantes)

        if ocupacao_atual > 0 and (ocupacao_atual + ocupacao_item) > capacidade_lote:
            lote_atual += 1
            linhas_com_lote.append(
                {
                    "separador": True,
                    "lote_num": lote_atual,
                }
            )
            ocupacao_atual = 0

        linha["lote_num"] = lote_atual
        linhas_com_lote.append(linha)
        ocupacao_atual += ocupacao_item

    blocos = []
    if not linhas_com_lote:
        return [{"linhas": [], "vazios": []}]

    for i in range(0, len(linhas_com_lote), LINHAS_POR_BLOCO):
        trecho = linhas_com_lote[i : i + LINHAS_POR_BLOCO]
        blocos.append(
            {
                "linhas": trecho,
                "vazios": [None] * max(0, LINHAS_POR_BLOCO - len(trecho)),
            }
        )

    return blocos


def _condicoes_especiais(paciente) -> str:
    if not paciente:
        return ""

    condicoes = []
    if getattr(paciente, "cadeirante", False):
        condicoes.append("CADEIRANTE")
    if getattr(paciente, "maca", False):
        condicoes.append("MACA")
    if getattr(paciente, "oxigenio", False):
        litros = getattr(paciente, "oxigenio_litros_min", None)
        if litros is not None and str(litros).strip():
            condicoes.append(f"O2 {litros}L/min")
        else:
            condicoes.append("O2")

    acompanhantes = int(getattr(paciente, "acompanhantes", 0) or 0)
    if acompanhantes > 0:
        condicoes.append(f"{acompanhantes} AC")

    if getattr(paciente, "servico_status", "") and paciente.servico_status != "ativo":
        condicoes.append(paciente.servico_status.upper())

    return " | ".join(condicoes)


def _linha_from_paciente(paciente, ordem, transporte=None, clinica_fallback=None):
    """Monta um dict com os dados de um paciente para a tabela do mapa."""
    clinica = transporte.clinica if transporte else None
    if not clinica and clinica_fallback:
        clinica = clinica_fallback
    if not clinica and paciente and getattr(paciente, "destino_preferencial_id", None):
        clinica = paciente.destino_preferencial

    acompanhantes = (getattr(paciente, "acompanhantes", 0) if paciente else 0) or 0

    endereco_paciente = ""
    if paciente:
        endereco_paciente = ", ".join(x for x in [paciente.rua, paciente.numero] if x)

    horario = ""
    if paciente and paciente.horario_consulta:
        horario = paciente.horario_consulta.strftime("%H:%M")

    telefone = ""
    if paciente and paciente.telefone:
        ddd = paciente.ddd or ""
        telefone = f"{ddd} {paciente.telefone}".strip() if ddd else (paciente.telefone or "")

    idade = ""
    if paciente:
        idade_calculada = None
        if getattr(paciente, "data_nascimento", None):
            idade_calculada = paciente.calcular_idade()
        if idade_calculada is not None:
            idade = str(idade_calculada)
        elif getattr(paciente, "idade", None) not in (None, ""):
            idade = str(paciente.idade)

    observacao = ""
    if paciente:
        partes_obs = []
        if getattr(paciente, "referencia", None):
            partes_obs.append(str(paciente.referencia).strip())
        if getattr(paciente, "observacoes", None):
            partes_obs.append(str(paciente.observacoes).strip())
        if transporte and getattr(transporte, "observacoes", None):
            partes_obs.append(str(transporte.observacoes).strip())
        observacao = " / ".join([p for p in partes_obs if p])

    destino_label = ""
    if clinica and getattr(clinica, "nome", ""):
        destino_label = clinica.nome
    elif paciente and getattr(paciente, "destino_preferencial", None):
        destino_label = getattr(paciente.destino_preferencial, "nome", "") or ""

    endereco_clinica = ""
    if clinica:
        endereco_clinica = ", ".join(
            parte for parte in [clinica.endereco, clinica.bairro, clinica.cidade] if parte
        )

    referencia_paciente = ""
    if paciente and getattr(paciente, "referencia", None):
        referencia_paciente = str(paciente.referencia).strip()

    return {
        "ordem": ordem,
        "nome": (paciente.nome if paciente else "") or "",
        "paciente_id": paciente.id if paciente else "",
        "acompanhantes": acompanhantes,
        "endereco": endereco_paciente,
        "bairro": (paciente.bairro if paciente else "") or "",
        "horario": horario,
        "acompanhante_marca": "X" if acompanhantes > 0 else "SO",
        "condicoes_especiais": _condicoes_especiais(paciente),
        "destino": destino_label,
        "telefone": telefone,
        "idade": idade,
        "observacao": observacao,
        "endereco_clinica": endereco_clinica,
        "referencia": referencia_paciente,
    }


@login_required
def mapa_operacional_imprimir(request):
    from .models import Transporte, Condutor, Veiculo, Paciente

    data_str = (request.GET.get("data") or "").strip()
    origem = (request.GET.get("origem") or "nem").strip().lower()
    empresa = (request.GET.get("empresa") or "").strip().upper()
    condutor_id = (request.GET.get("condutor") or "").strip()
    numero_viagem = (request.GET.get("numero_viagem") or "1a Viagem").strip()
    veiculo_id = (request.GET.get("veiculo") or "").strip()
    horario_consulta_base = (request.GET.get("horario_consulta") or "").strip()
    paciente_ids_raw = (request.GET.get("paciente_ids") or "").strip()

    paciente_ids = []
    if paciente_ids_raw:
        for pid in paciente_ids_raw.split(","):
            pid = pid.strip()
            if pid.isdigit():
                paciente_ids.append(int(pid))

    if not empresa:
        empresa = "NEM" if origem == "nem" else "PREFEITURA"

    data_filtro = parse_date(data_str) if data_str else None

    qs = Transporte.objects.select_related("paciente", "clinica", "condutor", "veiculo")
    if data_filtro:
        qs = qs.filter(data_transporte=data_filtro)
    if condutor_id:
        qs = qs.filter(condutor_id=condutor_id)
    if veiculo_id:
        qs = qs.filter(veiculo_id=veiculo_id)
    if paciente_ids:
        qs = qs.filter(paciente_id__in=paciente_ids)

    qs = qs.order_by("paciente__nome", "id")

    linhas = []
    clinica_fallback = None

    if qs:
        clinicas_encontradas = [
            t.clinica for t in qs if getattr(t, "clinica", None) is not None
        ]
        ids_clinicas = {c.id for c in clinicas_encontradas if getattr(c, "id", None) is not None}
        if len(ids_clinicas) == 1:
            clinica_fallback = clinicas_encontradas[0]

    if paciente_ids:
        pacientes_qs = Paciente.objects.filter(id__in=paciente_ids)
        mapa_pacientes = {p.id: p for p in pacientes_qs}
        transportes_por_paciente = {
            t.paciente_id: t for t in qs if getattr(t, "paciente_id", None)
        }

        for ordem, pid in enumerate(paciente_ids, start=1):
            paciente = mapa_pacientes.get(pid)
            if not paciente:
                continue
            transporte = transportes_por_paciente.get(pid)
            linhas.append(
                _linha_from_paciente(
                    paciente,
                    ordem,
                    transporte,
                    clinica_fallback=clinica_fallback,
                )
            )
    else:
        for ordem, t in enumerate(qs, start=1):
            linhas.append(_linha_from_paciente(t.paciente, ordem, t))

    condutor_obj = (
        Condutor.objects.filter(id=condutor_id).first() if condutor_id else None
    )
    veiculo_obj = Veiculo.objects.filter(id=veiculo_id).first() if veiculo_id else None

    frota_label = ""
    if veiculo_obj:
        if veiculo_obj.patrimonio:
            frota_label = f"Patrimonio {veiculo_obj.patrimonio}"
        elif veiculo_obj.placa:
            frota_label = f"Placa {veiculo_obj.placa}"

    capacidade_lote = _capacidade_lote(veiculo_obj, qs)
    blocos = _blocos_espelhados(linhas, capacidade_lote)
    for bloco in blocos:
        _preencher_destino_compartilhado_em_bloco(bloco)
        linhas_normais = [linha for linha in bloco.get("linhas", []) if not linha.get("separador")]
        bloco["mostrar_coluna_observacao"] = any(
            (linha.get("observacao") or "").strip() for linha in linhas_normais
        )

    data_fmt = ""
    if data_filtro:
        dias_semana = ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"]
        data_fmt = (
            f"{data_filtro.strftime('%d/%m/%Y')} - {dias_semana[data_filtro.weekday()]}"
        )

    return render(
        request,
        "transporte_pacientes/mapa_operacional_impressao.html",
        {
            "linhas": linhas,
            "blocos": blocos,
            "linhas_por_bloco": LINHAS_POR_BLOCO,
            "origem": origem,
            "empresa": empresa,
            "data_fmt": data_fmt,
            "numero_viagem": numero_viagem,
            "condutor": condutor_obj,
            "veiculo": veiculo_obj,
            "frota_label": frota_label,
            "capacidade_lote": capacidade_lote,
            "horario_consulta_base": horario_consulta_base,
            "total": len(linhas),
        },
    )
