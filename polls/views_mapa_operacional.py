"""
Módulo: Mapa Operacional de Viagem
Gera a escala de transporte no formato frente/verso inspirado no modelo físico da CASEM.
"""
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.dateparse import parse_date


NUMERO_MAXIMO_VIAGENS = 10


@login_required
def mapa_operacional(request):
    """
    Tela de seleção do mapa:
    - data da viagem
    - empresa prestadora (padrão: NEM, editável)
    - motorista (lista dos condutores cadastrados)
    - número da viagem (1ª, 2ª, … até o limite configurado)
    """
    from .models import Condutor, Veiculo
    from django.utils import timezone

    condutores = Condutor.objects.order_by('nome')
    veiculos = Veiculo.objects.order_by('tipo_veiculo', 'patrimonio', 'placa')
    hoje = timezone.localdate().isoformat()
    numeros_viagem = [f"{i}ª Viagem" for i in range(1, NUMERO_MAXIMO_VIAGENS + 1)]

    return render(request, 'transporte_pacientes/mapa_operacional_selecao.html', {
        'condutores': condutores,
        'veiculos': veiculos,
        'hoje': hoje,
        'numeros_viagem': numeros_viagem,
    })


@login_required
def mapa_operacional_imprimir(request):
    """
    Gera o mapa imprimível (frente + verso na mesma página):
    - Filtra transportes pelo conjunto data + empresa + condutor + número da viagem
    - Monta lista numerada com espelhamento frente/verso
    """
    from .models import Transporte, Condutor, Veiculo

    data_str = (request.GET.get('data') or '').strip()
    origem = (request.GET.get('origem') or 'nem').strip().lower()
    empresa = (request.GET.get('empresa') or '').strip().upper()
    condutor_id = (request.GET.get('condutor') or '').strip()
    numero_viagem = (request.GET.get('numero_viagem') or '1ª Viagem').strip()
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

    qs = qs.order_by('paciente__nome')

    # Montar linhas numeradas: cada linha carrega dados da frente E do verso
    linhas = []
    for ordem, t in enumerate(qs, start=1):
        p = t.paciente
        c = t.clinica

        # ---- FRENTE ----
        nome_paciente = (p.nome if p else '') or ''
        paciente_id = p.id if p else ''
        endereco_paciente = ''
        if p:
            partes = [p.rua, p.numero]
            endereco_paciente = ', '.join(x for x in partes if x)
        bairro_paciente = (p.bairro if p else '') or ''
        horario = ''
        if p and p.horario_consulta:
            horario = p.horario_consulta.strftime('%H:%M')
        elif t.hora_saida:
            horario = t.hora_saida.strftime('%H:%M') if hasattr(t.hora_saida, 'strftime') else str(t.hora_saida)[:5]

        # Marcador de acompanhante (X = acompanha, SÓ = vai sozinho)
        acompanhante_marca = 'X' if (p and p.acompanhantes and p.acompanhantes > 0) else 'SÓ'

        # ---- VERSO ----
        destino_nome = (c.nome if c else '') or ''

        # Telefone: preferência pelo da clínica, depois do paciente
        telefone = ''
        if c and c.telefone:
            telefone = c.telefone
        elif p and p.telefone:
            ddd = p.ddd or ''
            fone = p.telefone or ''
            telefone = f"{ddd} {fone}".strip() if ddd else fone

        # Observação/referência do paciente
        observacao = ''
        if p:
            partes_obs = []
            if p.referencia:
                partes_obs.append(p.referencia)
            if p.observacoes:
                partes_obs.append(p.observacoes)
            observacao = ' / '.join(partes_obs)

        linhas.append({
            # frente
            'ordem': ordem,
            'nome': nome_paciente,
            'paciente_id': paciente_id,
            'endereco': endereco_paciente,
            'bairro': bairro_paciente,
            'horario': horario,
            'acompanhante_marca': acompanhante_marca,
            # verso
            'destino': destino_nome,
            'telefone': telefone,
            'observacao': observacao,
        })

    condutor_obj = None
    if condutor_id:
        try:
            condutor_obj = Condutor.objects.get(id=condutor_id)
        except Condutor.DoesNotExist:
            pass

    veiculo_obj = None
    if veiculo_id:
        try:
            veiculo_obj = Veiculo.objects.get(id=veiculo_id)
        except Veiculo.DoesNotExist:
            pass

    frota_label = ''
    if veiculo_obj:
        if veiculo_obj.patrimonio:
            frota_label = f"Patrimônio {veiculo_obj.patrimonio}"
        elif veiculo_obj.placa:
            frota_label = f"Placa {veiculo_obj.placa}"

    hoje_fmt = ''
    if data_filtro:
        # formata como 01/06/2026 - SEG
        dias_semana = ['SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB', 'DOM']
        hoje_fmt = f"{data_filtro.strftime('%d/%m/%Y')} - {dias_semana[data_filtro.weekday()]}"

    return render(request, 'transporte_pacientes/mapa_operacional_impressao.html', {
        'linhas': linhas,
        'origem': origem,
        'empresa': empresa,
        'data_fmt': hoje_fmt,
        'numero_viagem': numero_viagem,
        'condutor': condutor_obj,
        'veiculo': veiculo_obj,
        'frota_label': frota_label,
        'hora_saida_base': hora_saida_base,
        'total': len(linhas),
    })
