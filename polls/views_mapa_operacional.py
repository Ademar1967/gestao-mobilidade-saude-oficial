import json
import re
from collections import OrderedDict
from datetime import timedelta
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time


NUMEROS_VIAGEM = [f"{i}ª Viagem" for i in range(1, 11)]


def _clean_text(value):
    texto = str(value or "")
    return texto.replace("�", "").strip()


def _parse_ids_csv(value):
    ids = []
    for parte in str(value or "").split(","):
        parte = parte.strip()
        if not parte:
            continue
        try:
            ids.append(int(parte))
        except ValueError:
            continue
    return ids


def _idade_from_paciente(paciente):
    if getattr(paciente, "idade", None) not in (None, ""):
        return str(paciente.idade)
    data_nascimento = getattr(paciente, "data_nascimento", None)
    if not data_nascimento:
        return "-"
    hoje = timezone.localdate()
    idade = hoje.year - data_nascimento.year
    if (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day):
        idade -= 1
    return str(max(0, idade))


def _condicoes_especiais(paciente):
    condicoes = []
    if getattr(paciente, "maca", False):
        condicoes.append("MACA")
    if getattr(paciente, "cadeirante", False):
        condicoes.append("CADEIRANTE")
    if getattr(paciente, "oxigenio", False):
        litros = getattr(paciente, "oxigenio_litros_min", None)
        if litros not in (None, ""):
            condicoes.append(f"O2 {litros} L/min")
        else:
            condicoes.append("O2")
    return " | ".join(condicoes) if condicoes else "-"


def _linha_from_paciente(paciente, ordem, transporte=None, clinica_fallback=None):
    clinica = None
    if transporte and getattr(transporte, "clinica", None):
        clinica = transporte.clinica
    elif clinica_fallback is not None:
        clinica = clinica_fallback

    destino = _clean_text(getattr(clinica, "nome", "")) if clinica else ""
    endereco_clinica = ""
    if clinica:
        partes = [
            _clean_text(getattr(clinica, "endereco", "")),
            _clean_text(getattr(clinica, "bairro", "")),
            _clean_text(getattr(clinica, "cidade", "")),
        ]
        endereco_clinica = " - ".join([p for p in partes if p])

    ddd = _clean_text(getattr(paciente, "ddd", ""))
    telefone_paciente = _clean_text(getattr(paciente, "telefone", ""))
    telefone = f"{ddd} {telefone_paciente}".strip() if ddd else telefone_paciente
    if not telefone and clinica is not None:
        telefone = _clean_text(getattr(clinica, "telefone", ""))

    rua = _clean_text(getattr(paciente, "rua", ""))
    numero = _clean_text(getattr(paciente, "numero", ""))
    endereco = f"{rua}, {numero}".strip(", ") if (rua or numero) else "-"

    referencia = _clean_text(getattr(paciente, "referencia", ""))
    observacoes_paciente = _clean_text(getattr(paciente, "observacoes", ""))
    observacoes_transporte = _clean_text(
        getattr(transporte, "observacoes", "") if transporte else ""
    )
    observacoes_lista = [
        texto
        for texto in [referencia, observacoes_paciente, observacoes_transporte]
        if texto
    ]

    acompanhantes = int(getattr(paciente, "acompanhantes", 0) or 0)
    acompanhante_marca = str(acompanhantes) if acompanhantes > 0 else "SO"

    horario = ""
    horario_consulta = getattr(paciente, "horario_consulta", None)
    if horario_consulta:
        horario = horario_consulta.strftime("%H:%M")

    return {
        "ordem": ordem,
        "paciente_id": paciente.id,
        "nome": _clean_text(getattr(paciente, "nome", "")),
        "telefone": telefone or "-",
        "idade": _idade_from_paciente(paciente),
        "endereco": endereco,
        "bairro": _clean_text(getattr(paciente, "bairro", "")) or "-",
        "referencia": referencia or "-",
        "observacao": " | ".join(observacoes_lista),
        "condicoes_especiais": _condicoes_especiais(paciente),
        "destino": destino,
        "endereco_clinica": endereco_clinica,
        "acompanhantes": acompanhantes,
        "acompanhante_marca": acompanhante_marca,
        "horario": horario,
        "data_transporte": getattr(transporte, "data_transporte", None),
        "veiculo_id": getattr(transporte, "veiculo_id", None),
        "condutor_id": getattr(transporte, "condutor_id", None),
    }


