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

    return render(request, 'transporte_pacientes/mapa_operacional_selecao.html', {
        'condutores': condutores,
        'veiculos': veiculos,
        'hoje': hoje,
        'numeros_viagem': numeros_viagem,
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
    from .models import Transporte, Condutor, Veiculo

    data_str = (request.GET.get('data') or '').strip()
    origem = (request.GET.get('origem') or 'nem').strip().lower()
    empresa = (request.GET.get('empresa') or '').strip().upper()
    condutor_id = (request.GET.get('condutor') or '').strip()
    numero_viagem = (request.GET.get('numero_viagem') or '1a Viagem').strip()
    veiculo_id = (request.GET.get('veiculo') or '').strip()
    hora_saida_base = (request.GET.get('hora_saida') or '').strip()

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

    qs = qs.order_by('paciente__nome', 'id')

    linhas = []
    for ordem, t in enumerate(qs, start=1):
        p = t.paciente
        c = t.clinica

        nome_paciente = (p.nome if p else '') or ''
        paciente_id = p.id if p else ''
        acompanhantes = (getattr(p, 'acompanhantes', 0) if p else 0) or 0

        endereco_paciente = ''
        if p:
            endereco_paciente = ', '.join(x for x in [p.rua, p.numero] if x)

        bairro_paciente = (p.bairro if p else '') or ''

        horario = ''
        if p and p.horario_consulta:
            horario = p.horario_consulta.strftime('%H:%M')
        elif t.hora_saida:
            horario = t.hora_saida.strftime('%H:%M') if hasattr(t.hora_saida, 'strftime') else str(t.hora_saida)[:5]

        acompanhante_marca = 'X' if acompanhantes > 0 else 'SO'

        destino_nome = (c.nome if c else '') or ''

        telefone = ''
        if c and c.telefone:
            telefone = c.telefone
        elif p and p.telefone:
            ddd = p.ddd or ''
            telefone = f"{ddd} {p.telefone}".strip() if ddd else (p.telefone or '')

        observacao = ''
        if p:
            partes_obs = []
            if p.referencia:
                partes_obs.append(p.referencia)
            if p.observacoes:
                partes_obs.append(p.observacoes)
            observacao = ' / '.join(partes_obs)

        condicoes_especiais = _condicoes_especiais(p)

        linhas.append({
            'ordem': ordem,
            'nome': nome_paciente,
            'paciente_id': paciente_id,
            'acompanhantes': acompanhantes,
            'endereco': endereco_paciente,
            'bairro': bairro_paciente,
            'horario': horario,
            'acompanhante_marca': acompanhante_marca,
            'condicoes_especiais': condicoes_especiais,
            'destino': destino_nome,
            'telefone': telefone,
            'observacao': observacao,
        })

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
        'hora_saida_base': hora_saida_base,
        'total': len(linhas),
    })
