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

    condutores = Condutor.objects.order_by('nome')
    veiculos = Veiculo.objects.order_by('tipo_veiculo', 'patrimonio', 'placa')
    hoje = timezone.localdate().isoformat()
    numeros_viagem = [f"{i}a Viagem" for i in range(1, NUMERO_MAXIMO_VIAGENS + 1)]
    paciente_ids_param = (request.GET.get('paciente_ids') or '').strip()

    return render(request, 'transporte_pacientes/mapa_operacional_selecao.html', {
        'condutores': condutores,
        'veiculos': veiculos,
        'hoje': hoje,
        'numeros_viagem': numeros_viagem,
        'form_values': {
            'origem': (request.GET.get('origem') or 'nem').strip().lower(),
            'empresa': (request.GET.get('empresa') or '').strip().upper(),
            'numero_viagem': (request.GET.get('numero_viagem') or '1a Viagem').strip(),
            'condutor': (request.GET.get('condutor') or '').strip(),
            'veiculo': (request.GET.get('veiculo') or '').strip(),
            'horario_consulta': (request.GET.get('horario_consulta') or '').strip(),
            'paciente_ids': paciente_ids_param,
        },
    })


def _capacidade_lote(veiculo_obj, qs=None) -> int:
    if not veiculo_obj or not getattr(veiculo_obj, 'lotacao', None):
        # Sem veículo específico, usa a maior lotação real dos veículos
        # presentes no filtro para não limitar artificialmente em 10.
        if qs is not None:
            lotacoes = []
            for t in qs:
                v = getattr(t, 'veiculo', None)
                lot = getattr(v, 'lotacao', None) if v else None
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


def _blocos_espelhados(linhas: list[dict], capacidade_lote: int) -> list[dict]:
    """
    Separa em lotes operacionais pela capacidade e depois em blocos de impressao.
    Inclui linhas separadoras para iniciar novo lote sem perder alinhamento frente/verso.
    """
    linhas_com_lote = []
    lote_atual = 1
    ocupacao_atual = 0

    for linha in linhas:
        acompanhantes = int(linha.get('acompanhantes') or 0)
        ocupacao_item = 1 + max(0, acompanhantes)

        if ocupacao_atual > 0 and (ocupacao_atual + ocupacao_item) > capacidade_lote:
            lote_atual += 1
            linhas_com_lote.append({
                'separador': True,
                'lote_num': lote_atual,
            })
            ocupacao_atual = 0

        linha['lote_num'] = lote_atual
        linhas_com_lote.append(linha)
        ocupacao_atual += ocupacao_item

    blocos = []
    if not linhas_com_lote:
        return [{'linhas': [], 'vazios': range(0)}]

    for i in range(0, len(linhas_com_lote), LINHAS_POR_BLOCO):
        trecho = linhas_com_lote[i:i + LINHAS_POR_BLOCO]
        blocos.append({
            'linhas': trecho,
            'vazios': range(max(0, LINHAS_POR_BLOCO - len(trecho))),
        })

    return blocos


def _condicoes_especiais(paciente) -> str:
    if not paciente:
        return ''

    condicoes = []
    if getattr(paciente, 'cadeirante', False):
        condicoes.append('CADEIRANTE')
    if getattr(paciente, 'maca', False):
        condicoes.append('MACA')
    if getattr(paciente, 'oxigenio', False):
        litros = getattr(paciente, 'oxigenio_litros_min', None)
        if litros is not None and str(litros).strip():
            condicoes.append(f'O2 {litros}L/min')
        else:
            condicoes.append('O2')

    acompanhantes = int(getattr(paciente, 'acompanhantes', 0) or 0)
    if acompanhantes > 0:
        condicoes.append(f'{acompanhantes} AC')

    if getattr(paciente, 'servico_status', '') and paciente.servico_status != 'ativo':
        condicoes.append(paciente.servico_status.upper())

    return ' | '.join(condicoes)