def _preencher_destino_compartilhado_em_bloco(bloco):
    linhas = [l for l in bloco.get("linhas", []) if not l.get("separador")]
    if not linhas:
        return bloco

    destino = ""
    endereco = ""
    for linha in linhas:
        if linha.get("destino"):
            destino = linha.get("destino")
            endereco = linha.get("endereco_clinica", "")
            break

    if not destino:
        return bloco

    for linha in linhas:
        linha["destino"] = destino
        if endereco and not linha.get("endereco_clinica"):
            linha["endereco_clinica"] = endereco
    return bloco


def _trip_key(linha):
    return (
        str(linha.get("data_transporte") or ""),
        str(linha.get("veiculo_id") or ""),
        str(linha.get("condutor_id") or ""),
    )


def _metadata_viagem_bloco(blocos, numero_viagem_texto):
    match = re.search(r"(\d+)", str(numero_viagem_texto or ""))
    trip_num = int(match.group(1)) if match else 1

    for idx, bloco in enumerate(blocos, start=1):
        bloco["trip_num"] = trip_num
        bloco["bloco_num"] = idx
        bloco["label"] = f"VIAGEM {trip_num} — BLOCO {idx}"
        bloco["mostrar_separador_antes"] = idx > 1
    return blocos


def _blocos_espelhados(linhas, capacidade_lote):
    capacidade = max(1, int(capacidade_lote or 1))
    grupos = OrderedDict()
    for linha in linhas:
        grupos.setdefault(_trip_key(linha), []).append(linha)

    blocos = []
    viagem_idx = 0
    bloco_global = 0

    for _, itens in grupos.items():
        viagem_idx += 1
        ordem = 0
        linhas_bloco = []
        ocupacao = 0

        for item in itens:
            ocupacao_item = 1 + max(0, int(item.get("acompanhantes", 0) or 0))

            if linhas_bloco and (ocupacao + ocupacao_item) > capacidade:
                bloco_global += 1
                bloco = {
                    "trip_num": viagem_idx,
                    "bloco_num": bloco_global,
                    "label": f"VIAGEM {viagem_idx} — BLOCO {bloco_global}",
                    "mostrar_separador_antes": bloco_global > 1,
                    "linhas": linhas_bloco,
                    "vazios": [],
                }
                bloco["mostrar_coluna_observacao"] = any(
                    bool((linha.get("observacao") or "").strip())
                    for linha in linhas_bloco
                    if not linha.get("separador")
                )
                blocos.append(_preencher_destino_compartilhado_em_bloco(bloco))

                linhas_bloco = []
                ocupacao = 0
                ordem = 0

            ordem += 1
            linha_atual = dict(item)
            linha_atual["ordem"] = ordem
            linhas_bloco.append(linha_atual)
            ocupacao += ocupacao_item

        if linhas_bloco:
            bloco_global += 1
            bloco = {
                "trip_num": viagem_idx,
                "bloco_num": bloco_global,
                "label": f"VIAGEM {viagem_idx} — BLOCO {bloco_global}",
                "mostrar_separador_antes": bloco_global > 1,
                "linhas": linhas_bloco,
                "vazios": [],
            }
            bloco["mostrar_coluna_observacao"] = any(
                bool((linha.get("observacao") or "").strip())
                for linha in linhas_bloco
                if not linha.get("separador")
            )
            blocos.append(_preencher_destino_compartilhado_em_bloco(bloco))

    return blocos


def _parse_salvar_payload(request):
    if (request.content_type or "").split(";")[0].strip().lower() == "application/json":
        try:
            return json.loads(request.body.decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            return {}

    payload = {
        "data": request.POST.get("data"),
        "padrao_agendamento": request.POST.get("padrao_agendamento"),
        "data_final": request.POST.get("data_final"),
        "apenas_dias_uteis": request.POST.get("apenas_dias_uteis"),
        "veiculo": request.POST.get("veiculo"),
        "condutor": request.POST.get("condutor"),
        "numero_viagem": request.POST.get("numero_viagem"),
        "observacoes": request.POST.get("observacoes"),
        "paciente_ids": request.POST.getlist("paciente_ids"),
    }
    return payload


def _to_bool(value):
    return str(value or "").strip().lower() in {"1", "true", "on", "sim", "yes"}


def _ids_alocados_na_data(data_ref):
    from .models import Transporte

    inicio = data_ref
    fim = data_ref + timedelta(days=1)
    return list(
        Transporte.objects.filter(data_transporte__gte=inicio, data_transporte__lt=fim)
        .values_list("paciente_id", flat=True)
        .distinct()
    )


def _coerce_paciente_ids(ids_raw):
    if isinstance(ids_raw, str):
        return _parse_ids_csv(ids_raw)

    ids = []
    for valor in ids_raw or []:
        try:
            ids.append(int(str(valor).strip()))
        except Exception:
            continue
    return ids


def _rotina_to_dict(rotina):
    return {
        "id": rotina.id,
        "nome": rotina.nome,
        "dados": {
            "origem": rotina.origem,
            "empresa": rotina.empresa,
            "padrao_agendamento": rotina.padrao_agendamento,
            "data_final": rotina.data_final.isoformat() if rotina.data_final else "",
            "apenas_dias_uteis": rotina.apenas_dias_uteis,
            "numero_viagem": rotina.numero_viagem,
            "condutor": str(rotina.condutor_id or ""),
            "veiculo": str(rotina.veiculo_id or ""),
            "horario_consulta": rotina.horario_consulta.strftime("%H:%M") if rotina.horario_consulta else "",
            "observacoes": rotina.observacoes or "",
            "paciente_ids": _coerce_paciente_ids(rotina.paciente_ids_json),
        },
        "atualizado_em": rotina.atualizado_em.isoformat(),
    }


def _datas_agendamento(data_inicial, padrao_agendamento, data_final_str, apenas_dias_uteis):
    padrao = str(padrao_agendamento or "data_unica").strip().lower()
    if padrao != "periodo":
        return [data_inicial]

    data_final = parse_date(str(data_final_str or "").strip())
    if not data_final:
        raise ValueError("Informe a data final para o agendamento por período.")
    if data_final < data_inicial:
        raise ValueError("A data final não pode ser menor que a data inicial.")

    datas = []
    cursor = data_inicial
    while cursor <= data_final:
        if (not apenas_dias_uteis) or cursor.weekday() < 5:
            datas.append(cursor)
        cursor += timedelta(days=1)

    if not datas:
        raise ValueError("Nenhuma data válida encontrada no período selecionado.")
    return datas


def _blocos_from_viagens_salvas(viagens, origem_padrao="nem"):
    blocos = []
    for viagem in viagens:
        blocos_qs = viagem.blocos.order_by("numero").prefetch_related(
            "transportes__paciente", "transportes__clinica", "transportes__veiculo", "transportes__condutor"
        )
        for bloco in blocos_qs:
            transportes = list(bloco.transportes.all().order_by("ordem", "id"))
            linhas = []
            for idx, transporte in enumerate(transportes, start=1):
                paciente = getattr(transporte, "paciente", None)
                if not paciente:
                    continue
                linha = _linha_from_paciente(
                    paciente,
                    idx,
                    transporte=transporte,
                    clinica_fallback=getattr(transporte, "clinica", None),
                )
                linha["ordem"] = int(transporte.ordem or idx)
                linhas.append(linha)

            veiculo_obj = viagem.veiculo
            frota_label = ""
            if veiculo_obj:
                if veiculo_obj.tipo_veiculo == "ambulancia" and veiculo_obj.patrimonio:
                    frota_label = f"AMB {veiculo_obj.patrimonio}"
                elif veiculo_obj.tipo_veiculo == "van" and veiculo_obj.placa:
                    frota_label = f"VAN {veiculo_obj.placa}"
                else:
                    frota_label = str(veiculo_obj)

            bloco_dict = {
                "trip_num": int(viagem.numero or 1),
                "bloco_num": int(bloco.numero or 1),
                "label": f"VIAGEM {int(viagem.numero or 1)} — BLOCO {int(bloco.numero or 1)}",
                "mostrar_separador_antes": False,
                "linhas": linhas,
                "vazios": [],
                "mostrar_coluna_observacao": any(bool((l.get("observacao") or "").strip()) for l in linhas),
                "data_fmt": viagem.data.strftime("%d/%m/%Y"),
                "numero_viagem": f"{int(viagem.numero or 1)}ª Viagem",
                "condutor_nome": getattr(getattr(viagem, "condutor", None), "nome", ""),
                "frota_label": frota_label,
                "origem": origem_padrao,
                "horario_consulta_base": "",
            }
            blocos.append(bloco_dict)

    return blocos


@login_required
def mapa_operacional_imprimir(request):
    from .models import Clinica, Condutor, Paciente, Transporte, Veiculo, Viagem

    data_filtro = parse_date(request.GET.get("data") or "") or timezone.localdate()
    paciente_ids_csv = (request.GET.get("paciente_ids") or "").strip()
    paciente_ids = _parse_ids_csv(paciente_ids_csv)
    origem = (request.GET.get("origem") or "nem").strip().lower() or "nem"
    empresa = (request.GET.get("empresa") or "NEM").strip() or "NEM"
    numero_viagem = (request.GET.get("numero_viagem") or "1ª Viagem").strip()
    padrao_agendamento = (request.GET.get("padrao_agendamento") or "data_unica").strip() or "data_unica"
    data_final_str = (request.GET.get("data_final") or "").strip()
    apenas_dias_uteis = _to_bool(request.GET.get("apenas_dias_uteis"))
    condutor_id = (request.GET.get("condutor") or "").strip()
    veiculo_id = (request.GET.get("veiculo") or "").strip()
    horario_consulta_base = (request.GET.get("horario_consulta") or "").strip()
    viagem_ids = _parse_ids_csv((request.GET.get("viagem_ids") or "").strip())

    if viagem_ids:
        viagens = list(
            Viagem.objects.select_related("veiculo", "condutor")
            .filter(id__in=viagem_ids)
            .order_by("data", "numero", "id")
        )
        blocos_salvos = _blocos_from_viagens_salvas(viagens, origem_padrao=origem)
        if blocos_salvos:
            return render(
                request,
                "transporte_pacientes/mapa_operacional_impressao.html",
                {
                    "titulo": "Mapa Operacional",
                    "data_fmt": data_filtro.strftime("%d/%m/%Y"),
                    "empresa": empresa,
                    "origem": origem,
                    "numero_viagem": numero_viagem,
                    "condutor": None,
                    "veiculo": None,
                    "frota_label": "",
                    "horario_consulta_base": horario_consulta_base,
                    "blocos": blocos_salvos,
                },
            )

    try:
        datas_agendamento = _datas_agendamento(
            data_filtro,
            padrao_agendamento,
            data_final_str,
            apenas_dias_uteis,
        )
    except ValueError:
        datas_agendamento = [data_filtro]

    transportes_qs = Transporte.objects.select_related("paciente", "clinica", "veiculo", "condutor")
    capacidade = 50
    veiculo_obj = Veiculo.objects.filter(id=veiculo_id).first() if veiculo_id else None
    if veiculo_obj and getattr(veiculo_obj, "lotacao", None):
        try:
            capacidade = max(1, int(veiculo_obj.lotacao) - 1)
        except Exception:
            capacidade = 50

    condutor_obj = Condutor.objects.filter(id=condutor_id).first() if condutor_id else None
    frota_label = ""
    if veiculo_obj:
        if veiculo_obj.tipo_veiculo == "ambulancia" and veiculo_obj.patrimonio:
            frota_label = f"AMB {veiculo_obj.patrimonio}"
        elif veiculo_obj.tipo_veiculo == "van" and veiculo_obj.placa:
            frota_label = f"VAN {veiculo_obj.placa}"
        else:
            frota_label = str(veiculo_obj)

    blocos = []
    for data_viagem in datas_agendamento:
        transportes_qs_data = transportes_qs.filter(
            data_transporte__gte=data_viagem,
            data_transporte__lt=data_viagem + timedelta(days=1),
        )
        if condutor_id:
            transportes_qs_data = transportes_qs_data.filter(condutor_id=condutor_id)
        if veiculo_id:
            transportes_qs_data = transportes_qs_data.filter(veiculo_id=veiculo_id)
        if paciente_ids:
            transportes_qs_data = transportes_qs_data.filter(paciente_id__in=paciente_ids)

        transportes = list(transportes_qs_data.order_by("id"))
        transportes_por_paciente = {t.paciente_id: t for t in transportes if t.paciente_id}

        if paciente_ids:
            pacientes = list(Paciente.objects.filter(id__in=paciente_ids))
            pacientes_por_id = {p.id: p for p in pacientes}
            pacientes_ordenados = [
                pacientes_por_id[pid] for pid in paciente_ids if pid in pacientes_por_id
            ]
        else:
            pacientes_ordenados = [
                t.paciente
                for t in transportes
                if getattr(t, "paciente", None) is not None
            ]

        clinica_fallback = None
        if transportes:
            clinica_fallback = transportes[0].clinica
        elif paciente_ids:
            clinica_fallback_id = (
                Transporte.objects.filter(paciente_id__in=paciente_ids)
                .exclude(clinica_id__isnull=True)
                .values_list("clinica_id", flat=True)
                .order_by("id")
                .first()
            )
            if clinica_fallback_id:
                clinica_fallback = Clinica.objects.filter(id=clinica_fallback_id).first()

        linhas = []
        for idx, paciente in enumerate(pacientes_ordenados, start=1):
            transporte = transportes_por_paciente.get(paciente.id)
            linhas.append(_linha_from_paciente(paciente, idx, transporte, clinica_fallback=clinica_fallback))

        blocos_dia = _blocos_espelhados(linhas, capacidade)
        if not blocos_dia:
            blocos_dia = [{
                "trip_num": 1,
                "bloco_num": 1,
                "label": "VIAGEM 1 — BLOCO 1",
                "mostrar_separador_antes": False,
                "linhas": [],
                "vazios": [],
                "mostrar_coluna_observacao": False,
            }]

        for bloco in blocos_dia:
            bloco["data_fmt"] = data_viagem.strftime("%d/%m/%Y")
            bloco["numero_viagem"] = numero_viagem
            bloco["condutor_nome"] = getattr(condutor_obj, "nome", "") if condutor_obj else ""
            bloco["frota_label"] = frota_label
            bloco["origem"] = origem
            bloco["horario_consulta_base"] = horario_consulta_base
        blocos.extend(blocos_dia)

    if blocos:
        return render(
            request,
            "transporte_pacientes/mapa_operacional_impressao.html",
            {
                "titulo": "Mapa Operacional",
                "data_fmt": data_filtro.strftime("%d/%m/%Y"),
                "empresa": empresa,
                "origem": origem,
                "numero_viagem": numero_viagem,
                "condutor": condutor_obj,
                "veiculo": veiculo_obj,
                "frota_label": frota_label,
                "horario_consulta_base": horario_consulta_base,
                "blocos": blocos,
            },
        )

    return render(
        request,
        "transporte_pacientes/mapa_operacional_impressao.html",
        {
            "titulo": "Mapa Operacional",
            "data_fmt": data_filtro.strftime("%d/%m/%Y"),
            "empresa": empresa,
            "origem": origem,
            "numero_viagem": numero_viagem,
            "condutor": condutor_obj,
            "veiculo": veiculo_obj,
            "frota_label": frota_label,
            "horario_consulta_base": horario_consulta_base,
            "blocos": blocos,
        },
    )


@login_required
def mapa_operacional_impressao(request):
    return mapa_operacional_imprimir(request)


@login_required
def mapa_operacional(request):
    from .models import Condutor, Paciente, Veiculo

    hoje_iso = timezone.localdate().isoformat()
    somente_ativos = _to_bool(request.GET.get("somente_ativos", "1"))
    pagina_pacientes = request.GET.get("pagina_pacientes", "1")

    form_values = {
        "origem": (request.GET.get("origem") or "nem").strip().lower() or "nem",
        "empresa": (request.GET.get("empresa") or "NEM").strip() or "NEM",
        "data": (request.GET.get("data") or hoje_iso).strip() or hoje_iso,
        "numero_viagem": (request.GET.get("numero_viagem") or "1ª Viagem").strip() or "1ª Viagem",
        "padrao_agendamento": (request.GET.get("padrao_agendamento") or "data_unica").strip() or "data_unica",
        "data_final": (request.GET.get("data_final") or "").strip(),
        "apenas_dias_uteis": (request.GET.get("apenas_dias_uteis") or "").strip(),
        "condutor": (request.GET.get("condutor") or "").strip(),
        "veiculo": (request.GET.get("veiculo") or "").strip(),
        "horario_consulta": (request.GET.get("horario_consulta") or "").strip(),
        "observacoes": (request.GET.get("observacoes") or "").strip(),
        "paciente_ids": (request.GET.get("paciente_ids") or "").strip(),
    }

    selected_patient_ids = _parse_ids_csv(form_values.get("paciente_ids", ""))
    pacientes_qs = Paciente.objects.order_by("id", "nome")
    if somente_ativos:
        pacientes_qs = pacientes_qs.filter(servico_ativo=True)

    paginator = Paginator(pacientes_qs, 20)
    page_obj = paginator.get_page(pagina_pacientes)

    data_ref = parse_date(form_values.get("data") or "") or timezone.localdate()
    alocados_na_data_ids = _ids_alocados_na_data(data_ref)

    filtros_paginacao = request.GET.copy()
    filtros_paginacao.pop("pagina_pacientes", None)
    paginacao_base_qs = filtros_paginacao.urlencode()

    filtros_status = request.GET.copy()
    filtros_status.pop("pagina_pacientes", None)
    filtros_status.pop("somente_ativos", None)
    status_base_qs = filtros_status.urlencode()

    context = {
        "hoje": hoje_iso,
        "numeros_viagem": NUMEROS_VIAGEM,
        "condutores": Condutor.objects.order_by("nome"),
        "veiculos": Veiculo.objects.order_by("tipo_veiculo", "patrimonio", "placa"),
        "form_values": form_values,
        "pacientes_cadastrados": page_obj.object_list,
        "pacientes_page_obj": page_obj,
        "somente_ativos": somente_ativos,
        "paginacao_base_qs": paginacao_base_qs,
        "status_base_qs": status_base_qs,
        "selected_patient_ids": selected_patient_ids,
        "alocados_na_data_ids": alocados_na_data_ids,
    }
    return render(request, "transporte_pacientes/mapa_operacional_selecao.html", context)


@login_required
def pacientes_alocados_por_data(request):
    data_ref = parse_date((request.GET.get("data") or "").strip())
    if not data_ref:
        return JsonResponse(
            {
                "ok": False,
                "erro": "Data inválida.",
                "error": "Data inválida.",
                "alocados_ids": [],
            },
            status=400,
        )

    ids = _ids_alocados_na_data(data_ref)
    return JsonResponse({"ok": True, "data": data_ref.isoformat(), "alocados_ids": ids})


@login_required
def rotinas_mapa_api(request):
    from .models import Condutor, RotinaMapaViagem, Veiculo

    if request.method == "GET":
        rotinas = RotinaMapaViagem.objects.filter(usuario=request.user).order_by("nome")
        return JsonResponse({"ok": True, "rotinas": [_rotina_to_dict(r) for r in rotinas]})

    if request.method != "POST":
        return JsonResponse(
            {"ok": False, "erro": "Método inválido.", "error": "Método inválido."},
            status=405,
        )

    try:
        payload = json.loads((request.body or b"{}").decode("utf-8"))
    except Exception:
        payload = {}

    action = str(payload.get("action") or "save").strip().lower()

    if action == "delete":
        rotina_id = payload.get("id")
        rotina = RotinaMapaViagem.objects.filter(id=rotina_id, usuario=request.user).first()
        if not rotina:
            return JsonResponse(
                {"ok": False, "erro": "Padrão não encontrado.", "error": "Padrão não encontrado."},
                status=404,
            )
        rotina.delete()
        rotinas = RotinaMapaViagem.objects.filter(usuario=request.user).order_by("nome")
        return JsonResponse({"ok": True, "rotinas": [_rotina_to_dict(r) for r in rotinas]})

    nome = str(payload.get("nome") or "").strip()
    dados = payload.get("dados") or {}
    if not nome:
        return JsonResponse(
            {"ok": False, "erro": "Informe o nome do padrão.", "error": "Informe o nome do padrão."},
            status=400,
        )

    rotina_id = payload.get("id")
    rotina = None
    if rotina_id:
        rotina = RotinaMapaViagem.objects.filter(id=rotina_id, usuario=request.user).first()

    if rotina is None:
        rotina = RotinaMapaViagem.objects.filter(usuario=request.user, nome=nome).first()

    if rotina is None:
        rotina = RotinaMapaViagem(usuario=request.user, nome=nome)

    rotina.nome = nome
    rotina.origem = str(dados.get("origem") or "nem").strip().lower() or "nem"
    rotina.empresa = str(dados.get("empresa") or "NEM").strip() or "NEM"
    rotina.padrao_agendamento = str(dados.get("padrao_agendamento") or "data_unica").strip() or "data_unica"
    rotina.apenas_dias_uteis = _to_bool(dados.get("apenas_dias_uteis"))
    rotina.numero_viagem = str(dados.get("numero_viagem") or "1ª Viagem").strip() or "1ª Viagem"
    rotina.observacoes = str(dados.get("observacoes") or "").strip()

    data_final = parse_date(str(dados.get("data_final") or "").strip())
    rotina.data_final = data_final

    horario_consulta = parse_time(str(dados.get("horario_consulta") or "").strip())
    rotina.horario_consulta = horario_consulta

    condutor_id = str(dados.get("condutor") or "").strip()
    veiculo_id = str(dados.get("veiculo") or "").strip()
    rotina.condutor = Condutor.objects.filter(id=condutor_id).first() if condutor_id else None
    rotina.veiculo = Veiculo.objects.filter(id=veiculo_id).first() if veiculo_id else None

    rotina.paciente_ids_json = _coerce_paciente_ids(dados.get("paciente_ids") or [])
    rotina.save()

    rotinas = RotinaMapaViagem.objects.filter(usuario=request.user).order_by("nome")
    return JsonResponse(
        {
            "ok": True,
            "rotina": _rotina_to_dict(rotina),
            "rotinas": [_rotina_to_dict(r) for r in rotinas],
        }
    )


@login_required
def salvar_viagem(request):
    from .models import Bloco, Condutor, Paciente, Transporte, Veiculo, Viagem

    payload = _parse_salvar_payload(request)
    ajax = (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or (request.content_type or "").startswith("application/json")
    )

    try:
        if request.method != "POST":
            if ajax:
                return JsonResponse(
                    {"ok": False, "erro": "Método inválido.", "error": "Método inválido."},
                    status=405,
                )
            return redirect("transporte_pacientes:mapa_operacional")

        data_str = str(payload.get("data") or "").strip()
        padrao_agendamento = str(payload.get("padrao_agendamento") or "data_unica").strip()
        data_final_str = str(payload.get("data_final") or "").strip()
        apenas_dias_uteis = _to_bool(payload.get("apenas_dias_uteis"))
        veiculo_id = str(payload.get("veiculo") or "").strip()
        condutor_id = str(payload.get("condutor") or "").strip()
        numero_viagem = str(payload.get("numero_viagem") or "1a Viagem").strip()
        observacoes = str(payload.get("observacoes") or "").strip()
        paciente_ids_raw = payload.get("paciente_ids") or []
        if isinstance(paciente_ids_raw, str):
            paciente_ids_raw = _parse_ids_csv(paciente_ids_raw)

        paciente_ids = []
        for valor in paciente_ids_raw:
            try:
                paciente_ids.append(int(str(valor).strip()))
            except Exception:
                pass

        if not data_str:
            msg = "Data é obrigatória."
            if ajax:
                return JsonResponse({"ok": False, "erro": msg, "error": msg}, status=400)
            messages.error(request, msg)
            return redirect("transporte_pacientes:mapa_operacional")

        data_filtro = parse_date(data_str)
        if not data_filtro:
            msg = "Data inválida."
            if ajax:
                return JsonResponse({"ok": False, "erro": msg, "error": msg}, status=400)
            messages.error(request, msg)
            return redirect("transporte_pacientes:mapa_operacional")

        try:
            datas_agendamento = _datas_agendamento(
                data_filtro,
                padrao_agendamento,
                data_final_str,
                apenas_dias_uteis,
            )
        except ValueError as exc:
            msg = str(exc)
            if ajax:
                return JsonResponse({"ok": False, "erro": msg, "error": msg}, status=400)
            messages.error(request, msg)
            return redirect("transporte_pacientes:mapa_operacional")

        veiculo_obj_fixo = Veiculo.objects.filter(id=veiculo_id).first() if veiculo_id else None
        condutor_obj_fixo = Condutor.objects.filter(id=condutor_id).first() if condutor_id else None

        capacidade_lote = 30
        if veiculo_obj_fixo and getattr(veiculo_obj_fixo, "lotacao", None):
            try:
                capacidade_lote = max(1, int(veiculo_obj_fixo.lotacao) - 1)
            except Exception:
                capacidade_lote = 30

        numero_int = 1
        texto_num = (numero_viagem or "").strip()
        if texto_num:
            match = re.search(r"(\d+)", texto_num)
            if match:
                numero_int = max(1, int(match.group(1)))

        total_viagens = 0
        total_transportes = 0
        total_blocos = 0
        primeira_viagem_id = None
        viagem_ids_salvas = []

        for data_viagem in datas_agendamento:
            qs_base = Transporte.objects.select_related("paciente", "veiculo", "condutor")
            qs_base = qs_base.filter(
                data_transporte__gte=data_viagem,
                data_transporte__lt=data_viagem + timedelta(days=1),
            )

            if paciente_ids:
                # Para seleção explícita de pacientes, prioriza o vínculo por paciente+data.
                # Condutor/veículo são filtros da viagem atual e não devem ocultar pacientes selecionados.
                qs_pacientes = qs_base.filter(paciente_id__in=paciente_ids).order_by("id")
                transportes_por_paciente = {}
                for transporte in qs_pacientes:
                    if transporte.paciente_id not in transportes_por_paciente:
                        transportes_por_paciente[transporte.paciente_id] = transporte

                faltantes = [pid for pid in paciente_ids if pid not in transportes_por_paciente]
                if faltantes:
                    pacientes_faltantes = Paciente.objects.in_bulk(faltantes)
                    for pid in faltantes:
                        paciente = pacientes_faltantes.get(pid)
                        if not paciente:
                            continue
                        transporte_novo = Transporte.objects.create(
                            paciente=paciente,
                            data_transporte=data_viagem,
                            veiculo=veiculo_obj_fixo,
                            condutor=condutor_obj_fixo,
                            clinica=getattr(paciente, "destino_preferencial", None),
                            tipo_transporte="CONSULTA",
                        )
                        transportes_por_paciente[pid] = transporte_novo

                transportes = [
                    transportes_por_paciente[pid]
                    for pid in paciente_ids
                    if pid in transportes_por_paciente
                ]
            else:
                qs = qs_base
                if condutor_id:
                    qs = qs.filter(condutor_id=condutor_id)
                if veiculo_id:
                    qs = qs.filter(veiculo_id=veiculo_id)
                transportes = list(qs.order_by("paciente_id", "id"))

            if not transportes:
                continue

            veiculo_obj = veiculo_obj_fixo or transportes[0].veiculo
            condutor_obj = condutor_obj_fixo or transportes[0].condutor

            viagem = Viagem.objects.create(
                data=data_viagem,
                numero=numero_int,
                veiculo=veiculo_obj,
                condutor=condutor_obj,
                status="rascunho",
                observacoes=observacoes,
            )
            if primeira_viagem_id is None:
                primeira_viagem_id = viagem.id
            viagem_ids_salvas.append(viagem.id)

            bloco_numero = 0
            ocupacao_atual = 0
            ordem = 0

            for transporte in transportes:
                acompanhantes = int(getattr(transporte.paciente, "acompanhantes", 0) or 0)
                ocupacao_item = 1 + max(0, acompanhantes)

                if (ocupacao_atual + ocupacao_item) > capacidade_lote:
                    bloco_numero += 1
                    bloco = Bloco.objects.create(viagem=viagem, numero=bloco_numero)
                    ocupacao_atual = 0
                    ordem = 0
                else:
                    bloco = viagem.blocos.order_by("-numero").first()
                    if bloco is None:
                        bloco_numero += 1
                        bloco = Bloco.objects.create(viagem=viagem, numero=bloco_numero)
                        ocupacao_atual = 0
                        ordem = 0

                ordem += 1
                transporte.bloco = bloco
                transporte.ordem = ordem
                transporte.save(update_fields=["bloco", "ordem"])
                ocupacao_atual += ocupacao_item

            total_viagens += 1
            total_transportes += len(transportes)
            total_blocos += viagem.blocos.count()

        if total_viagens == 0:
            msg = "Nenhum transporte encontrado para os filtros/período informado."
            if ajax:
                return JsonResponse({"ok": False, "erro": msg, "error": msg}, status=400)
            messages.error(request, msg)
            return redirect("transporte_pacientes:mapa_operacional")

        url = reverse("transporte_pacientes:mapa_operacional")
        if ajax:
            periodo_txt = f"{datas_agendamento[0]:%d/%m/%Y}"
            if len(datas_agendamento) > 1:
                periodo_txt = f"{datas_agendamento[0]:%d/%m/%Y} até {datas_agendamento[-1]:%d/%m/%Y}"
            return JsonResponse(
                {
                    "ok": True,
                    "message": "Viagens salvas com sucesso.",
                    "redirect": url,
                    "viagem_id": primeira_viagem_id,
                    "total_transportes": total_transportes,
                    "total_blocos": total_blocos,
                    "total_viagens": total_viagens,
                    "viagem_ids": viagem_ids_salvas,
                    "periodo_agendado": periodo_txt,
                }
            )

        if total_viagens == 1:
            messages.success(request, "Viagem salva com sucesso.")
        else:
            messages.success(request, f"{total_viagens} viagens foram salvas com sucesso.")
        return redirect("transporte_pacientes:mapa_operacional")

    except Exception as exc:
        msg = f"Erro ao salvar: {exc}"
        if ajax:
            return JsonResponse({"ok": False, "erro": msg, "error": msg}, status=500)
        messages.error(request, msg)
        return redirect("transporte_pacientes:mapa_operacional")