@login_required
def mapa_operacional_imprimir(request):
    from .models import Transporte, Condutor, Veiculo, Paciente

    data_str = (request.GET.get('data') or '').strip()
    origem = (request.GET.get('origem') or 'nem').strip().lower()
    empresa = (request.GET.get('empresa') or '').strip().upper()
    condutor_id = (request.GET.get('condutor') or '').strip()
    numero_viagem = (request.GET.get('numero_viagem') or '1a Viagem').strip()
    veiculo_id = (request.GET.get('veiculo') or '').strip()
    horario_consulta_base = (request.GET.get('horario_consulta') or '').strip()
    paciente_ids_raw = (request.GET.get('paciente_ids') or '').strip()

    paciente_ids = []
    if paciente_ids_raw:
        for pid in paciente_ids_raw.split(','):
            pid = pid.strip()
            if pid.isdigit():
                paciente_ids.append(int(pid))

    if not empresa:
        empresa = 'NEM' if origem == 'nem' else 'PREFEITURA'

    data_filtro = parse_date(data_str) if data_str else None

    qs = Transporte.objects.select_related('paciente', 'clinica', 'condutor', 'veiculo')
    if data_filtro:
        qs = qs.filter(data_transporte=data_filtro)
    if condutor_id:
        qs = qs.filter(condutor_id=condutor_id)
    if veiculo_id:
        qs = qs.filter(veiculo_id=veiculo_id)
    if paciente_ids:
        qs = qs.filter(paciente_id__in=paciente_ids)

    qs = qs.order_by('paciente__nome', 'id')

    linhas = []

    def _linha_from_paciente(paciente, ordem, transporte=None):
        clinica = transporte.clinica if transporte else None
        acompanhantes = (getattr(paciente, 'acompanhantes', 0) if paciente else 0) or 0

        endereco_paciente = ''
        if paciente:
            endereco_paciente = ', '.join(x for x in [paciente.rua, paciente.numero] if x)

        horario = ''
        if paciente and paciente.horario_consulta:
            horario = paciente.horario_consulta.strftime('%H:%M')

        telefone = ''
        if clinica and clinica.telefone:
            telefone = clinica.telefone
        elif paciente and paciente.telefone:
            ddd = paciente.ddd or ''
            telefone = f"{ddd} {paciente.telefone}".strip() if ddd else (paciente.telefone or '')

        observacao = ''
        if paciente:
            partes_obs = []
            if paciente.referencia:
                partes_obs.append(paciente.referencia)
            if paciente.observacoes:
                partes_obs.append(paciente.observacoes)
            observacao = ' / '.join(partes_obs)

        return {
            'ordem': ordem,
            'nome': (paciente.nome if paciente else '') or '',
            'paciente_id': paciente.id if paciente else '',
            'acompanhantes': acompanhantes,
            'endereco': endereco_paciente,
            'bairro': (paciente.bairro if paciente else '') or '',
            'horario': horario,
            'acompanhante_marca': 'X' if acompanhantes > 0 else 'SO',
            'condicoes_especiais': _condicoes_especiais(paciente),
            'destino': ((clinica.nome if clinica else '') or 'A definir') if paciente else '',
            'telefone': telefone,
            'observacao': observacao,
        }

    for ordem, t in enumerate(qs, start=1):
        linhas.append(_linha_from_paciente(t.paciente, ordem, t))

    # Se vieram pacientes selecionados, mas nenhum transporte ainda foi salvo,
    # gera o mapa diretamente com os dados operacionais do paciente.
    if not linhas and paciente_ids:
        pacientes_qs = Paciente.objects.filter(id__in=paciente_ids)
        mapa_pacientes = {p.id: p for p in pacientes_qs}
        pacientes_ordenados = [mapa_pacientes[pid] for pid in paciente_ids if pid in mapa_pacientes]
        for ordem, paciente in enumerate(pacientes_ordenados, start=1):
            linhas.append(_linha_from_paciente(paciente, ordem))

    condutor_obj = Condutor.objects.filter(id=condutor_id).first() if condutor_id else None
    veiculo_obj = Veiculo.objects.filter(id=veiculo_id).first() if veiculo_id else None

    frota_label = ''
    if veiculo_obj:
        if veiculo_obj.patrimonio:
            frota_label = f"Patrimonio {veiculo_obj.patrimonio}"
        elif veiculo_obj.placa:
            frota_label = f"Placa {veiculo_obj.placa}"

    capacidade_lote = _capacidade_lote(veiculo_obj, qs)
    blocos = _blocos_espelhados(linhas, capacidade_lote)

    data_fmt = ''
    if data_filtro:
        dias_semana = ['SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB', 'DOM']
        data_fmt = f"{data_filtro.strftime('%d/%m/%Y')} - {dias_semana[data_filtro.weekday()]}"

    return render(request, 'transporte_pacientes/mapa_operacional_impressao.html', {
        'linhas': linhas,
        'blocos': blocos,
        'linhas_por_bloco': LINHAS_POR_BLOCO,
        'origem': origem,
        'empresa': empresa,
        'data_fmt': data_fmt,
        'numero_viagem': numero_viagem,
        'condutor': condutor_obj,
        'veiculo': veiculo_obj,
        'frota_label': frota_label,
        'capacidade_lote': capacidade_lote,
        'horario_consulta_base': horario_consulta_base,
        'total': len(linhas),
    })
