    
from django.db.models import Count
from django.contrib.admin.views.decorators import staff_member_required

# --- ESTATÍSTICA: Transportes por veículo ---
@staff_member_required
def estatistica_transportes_veiculo(request):
	from .models import Transporte, Veiculo
	qs = (
		Transporte.objects.values('veiculo__patrimonio', 'veiculo__placa')
		.annotate(total=Count('id'))
		.order_by('-total')
	)
	dados = [
		{'veiculo': (row['veiculo__patrimonio'] or row['veiculo__placa'] or 'Não informado'), 'total': row['total']}
		for row in qs
	]
	return render(request, 'transporte_pacientes/estatistica_veiculo.html', {'dados': dados})

# --- ESTATÍSTICA: Transportes por motorista (condutor) ---
@staff_member_required
def estatistica_transportes_condutor(request):
	from .models import Transporte, Condutor
	qs = (
		Transporte.objects.values('condutor__nome')
		.annotate(total=Count('id'))
		.order_by('-total')
	)
	dados = [
		{'condutor': row['condutor__nome'] or 'Não informado', 'total': row['total']}
		for row in qs
	]
	return render(request, 'transporte_pacientes/estatistica_condutor.html', {'dados': dados})

# --- ESTATÍSTICA: Transportes por mês/ano ---
@staff_member_required
def estatistica_transportes_periodo(request):
	from .models import Transporte
	from django.db.models.functions import TruncMonth
	qs = (
		Transporte.objects.annotate(mes=TruncMonth('data_transporte'))
		.values('mes')
		.annotate(total=Count('id'))
		.order_by('mes')
	)
	dados = [
		{'mes': row['mes'].strftime('%m/%Y') if row['mes'] else 'Sem data', 'total': row['total']}
		for row in qs
	]
	return render(request, 'transporte_pacientes/estatistica_periodo.html', {'dados': dados})

# --- ESTATÍSTICA: Transportes por clínica ---
@staff_member_required
def estatistica_transportes_clinica(request):
	from .models import Transporte, Clinica
	qs = (
		Transporte.objects.values('clinica__nome')
		.annotate(total=Count('id'))
		.order_by('-total')
	)
	dados = [
		{'clinica': row['clinica__nome'] or 'Não informado', 'total': row['total']}
		for row in qs
	]
	return render(request, 'transporte_pacientes/estatistica_clinica.html', {'dados': dados})

# --- ESTATÍSTICA: Transportes por tipo ---
@staff_member_required
def estatistica_transportes_tipo(request):
	from .models import Transporte
	tipos = dict(Transporte._meta.get_field('tipo_transporte').choices)
	qs = Transporte.objects.values('tipo_transporte').annotate(total=Count('id')).order_by('tipo_transporte')
	dados = [
		{'tipo': tipos.get(row['tipo_transporte'], row['tipo_transporte']), 'total': row['total']}
		for row in qs
	]
	return render(request, 'transporte_pacientes/estatistica_tipo.html', {'dados': dados})
from django.http import JsonResponse
# Endpoint para sugerir dados de retorno invertidos
def retorno_sugestao_api(request):
	from .models import Transporte, Paciente
	paciente_id = request.GET.get('paciente_id')
	if not paciente_id:
		return JsonResponse({'erro': 'Paciente não informado.'}, status=400)
	try:
		paciente = Paciente.objects.get(id=paciente_id)
	except Paciente.DoesNotExist:
		return JsonResponse({'erro': 'Paciente não encontrado.'}, status=404)
	# Busca o último transporte de consulta desse paciente
	consulta = Transporte.objects.filter(paciente=paciente, tipo_transporte='CONSULTA').order_by('-data_transporte', '-hora_saida').first()
	if not consulta:
		return JsonResponse({'erro': 'Nenhum transporte de consulta encontrado para este paciente.'}, status=404)
	# Sugerir dados invertidos: origem = clinica, destino = endereço do paciente
	sugestao = {
		'origem_nome': consulta.clinica.nome if consulta.clinica else '',
		'origem_endereco': consulta.clinica.endereco if consulta.clinica and hasattr(consulta.clinica, 'endereco') else '',
		'destino_rua': paciente.rua,
		'destino_numero': paciente.numero,
		'destino_bairro': paciente.bairro,
		'destino_cidade': paciente.cidade,
		'destino_estado': paciente.estado,
		'destino_cep': paciente.cep,
		'destino_referencia': paciente.referencia,
	}
	return JsonResponse(sugestao)
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from .models import Paciente, Transporte
from django.shortcuts import render
from django.utils import timezone
import logging

# --- API: Detalhes completos do paciente para busca global ---
@require_GET
def paciente_detalhes_api(request, paciente_id):
	# print(f"[DEBUG] Requisição detalhes paciente id={paciente_id}")
	try:
		p = Paciente.objects.get(id=paciente_id)
		print(f"[DEBUG] Paciente encontrado: {p.nome} (id={p.id})")
	except Paciente.DoesNotExist:
		print(f"[DEBUG] Paciente id={paciente_id} NÃO encontrado!")
		return JsonResponse({'erro': 'Paciente não encontrado.'}, status=404)
	except Exception as exc:
		print(f"[DEBUG] Erro inesperado ao buscar paciente id={paciente_id}: {exc}")
		return JsonResponse({'erro': f'Erro inesperado: {exc}'}, status=500)
	atualizacoes = []
	try:
		transportes = Transporte.objects.filter(paciente=p).order_by('-data_transporte')[:5]
		print(f"[DEBUG] Transportes encontrados: {len(transportes)}")
		for t in transportes:
			if not t.data_transporte:
				print(f"[DEBUG] Transporte id={t.id} ignorado (data_transporte nula)")
				continue
			clinica_nome = t.clinica.nome if t.clinica else ''
			veiculo_nome = str(t.veiculo) if t.veiculo else ''
			try:
				data_str = t.data_transporte.strftime('%d/%m/%Y')
				atualizacoes.append(f"{data_str} - {clinica_nome} - {veiculo_nome}")
				print(f"[DEBUG] Atualização adicionada: {data_str} - {clinica_nome} - {veiculo_nome}")
			except Exception as exc:
				print(f"[DEBUG] Erro ao montar atualização transporte id={t.id}: {exc}")
				continue
	except Exception as exc:
		print(f"[DEBUG] Erro ao buscar transportes: {exc}")

	dados = {
		'id': p.id,
		'nome': p.nome or '',
		'idade': p.idade or '',
		'peso': str(p.peso) if p.peso is not None else '',
		'cartao_sis': p.cartao_sis or '',
		'ddd': p.ddd or '',
		'telefone': p.telefone or '',
		'rua': p.rua or '',
		'numero': p.numero or '',
		'bairro': p.bairro or '',
		'cidade': p.cidade or '',
		'estado': p.estado or '',
		'cep': p.cep or '',
		'referencia': p.referencia or '',
		'observacoes': p.observacoes or '',
		'status': p.status or '',
		'oxigenio': bool(p.oxigenio),
		'oxigenio_litros_min': str(p.oxigenio_litros_min) if p.oxigenio_litros_min is not None else '',
		'maca': bool(p.maca),
		'cadeirante': bool(p.cadeirante),
		'acompanhantes': p.acompanhantes,
		'acompanhante': bool(p.acompanhantes),  # compatibilidade: True se tem pelo menos 1 acompanhante
		'evolucao': p.evolucao or '',
		'atualizacoes': atualizacoes,
	}
	try:
		print(f"[DEBUG] JSON de resposta: {dados}")
		return JsonResponse(dados)
	except Exception as exc:
		print(f"[DEBUG] ERRO AO SERIALIZAR JSON: {exc}")
		return JsonResponse({'erro': f'Erro ao serializar resposta: {exc}'}, status=500)

@require_GET
def pacientes_count_api(request):
    """Retorna a contagem total de pacientes cadastrados."""
    count = Paciente.objects.count()
    return JsonResponse({'count': count})

def get_context_with_now(context=None):
    if context is None:
        context = {}
    context['now'] = timezone.localtime(timezone.now())
    return context

from django.db import models
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
# --- AUTOCOMPLETE DE VEÍCULOS (AMBULÂNCIA POR PATRIMÔNIO, VAN POR PLACA) ---
@require_GET
def buscar_veiculos_sugestoes(request):
	from .models import Veiculo
	termo = (request.GET.get('q') or '').strip()
	if len(termo) < 2:
		return JsonResponse({'sucesso': True, 'resultados': []})
	queryset = (
		Veiculo.objects.only('id', 'patrimonio', 'placa', 'tipo_veiculo')
		.annotate(
			uso_count=models.Count('transportes'),
			ultima_data=models.Max('transportes__data_transporte')
		)
		.filter(
			(
				(models.Q(tipo_veiculo='ambulancia') & models.Q(patrimonio__icontains=termo)) |
				(models.Q(tipo_veiculo='van') & models.Q(placa__icontains=termo))
			)
		)
		.order_by('-uso_count', '-ultima_data', 'tipo_veiculo', 'patrimonio', 'placa')[:10]
	)
	resultados = []
	for v in queryset:
		identificador = v.patrimonio if v.tipo_veiculo == 'ambulancia' else v.placa
		resultados.append({
			'id': v.id,
			'nome': identificador or '',
			'patrimonio': v.patrimonio or '',
			'placa': v.placa or '',
			'tipo': v.tipo_veiculo,
			'uso_count': v.uso_count or 0,
		})
	return JsonResponse({'sucesso': True, 'resultados': resultados})
from django.shortcuts import render
# View para exibir mensagens recebidas do WhatsApp (aberta para teste)
def mensagens_whatsapp(request):
	from .models import MensagemWhatsApp
	mensagens = MensagemWhatsApp.objects.order_by('-data_recebimento')[:50]
	return render(request, 'transporte_pacientes/mensagens_whatsapp.html', {'mensagens': mensagens})
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from twilio.twiml.messaging_response import MessagingResponse

# Endpoint para receber mensagens do WhatsApp via Twilio
@csrf_exempt
def whatsapp_webhook(request):
	if request.method == 'POST':
		from django.utils.encoding import force_str
		body = request.POST.get('Body', '')
		from_number = request.POST.get('From', '')
		# Log da mensagem recebida
		print(f"Mensagem recebida de {from_number}: {body}")

		# Salvar mensagem no banco de dados
		from .models import MensagemWhatsApp
		MensagemWhatsApp.objects.create(numero=from_number, corpo=body)

		# Resposta automática orientando o usuário
		msg_instrucoes = (
		    "Olá! Para cadastrar um paciente, envie os dados neste formato:\n"
		    "Nome: [nome completo]\n"
		    "Idade: [idade]\n"
		    "Endereço: [endereço completo]\n"
		    "Telefone: [telefone]"
		)
		resp = MessagingResponse()
		resp.message(msg_instrucoes)
		return HttpResponse(str(resp), content_type='text/xml')
	return HttpResponse("Somente POST aceito", status=405)
from django.shortcuts import render, redirect, get_object_or_404
import logging
import shutil
from datetime import datetime
from pathlib import Path
from django.conf import settings
from .models import Condutor
from .forms import CondutorForm, EnfermagemForm


audit_logger = logging.getLogger("polls.audit")
from django.shortcuts import render, redirect, get_object_or_404
import logging
import shutil
from datetime import datetime
from pathlib import Path
from django.conf import settings
from .models import Condutor
from .forms import CondutorForm, EnfermagemForm


audit_logger = logging.getLogger("polls.audit")

def editar_condutor(request, condutor_id):
	"""Exibe e processa o formulario de edicao de condutor."""
	condutor = get_object_or_404(Condutor, id=condutor_id)
	if request.method == 'POST':
		form = CondutorForm(request.POST, instance=condutor)
		if form.is_valid():
			form.save()
			from django.contrib import messages
			messages.success(request, 'Nome do condutor atualizado com sucesso!')
			return redirect('transporte_pacientes:cadastrar_condutor')
	else:
		form = CondutorForm(instance=condutor)
	return render(request, 'transporte_pacientes/editar_condutor.html', {'form': form, 'condutor': condutor})
# View para editar enfermagem
def editar_enfermagem(request, enfermagem_id):
	"""Exibe e processa o formulario de edicao de membro de enfermagem."""
	from .models import Enfermagem
	enfermagem = get_object_or_404(Enfermagem, id=enfermagem_id)
	if request.method == 'POST':
		form = EnfermagemForm(request.POST, instance=enfermagem)
		if form.is_valid():
			form.save()
			from django.contrib import messages
			messages.success(request, 'Nome da enfermagem atualizado com sucesso!')
			return redirect('transporte_pacientes:cadastrar_enfermagem')
	else:
		form = EnfermagemForm(instance=enfermagem)
	return render(request, 'transporte_pacientes/editar_enfermagem.html', {'form': form, 'enfermagem': enfermagem})

# View para editar veiculo
def editar_veiculo(request, veiculo_id):
	"""Exibe e processa o formulario de edicao de veiculo."""
	from .models import Veiculo
	from .forms import VeiculoForm
	veiculo = get_object_or_404(Veiculo, id=veiculo_id)
	if request.method == 'POST':
		form = VeiculoForm(request.POST, instance=veiculo)
		if form.is_valid():
			form.save()
			from django.contrib import messages
			messages.success(request, 'Dados do veículo atualizados com sucesso!')
			return redirect('transporte_pacientes:cadastrar_veiculo')
	else:
		form = VeiculoForm(instance=veiculo)
	return render(request, 'transporte_pacientes/editar_veiculo.html', {'form': form, 'veiculo': veiculo})
# --- VIEWS DE TRANSPORTE ---
# Cadastro e listagem de transportes integrando todas as entidades principais.
import csv
from .forms import TransporteForm
from .models import Transporte
from django.shortcuts import render, redirect

from django.http import HttpResponse

@login_required
def exportar_pacientes_csv(request):
    """Exporta todos os pacientes cadastrados como arquivo CSV para download."""
    from .models import Paciente
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="pacientes.csv"'
    writer = csv.writer(response)
    campos = [f.name for f in Paciente._meta.fields if f.name != 'id']
    writer.writerow(campos)
    for obj in Paciente.objects.all():
        row = [getattr(obj, campo, '') for campo in campos]
        writer.writerow(row)
    return response
# --- VIEWS DE TRANSPORTE ---
# Cadastro e listagem de transportes integrando todas as entidades principais.
from .forms import TransporteForm
from .models import Transporte
from django.shortcuts import render, redirect

def buscar_clinicas_sugestoes(request):
	"""Retorna sugestoes de clinicas por nome: primeiro do banco, depois do CNES."""
	from django.http import JsonResponse
	from .models import Clinica
	termo = (request.GET.get('q') or '').strip()
	if len(termo) < 2:
		return JsonResponse({'sucesso': True, 'resultados': []})

	# 1) Clínicas já cadastradas no banco (prioridade)
	queryset = (
		Clinica.objects
		.only('id', 'nome', 'endereco', 'bairro', 'cidade', 'telefone')
		.annotate(
			uso_count=models.Count('transportes'),
			ultima_data=models.Max('transportes__data_transporte')
		)
		.filter(nome__icontains=termo)
		.order_by('-uso_count', '-ultima_data', 'nome')[:10]
	)
	resultados = [
		{
			'id': c.id,
			'nome': c.nome,
			'endereco': c.endereco or '',
			'bairro': c.bairro or '',
			'cidade': c.cidade or '',
			'telefone': c.telefone or '',
			'uso_count': c.uso_count or 0,
			'fonte': 'banco',
		}
		for c in queryset
	]

	# 2) Complementa com CNES se ainda há espaço (até 10 total)
	vagas = 10 - len(resultados)
	if vagas > 0:
		# Garante cache carregado
		global _AUTOCOMPLETE_DF, _AUTOCOMPLETE_NOMES_NORM
		if _AUTOCOMPLETE_DF is None:
			_AUTOCOMPLETE_DF, _AUTOCOMPLETE_NOMES_NORM = _load_autocomplete_df()
		df_cnes = _AUTOCOMPLETE_DF
		if df_cnes is not None:
			nomes_banco = {r['nome'].lower() for r in resultados}
			termo_norm = _normalize(termo)
			nomes_norm = df_cnes['nome'].apply(_normalize)
			mask = nomes_norm.str.contains(termo_norm, regex=False)
			for _, row in df_cnes[mask].head(vagas * 2).iterrows():
				if len(resultados) >= 10:
					break
				# Não duplicar o que já está no banco
				if row['nome'].lower() in nomes_banco:
					continue
				cidade = row.get('municipio', '')
				resultados.append({
					'id': None,
					'nome': f"{row['nome']} — {cidade}" if cidade else row['nome'],
					'endereco': f"{row['logradouro']}, {row['numero']}".strip(', '),
					'bairro': row.get('bairro', ''),
					'cidade': cidade,
					'telefone': '',
					'uso_count': 0,
					'fonte': 'cnes',
				})
	# 2b) Enriquecer resultados do banco que não têm endereço com dados do CSV
	if _AUTOCOMPLETE_DF is None:
		_AUTOCOMPLETE_DF, _AUTOCOMPLETE_NOMES_NORM = _load_autocomplete_df()
	if _AUTOCOMPLETE_DF is not None:
		df_ref = _AUTOCOMPLETE_DF
		nomes_norm_ref = df_ref['nome'].apply(_normalize)
		for r in resultados:
			if r['fonte'] == 'banco' and not r['endereco'] and not r['bairro']:
				alvo_norm = _normalize(r['nome'])
				matches = df_ref[nomes_norm_ref == alvo_norm]
				if matches.empty:
					# tenta match parcial
					matches = df_ref[nomes_norm_ref.str.contains(alvo_norm[:10], regex=False)]
				if not matches.empty:
					row = matches.iloc[0]
					cidade = row.get('municipio', '')
					r['endereco'] = f"{row['logradouro']}, {row['numero']}".strip(', ')
					r['bairro'] = row.get('bairro', '')
					r['cidade'] = cidade or r['cidade']
	audit_logger.info("Sugestoes de clinica consultadas", extra={"termo": termo, "quantidade": len(resultados)})
	return JsonResponse({'sucesso': True, 'resultados': resultados})


@login_required
@require_GET
def buscar_condutores_sugestoes(request):
	from .models import Condutor
	termo = (request.GET.get('q') or '').strip()
	if len(termo) < 2:
		return JsonResponse({'sucesso': True, 'resultados': []})

	queryset = (
		Condutor.objects
		.annotate(
			uso_count=models.Count('transportes'),
			ultima_data=models.Max('transportes__data_transporte')
		)
		.filter(nome__icontains=termo)
		.order_by('-uso_count', '-ultima_data', 'nome')[:10]
	)

	resultados = [
		{
			'id': c.id,
			'nome': c.nome or '',
			'uso_count': c.uso_count or 0,
		}
		for c in queryset
	]
	return JsonResponse({'sucesso': True, 'resultados': resultados})


@login_required
@require_GET
def buscar_enfermagem_sugestoes(request):
	from .models import Enfermagem
	termo = (request.GET.get('q') or '').strip()
	if len(termo) < 2:
		return JsonResponse({'sucesso': True, 'resultados': []})

	queryset = (
		Enfermagem.objects.only('id', 'nome')
		.annotate(
			uso_count=models.Count('transportes'),
			ultima_data=models.Max('transportes__data_transporte')
		)
		.filter(nome__icontains=termo)
		.order_by('-uso_count', '-ultima_data', 'nome')[:10]
	)

	resultados = [
		{
			'id': e.id,
			'nome': e.nome or '',
			'uso_count': e.uso_count or 0,
		}
		for e in queryset
	]
	return JsonResponse({'sucesso': True, 'resultados': resultados})


@require_GET
def buscar_pacientes_sugestoes(request):
	"""Retorna pacientes para autocomplete e reaproveitamento de cadastro."""
	import sys
	from django.db.models import Q
	from .models import Paciente
	print("[DEBUG] buscar_pacientes_sugestoes chamada", file=sys.stderr)
	try:
		termo = (request.GET.get('q') or '').strip()
		print(f"[DEBUG] termo recebido: '{termo}'", file=sys.stderr)
		if len(termo) < 2:
			print("[DEBUG] termo muito curto", file=sys.stderr)
			return JsonResponse({'sucesso': True, 'resultados': []})

		queryset = (
			Paciente.objects.only(
				'id', 'nome', 'ddd', 'telefone', 'cartao_sis', 'idade', 'peso',
				'referencia', 'rua', 'numero', 'bairro', 'estado', 'cidade', 'cep',
				'oxigenio', 'oxigenio_litros_min', 'maca', 'cadeirante',
				'evolucao', 'observacoes'
			)
			.annotate(
				uso_count=models.Count('transportes'),
				ultima_data=models.Max('transportes__data_transporte')
			)
			.filter(
				Q(nome__icontains=termo) |
				Q(telefone__icontains=termo) |
				Q(cartao_sis__icontains=termo)
			)
			.order_by('-uso_count', '-ultima_data', '-id')[:10]
		)
		print(f"[DEBUG] queryset count: {queryset.count()}", file=sys.stderr)
		resultados = []
		for p in queryset:
			resultados.append({
				'id': p.id,
				'debug_id': str(p.id),  # Para debug visual no front
				'nome': p.nome or '',
				'ddd': p.ddd or '',
				'telefone': p.telefone or '',
				'cartao_sis': p.cartao_sis or '',
				# 'acompanhante' removido pois não existe no modelo em produção
			})
		print(f"[DEBUG] resultados gerados: {len(resultados)}", file=sys.stderr)
		return JsonResponse({'sucesso': True, 'resultados': resultados})
	except Exception as exc:
		import traceback
		print(f"[ERRO buscar_pacientes_sugestoes] {exc}", file=sys.stderr)
		traceback.print_exc()
		return JsonResponse({'sucesso': False, 'erro': str(exc), 'traceback': traceback.format_exc()}, status=500)


def obter_dados_clinica(request, clinica_id):
	"""API que retorna dados da clÃ­nica em JSON para prÃ©-preencher endereÃ§o"""
	from django.http import JsonResponse
	from .models import Clinica
	try:
		clinica = Clinica.objects.only('nome', 'endereco', 'bairro', 'cidade', 'telefone').get(id=clinica_id)
		audit_logger.info(
			"Clinica consultada via API",
			extra={
				"clinica_id": clinica_id,
				"usuario": getattr(request.user, "username", "anonimo") if hasattr(request, "user") and request.user.is_authenticated else "anonimo",
			},
		)
		return JsonResponse({
			'nome': clinica.nome,
			'endereco': clinica.endereco or '',
			'bairro': clinica.bairro or '',
			'cidade': clinica.cidade or '',
			'telefone': clinica.telefone or '',
			'sucesso': True
		})
	except Clinica.DoesNotExist:
		audit_logger.warning("Clinica nao encontrada via API", extra={"clinica_id": clinica_id})
		return JsonResponse({'sucesso': False, 'erro': 'ClÃ­nica nÃ£o encontrada'}, status=404)

def cadastrar_transporte(request):
	"""Cadastra um novo transporte; aceita paciente_id via GET para pre-preencher o formulario."""
	from django.contrib import messages
	from .models import Paciente
	paciente_id = request.GET.get('paciente_id')
	from .models import Paciente
	from .models import Veiculo
	veiculos = Veiculo.objects.all().order_by('tipo_veiculo', 'patrimonio', 'placa')
	if request.method == 'POST':
		   # Garante que campos manuais prevalecem sobre selects
		   post_data = request.POST.copy()
		   # Se preenchido, zera o select correspondente para forçar o uso do manual
		   if post_data.get('veiculo_livre', '').strip():
			   post_data['veiculo'] = ''
		   if post_data.get('clinica_manual', '').strip():
			   post_data['clinica'] = ''
		   if post_data.get('condutor_manual', '').strip():
			   post_data['condutor'] = ''
		   if post_data.get('enfermagem_manual', '').strip():
			   post_data['enfermagem'] = ''

		   form = TransporteForm(post_data)
		   if form.is_valid():
			   transporte = form.save()
			   audit_logger.info(
				   "Transporte cadastrado",
				   extra={
					   "transporte_id": transporte.id,
					   "paciente_id": transporte.paciente_id,
					   "clinica_id": transporte.clinica_id,
					   "veiculo_id": transporte.veiculo_id,
					   "usuario": getattr(request.user, "username", "anonimo") if hasattr(request, "user") and request.user.is_authenticated else "anonimo",
				   },
			   )
			   # Mensagem detalhada de sucesso
			   msg_sucesso = 'Todos os dados foram salvos com sucesso!'
			   detalhes = []
			   if hasattr(form, 'novo_veiculo_cadastrado') and form.novo_veiculo_cadastrado:
				   detalhes.append('Veículo cadastrado')
			   elif hasattr(form, 'veiculo_ja_existia') and form.veiculo_ja_existia:
				   detalhes.append('Veículo já existia e foi selecionado')
			   if hasattr(form, 'alerta_oxigenio_ambulancia') and form.alerta_oxigenio_ambulancia:
				   detalhes.append('Atenção: paciente usuário de O2 deve ser alocado preferencialmente em ambulância. O transporte foi salvo mesmo assim.')
			   if form.cleaned_data.get('condutor_manual'):
				   detalhes.append('Condutor salvo')
			   if form.cleaned_data.get('clinica_manual'):
				   detalhes.append('Clínica salva')
			   if form.cleaned_data.get('enfermagem_manual'):
				   detalhes.append('Enfermagem salva')
			   if detalhes:
				   msg_sucesso += ' [' + '; '.join(detalhes) + ']'
			   messages.success(request, msg_sucesso)
			   # Após salvar, exibe mensagem e mantém usuário na tela de cadastro
			   form = TransporteForm()  # Limpa o formulário
			   breadcrumbs = [
				   {'label': 'Início', 'url': '/'},
				   {'label': 'Transportes', 'url': '/transportes/'},
				   {'label': 'Cadastrar Transporte', 'url': ''},
			   ]
			   return render(request, 'transporte_pacientes/cadastrar_transporte.html', {'form': form, 'veiculos': veiculos, 'breadcrumbs': breadcrumbs})
		   audit_logger.warning("Falha de validacao ao cadastrar transporte", extra={"erros": form.errors.as_json()})
		   first_error = '; '.join([f"{k}: {', '.join(v)}" for k, v in form.errors.items()])
		   if first_error:
			   messages.error(request, f'Nao foi possivel cadastrar transporte. {first_error}')
		   else:
			   messages.error(request, 'Nao foi possivel cadastrar transporte. Verifique os campos obrigatorios.')
	else:
		# GET: preencher paciente se vier na URL
		if paciente_id:
			try:
				paciente_obj = Paciente.objects.get(id=paciente_id)
				form = TransporteForm(initial={'paciente': paciente_id})
				form.fields['paciente'].queryset = Paciente.objects.filter(id=paciente_id)
			except Paciente.DoesNotExist:
				form = TransporteForm()
		else:
			form = TransporteForm()
	return render(request, 'transporte_pacientes/cadastrar_transporte.html', {'form': form, 'veiculos': veiculos})

def cadastrar_transporte_lote(request):
	"""Transporta varios pacientes selecionados no mesmo veiculo/condutor/data,
	mas com clinica individual por paciente."""
	from django.contrib import messages
	from .models import Paciente, Veiculo, Clinica, Condutor, Enfermagem
	import re

	veiculos = Veiculo.objects.all().order_by('tipo_veiculo', 'patrimonio', 'placa')
	clinicas = Clinica.objects.all().order_by('nome')
	condutores = Condutor.objects.all().order_by('nome')
	enfermagens = Enfermagem.objects.all().order_by('nome')

	if request.method == 'POST':
		ids_raw = request.POST.get('paciente_ids_lote', '')
		ids_list = [int(x.strip()) for x in ids_raw.split(',') if x.strip().isdigit()]
		pacientes_lote = list(Paciente.objects.filter(id__in=ids_list))

		# Campos comuns
		veiculo_id = request.POST.get('veiculo') or None
		veiculo_livre = (request.POST.get('veiculo_livre') or '').strip()
		condutor_id = request.POST.get('condutor') or None
		condutor_manual = re.sub(r'\s+', ' ', (request.POST.get('condutor_manual') or '').strip())
		enfermagem_id = request.POST.get('enfermagem') or None
		enfermagem_manual = re.sub(r'\s+', ' ', (request.POST.get('enfermagem_manual') or '').strip())
		data_transporte = request.POST.get('data_transporte') or None
		hora_saida = request.POST.get('hora_saida') or None
		hora_chegada = request.POST.get('hora_chegada') or None
		observacoes = request.POST.get('observacoes') or ''

		# Resolver veiculo
		veiculo_obj = None
		if veiculo_id:
			try:
				veiculo_obj = Veiculo.objects.get(id=veiculo_id)
			except Veiculo.DoesNotExist:
				pass
		if not veiculo_obj and veiculo_livre:
			veiculo_obj, _ = Veiculo.objects.get_or_create(
				placa=veiculo_livre.upper(),
				defaults={'tipo_veiculo': 'outros', 'placa': veiculo_livre.upper()}
			)

		# Resolver condutor
		condutor_obj = None
		if condutor_id:
			try:
				condutor_obj = Condutor.objects.get(id=condutor_id)
			except Condutor.DoesNotExist:
				pass
		if not condutor_obj and condutor_manual:
			condutor_obj, _ = Condutor.objects.get_or_create(nome__iexact=condutor_manual, defaults={'nome': condutor_manual})

		# Resolver enfermagem
		enfermagem_obj = None
		if enfermagem_id:
			try:
				enfermagem_obj = Enfermagem.objects.get(id=enfermagem_id)
			except Enfermagem.DoesNotExist:
				pass
		if not enfermagem_obj and enfermagem_manual:
			enfermagem_obj, _ = Enfermagem.objects.get_or_create(nome__iexact=enfermagem_manual, defaults={'nome': enfermagem_manual})

		erros = []
		salvos = 0
		for idx, pac in enumerate(pacientes_lote):
			# Clínica individual por paciente
			clinica_id = request.POST.get(f'clinica_{idx}') or None
			clinica_manual_txt = re.sub(r'\s+', ' ', (request.POST.get(f'clinica_manual_{idx}') or '').strip())
			clinica_obj = None
			if clinica_id:
				try:
					clinica_obj = Clinica.objects.get(id=clinica_id)
				except Clinica.DoesNotExist:
					pass
			if not clinica_obj and clinica_manual_txt:
				clinica_obj, _ = Clinica.objects.get_or_create(nome__iexact=clinica_manual_txt, defaults={'nome': clinica_manual_txt})

			if not data_transporte:
				erros.append(f"{pac.nome}: data do transporte obrigatória.")
				continue

			try:
				from .models import Transporte
				t = Transporte(
					paciente=pac,
					veiculo=veiculo_obj,
					condutor=condutor_obj,
					enfermagem=enfermagem_obj,
					clinica=clinica_obj,
					data_transporte=data_transporte,
					hora_saida=hora_saida or None,
					hora_chegada=hora_chegada or None,
					observacoes=observacoes,
				)
				t.full_clean(exclude=['hora_saida', 'hora_chegada'])
				t.save()
				salvos += 1
				audit_logger.info("Transporte lote cadastrado", extra={"transporte_id": t.id, "paciente_id": pac.id})
			except Exception as e:
				   print(f"[ERRO TRANSPORTE LOTE] Paciente: {pac.nome} | Erro: {e}")
				   erros.append(f"{pac.nome}: {e}")

		if salvos:
			messages.success(request, f'{salvos} transporte(s) cadastrado(s) com sucesso!')
		for e in erros:
			messages.error(request, f'Erro: {e}')
		return redirect('transporte_pacientes:listar_transportes')

	# GET
	ids_param = request.GET.get('paciente_ids', '')
	ids_list = [int(x.strip()) for x in ids_param.split(',') if x.strip().isdigit()]
	pacientes_selecionados = list(Paciente.objects.filter(id__in=ids_list))
	if not pacientes_selecionados:
		messages.warning(request, 'Nenhum paciente selecionado.')
		return redirect('transporte_pacientes:home')

	breadcrumbs = [
		{'label': 'Início', 'url': '/'},
		{'label': 'Transportes', 'url': '/transportes/'},
		{'label': 'Transporte em Lote', 'url': ''},
	]
	return render(request, 'transporte_pacientes/cadastrar_transporte_lote.html', {
		'pacientes': pacientes_selecionados,
		'paciente_ids_lote': ids_param,
		'veiculos': veiculos,
		'clinicas': clinicas,
		'condutores': condutores,
		'enfermagens': enfermagens,
		'today': __import__('datetime').date.today(),
		'acompanhantes_count': sum(getattr(p, 'acompanhantes', 0) for p in pacientes_selecionados),
		'breadcrumbs': breadcrumbs,
	})

def listar_transportes(request):
	"""Lista todos os transportes ordenados por data e hora de saida."""
	from .models import Paciente, Clinica, Condutor, Veiculo
	qs = Transporte.objects.select_related('paciente', 'veiculo', 'condutor', 'clinica', 'enfermagem').order_by('-data_transporte', '-hora_saida')

	paciente_id = request.GET.get('paciente')
	clinica_id = request.GET.get('clinica')
	data_transporte = request.GET.get('data_transporte')
	condutor_id = request.GET.get('condutor')
	veiculo_id = request.GET.get('veiculo')

	if paciente_id:
		qs = qs.filter(paciente_id=paciente_id)
	if clinica_id:
		qs = qs.filter(clinica_id=clinica_id)
	if data_transporte:
		qs = qs.filter(data_transporte=data_transporte)
	if condutor_id:
		qs = qs.filter(condutor_id=condutor_id)
	if veiculo_id:
		qs = qs.filter(veiculo_id=veiculo_id)

	# Para selects de filtro
	pacientes = Paciente.objects.all().order_by('nome')
	clinicas = Clinica.objects.all().order_by('nome')
	condutores = Condutor.objects.all().order_by('nome')
	veiculos = Veiculo.objects.all().order_by('patrimonio', 'placa')

	breadcrumbs = [
		{'label': 'Início', 'url': '/'},
		{'label': 'Transportes', 'url': ''},
	]
	context = {
		'transportes': qs,
		'breadcrumbs': breadcrumbs,
		'pacientes': pacientes,
		'clinicas': clinicas,
		'condutores': condutores,
		'veiculos': veiculos,
		'filtros': {
			'paciente': paciente_id or '',
			'clinica': clinica_id or '',
			'data_transporte': data_transporte or '',
			'condutor': condutor_id or '',
			'veiculo': veiculo_id or '',
		}
	}
	return render(request, 'transporte_pacientes/listar_transportes.html', context)
def excluir_selecionadas_enfermagem(request):
	"""Exclui os membros de enfermagem marcados via checkbox na listagem."""
	from .models import Enfermagem
	from django.contrib import messages
	if request.method == 'POST':
		ids = request.POST.getlist('enfermagem_ids')
		if ids:
			Enfermagem.objects.filter(id__in=ids).delete()
			messages.success(request, f'{len(ids)} enfermagem(ns) selecionada(s) foram excluÃ­das.')
		else:
			messages.warning(request, 'Nenhuma enfermagem selecionada para exclusÃ£o.')
	return redirect('transporte_pacientes:cadastrar_enfermagem')
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404

def excluir_enfermagem(request, enfermagem_id):
	"""Exclui um membro de enfermagem por ID."""
	from .models import Enfermagem
	if request.method == 'POST':
		enfermagem = get_object_or_404(Enfermagem, id=enfermagem_id)
		enfermagem.delete()
		messages.success(request, 'Enfermagem excluÃ­da com sucesso!')
	return redirect('transporte_pacientes:cadastrar_enfermagem')
from .forms import EnfermagemForm

def cadastrar_enfermagem(request):
	"""Cadastra membro de enfermagem e exibe a lista completa."""
	from .models import Enfermagem
	if request.method == 'POST':
		form = EnfermagemForm(request.POST)
		if form.is_valid():
			form.save()
			from django.contrib import messages
			messages.success(request, 'Enfermagem cadastrada com sucesso!')
			return redirect('transporte_pacientes:cadastrar_enfermagem')
		first_error = '; '.join([f"{k}: {', '.join(v)}" for k, v in form.errors.items()])
		messages.error(request, f'Nao foi possivel cadastrar enfermagem. {first_error}')
	else:
		form = EnfermagemForm()
	enfermagens = Enfermagem.objects.all().order_by('-id')
	breadcrumbs = [
		{'label': 'Início', 'url': '/'},
		{'label': 'Enfermagem', 'url': '/enfermagem/'},
		{'label': 'Cadastrar Enfermagem', 'url': ''},
	]
	return render(request, 'transporte_pacientes/cadastrar_enfermagem.html', {
		'form': form,
		'enfermagens': enfermagens,
		'breadcrumbs': breadcrumbs,
	})
def excluir_selecionadas_clinicas(request):
	"""Exclui as clinicas marcadas via checkbox na listagem."""
	from .models import Clinica
	from django.contrib import messages
	if request.method == 'POST':
		ids = request.POST.getlist('clinicas_ids')
		if ids:
			Clinica.objects.filter(id__in=ids).delete()
			messages.success(request, f'{len(ids)} clÃ­nica(s) selecionada(s) foram excluÃ­das.')
		else:
			messages.warning(request, 'Nenhuma clÃ­nica selecionada para exclusÃ£o.')
	return redirect('transporte_pacientes:cadastrar_clinica')
def excluir_todas_clinicas(request):
	"""Exclui todas as clinicas do banco de dados (operacao irreversivel)."""
	from .models import Clinica
	from django.contrib import messages
	if request.method == 'POST':
		total = Clinica.objects.count()
		Clinica.objects.all().delete()
		messages.success(request, f'Todas as {total} clÃ­nicas foram excluÃ­das.')
	return redirect('transporte_pacientes:cadastrar_clinica')
from django.shortcuts import redirect, get_object_or_404
def excluir_clinica(request, clinica_id):
	"""Exclui uma clinica especifica por ID."""
	from .models import Clinica
	from django.contrib import messages
	if request.method == 'POST':
		clinica = get_object_or_404(Clinica, id=clinica_id)
		clinica.delete()
		messages.success(request, 'ClÃ­nica excluÃ­da com sucesso!')
	return redirect('transporte_pacientes:cadastrar_clinica')
from django.http import JsonResponse
import json

def corrigir_dados_clinica(request):
	from .models import Clinica
	from .forms import ClinicaForm
	from django.contrib import messages
	from django.shortcuts import render, redirect, get_object_or_404
	from django.http import JsonResponse
	import json

	if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
		# API AJAX para correção de campo
		try:
			data = json.loads(request.body.decode('utf-8'))
			campo = data.get('campo')
			valor = data.get('valor')
			valor_corrigido = valor
			erro = None
			if campo == 'telefone':
				valor_corrigido = ''.join(filter(str.isdigit, str(valor)))
			elif campo in ['nome', 'endereco', 'bairro', 'cidade']:
				valor_corrigido = str(valor).strip()
			if erro:
				return JsonResponse({'sucesso': False, 'erro': erro})
			return JsonResponse({'sucesso': True, 'valor_corrigido': valor_corrigido})
		except Exception as e:
			return JsonResponse({'sucesso': False, 'erro': str(e)})
	elif request.method == 'POST':
		# Edição de clínica via formulário
		clinica_id = request.GET.get('id')
		clinica = get_object_or_404(Clinica, id=clinica_id)
		form = ClinicaForm(request.POST, instance=clinica)
		if form.is_valid():
			form.save()
			messages.success(request, 'Clínica atualizada com sucesso!')
			return redirect('transporte_pacientes:cadastrar_clinica')
		clinicas = Clinica.objects.all().order_by('-id')
		return render(request, 'transporte_pacientes/cadastrar_clinica.html', {'form': form, 'clinicas': clinicas, 'editar': True, 'clinica_editando': clinica})
	else:
		# GET: exibe formulário de edição
		clinica_id = request.GET.get('id')
		if not clinica_id:
			messages.error(request, 'ID da clínica não informado.')
			return redirect('transporte_pacientes:cadastrar_clinica')
		clinica = get_object_or_404(Clinica, id=clinica_id)
		form = ClinicaForm(instance=clinica)
		clinicas = Clinica.objects.all().order_by('-id')
		return render(request, 'transporte_pacientes/cadastrar_clinica.html', {'form': form, 'clinicas': clinicas, 'editar': True, 'clinica_editando': clinica})
from django.contrib import messages

def excluir_todos_pacientes(request):
	"""Exclui todos os pacientes do banco de dados (operacao irreversivel)."""
	from .models import Paciente
	total = Paciente.objects.count()
	Paciente.objects.all().delete()
	messages.success(request, f"Todos os {total} pacientes foram excluÃ­dos.")
	return redirect('transporte_pacientes:cadastrar_paciente')
from django.contrib import messages

def corrigir_dados_pacientes(request):
	"""API AJAX para corrigir/normalizar um campo de paciente individualmente."""
	from django.http import JsonResponse
	import json
	from .models import Paciente
	if request.method == 'POST':
		try:
			data = json.loads(request.body.decode('utf-8'))
			campo = data.get('campo')
			valor = data.get('valor')
			valor_corrigido = valor
			erro = None
			# Corrigir individualmente
			if campo == 'peso':
				try:
					valor_corrigido = float(str(valor).replace(',', '.'))
					if valor_corrigido <= 0:
						valor_corrigido = ''
				except Exception:
					erro = 'Valor invÃ¡lido para peso.'
			elif campo == 'idade':
				try:
					valor_corrigido = abs(int(valor))
				except Exception:
					erro = 'Valor invÃ¡lido para idade.'
			elif campo == 'telefone':
				valor_corrigido = ''.join(filter(str.isdigit, str(valor)))
			elif campo == 'status':
				valor_corrigido = str(valor).strip().lower()
			# Adicione outros campos conforme necessÃ¡rio
			if erro:
				return JsonResponse({'sucesso': False, 'erro': erro})
			return JsonResponse({'sucesso': True, 'valor_corrigido': valor_corrigido})
		except Exception as e:
			return JsonResponse({'sucesso': False, 'erro': str(e)})
	else:
		messages.success(request, "CorreÃ§Ãµes aplicadas nos dados dos pacientes.")
		referer = request.META.get('HTTP_REFERER')
		if referer:
			return redirect(referer)
		else:
			return redirect('transporte_pacientes:cadastrar_paciente')
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

def excluir_paciente_ajax(request):
	"""Exclui um ou mais pacientes via requisicao AJAX (POST com lista de IDs)."""
	if request.method == 'POST':
		from .models import Paciente
		ids = request.POST.getlist('id')
		if not ids:
			return JsonResponse({'success': False, 'error': 'Nenhum id recebido.'}, status=400)
		Paciente.objects.filter(id__in=ids).delete()
		return JsonResponse({'success': True})
	return JsonResponse({'success': False}, status=400)
def buscar_editar_paciente(request):
	"""Busca pacientes por nome ou telefone (parametro 'q') e exibe lista editavel."""
	from .models import Paciente
	from django.db.models import Q
	q = request.GET.get('q', '')
	pacientes = Paciente.objects.all()
	if q:
		pacientes = pacientes.filter(Q(nome__icontains=q) | Q(telefone__icontains=q)).distinct()
	return render(request, 'transporte_pacientes/buscar_editar_paciente.html', {'pacientes': pacientes})
from django.shortcuts import get_object_or_404
def editar_paciente(request, pk):
	"""Exibe e processa o formulario de edicao de paciente."""
	from .models import Paciente
	paciente = get_object_or_404(Paciente, pk=pk)
	if request.method == 'POST':
		form = PacienteForm(request.POST, instance=paciente)
		if form.is_valid():
			form.save()
			return redirect('transporte_pacientes:cadastrar_paciente')
	else:
		form = PacienteForm(instance=paciente)
	return render(request, 'transporte_pacientes/editar_paciente.html', {'form': form, 'paciente': paciente})
from django.http import JsonResponse
import pandas as pd
import unicodedata
import logging

# ── Cache em memória: carregado uma única vez no primeiro request ────────────
_AUTOCOMPLETE_DF = None          # DataFrame unificado
_AUTOCOMPLETE_NOMES_NORM = None  # Série de nomes normalizados (evita recalcular)

# Mapa dos códigos IBGE → nome do município (Grande SP)
_COD_MUNICIPIO = {
    '355030': 'São Paulo', '350950': 'Arujá', '350280': 'Barueri',
    '350570': 'Biritiba Mirim', '350760': 'Cajamar', '351060': 'Carapicuíba',
    '351880': 'Guarulhos', '352500': 'Diadema', '351500': 'Embu das Artes',
    '351510': 'Embu-Guaçu', '351570': 'Ferraz de Vasconcelos',
    '351630': 'Francisco Morato', '351640': 'Franco da Rocha',
    '352250': 'Itapecerica da Serra', '352310': 'Itapevi',
    '352340': 'Itaquaquecetuba', '352590': 'Juquitiba',
    '352940': 'Mauá', '353060': 'Mogi das Cruzes', '353440': 'Osasco',
    '353910': 'Poá', '354330': 'Ribeirão Pires', '354340': 'Rio Grande da Serra',
    '354780': 'Santa Isabel', '354870': 'Santana de Parnaíba',
    '354880': 'Santo André', '354890': 'São Bernardo do Campo',
    '354910': 'São Caetano do Sul', '355220': 'Suzano',
    '355645': 'Taboão da Serra', '355715': 'Vargem Grande Paulista',
}

def _normalize(s):
    return unicodedata.normalize('NFKD', str(s)).encode('ASCII', 'ignore').decode('ASCII').lower()

def _load_autocomplete_df():
    """Lê todos os CSVs uma única vez e retorna DataFrame unificado."""
    base_dir = Path(__file__).resolve().parent.parent
    frames = []

    # 1) CSV do CNES (431 hospitais da Grande SP)
    cnes_path = base_dir / 'polls' / 'data' / 'hospitais_sp_cnes.csv'
    if cnes_path.exists():
        try:
            df_cnes = pd.read_csv(cnes_path, dtype=str).fillna('')
            # Mapeia cod_municipio → nome do município
            df_cnes['municipio'] = df_cnes['cod_municipio'].map(_COD_MUNICIPIO).fillna('Grande SP')
            # Normaliza nomes para maiúsculas com título (melhor exibição)
            df_cnes['nome'] = df_cnes['nome'].str.title()
            # Seleciona apenas colunas necessárias
            df_cnes = df_cnes[['nome', 'logradouro', 'numero', 'bairro', 'municipio', 'cep']]
            frames.append(df_cnes)
            logging.info(f"[AUTOCOMPLETE] CNES carregado: {len(df_cnes)} registros")
        except Exception as e:
            logging.warning(f"[AUTOCOMPLETE] Falha ao ler CNES: {e}")

    # 2) CSVs manuais de referência
    for fname in ['enderecos_sp_hospitais_referencia_corrigido.csv', 'enderecos_sp_hospitais_adicionais.csv']:
        p = base_dir / fname
        if p.exists():
            try:
                df_extra = pd.read_csv(p, dtype=str).fillna('')
                if 'municipio' not in df_extra.columns:
                    df_extra['municipio'] = ''
                df_extra = df_extra[['nome', 'logradouro', 'numero', 'bairro', 'municipio', 'cep']]
                frames.append(df_extra)
                logging.info(f"[AUTOCOMPLETE] {fname} carregado: {len(df_extra)} registros")
            except Exception as e:
                logging.warning(f"[AUTOCOMPLETE] Falha ao ler {fname}: {e}")

    if not frames:
        return None, None

    df = pd.concat(frames, ignore_index=True).drop_duplicates(subset=['nome', 'cep'])
    nomes_norm = df['nome'].apply(_normalize)
    return df, nomes_norm


# Autocomplete AJAX para endereço de unidade de saúde
def autocomplete_endereco_unidade(request):
    global _AUTOCOMPLETE_DF, _AUTOCOMPLETE_NOMES_NORM
    try:
        from rapidfuzz import process, fuzz
    except ImportError:
        process = None
        fuzz = None

    # Carrega o cache na primeira chamada
    if _AUTOCOMPLETE_DF is None:
        _AUTOCOMPLETE_DF, _AUTOCOMPLETE_NOMES_NORM = _load_autocomplete_df()

    term = _normalize(request.GET.get('term', ''))
    show_all = request.GET.get('show_all', 'false').lower() in ('true', '1', 'yes', 'on')
    max_results = None if show_all else 10  # None = sem limite (todas), 10 = padrão
    resultados = []

    try:
        # Se não há DataFrames e precisa mostrar tudo, tenta BD
        if _AUTOCOMPLETE_DF is None:
            from .models import Clinica
            clinicas = Clinica.objects.all() if show_all else Clinica.objects.filter(nome__icontains=request.GET.get('term', '').strip())
            clinicas = clinicas.order_by('nome')
            if max_results:
                clinicas = clinicas[:max_results]
            return JsonResponse([{
                'label': c.nome, 'value': c.endereco or '',
                'logradouro': c.endereco or '', 'numero': '', 'cep': '',
            } for c in clinicas], safe=False)

        df = _AUTOCOMPLETE_DF
        nomes_norm = _AUTOCOMPLETE_NOMES_NORM

        # Se term vazio e show_all=true, retorna TODAS
        if term == '' and show_all:
            encontrados = df
        # Se term vazio e show_all=false, retorna vazio
        elif term == '':
            encontrados = pd.DataFrame()
        # Caso contrário, busca por substring
        else:
            mask = nomes_norm.str.contains(term, regex=False)
            encontrados = df[mask]

        # Limita resultado se necessário
        if max_results:
            encontrados = encontrados.head(max_results)

        indices_usados = set(encontrados.index.tolist())

        def row_to_dict(row):
            endereco = f"{row['logradouro']}, {row['numero']}, {row['bairro']}, {row['municipio']}, {row['cep']}"
            cidade = row['municipio']
            label = f"{row['nome']} — {cidade}" if cidade else row['nome']
            return {
                'label': label,
                'value': endereco.strip(', '),
                'logradouro': row['logradouro'],
                'numero': row['numero'],
                'cep': row['cep'],
            }

        for _, row in encontrados.iterrows():
            resultados.append(row_to_dict(row))

        # Fuzzy apenas se poucos resultados diretos E não estiver mostrando tudo
        if not show_all and len(resultados) < 5 and process and fuzz:
            fuzzy_matches = process.extract(term, nomes_norm.tolist(), scorer=fuzz.WRatio, limit=15)
            for _, score, idx in fuzzy_matches:
                if score > 65 and idx not in indices_usados and len(resultados) < 10:
                    resultados.append(row_to_dict(df.iloc[idx]))
                    indices_usados.add(idx)

        # Remove duplicados mantendo ordem
        seen = set()
        resultados_unicos = [r for r in resultados if r['label'] not in seen and not seen.add(r['label'])]

        return JsonResponse(resultados_unicos, safe=False)

    except Exception as e:
        logging.error(f"[AUTOCOMPLETE] Erro: {e}")
        return JsonResponse({'error': str(e)}, status=500)

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.utils import timezone
from .models import Veiculo, Condutor, Clinica, Paciente
from .excel_utils import exportar_excel_profissional
import tempfile
from .forms import PacienteForm, VeiculoForm, CondutorForm, ClinicaForm
from django.http import HttpResponse, JsonResponse


# View de login personalizada
def login_view(request):
	if request.user.is_authenticated:
		return redirect('transporte_pacientes:home')
	if request.method == 'POST':
		username = request.POST.get('username')
		password = request.POST.get('password')
		user = authenticate(request, username=username, password=password)
		if user is not None:
			login(request, user)
			return redirect('transporte_pacientes:home')
		else:
			messages.error(request, 'Usuário ou senha inválidos.')
	year = timezone.now().year
	return render(request, 'registration/login.html', {'year': year})

@login_required
def home(request):
	"""Pagina inicial do app exibindo as unidades de saude cadastradas."""
	unidades_salvas = Clinica.objects.all()
	return render(request, 'polls/home.html', {'unidades_salvas': unidades_salvas})

def exportar_veiculos_excel(request):
	from .models import Veiculo
	campos = ["tipo_veiculo", "placa", "patrimonio"]
	queryset = Veiculo.objects.all()
	import tempfile
	with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
		exportar_excel_profissional(queryset, campos, tmp.name)
		tmp.seek(0)
		response = HttpResponse(tmp.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
		response['Content-Disposition'] = 'attachment; filename="veiculos.xlsx"'
		return response

def exportar_condutores_excel(request):
	from .models import Condutor
	campos = ["nome"]
	queryset = Condutor.objects.all()
	import tempfile
	with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
		exportar_excel_profissional(queryset, campos, tmp.name)
		tmp.seek(0)
		response = HttpResponse(tmp.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
		response['Content-Disposition'] = 'attachment; filename="condutores.xlsx"'
		return response

def exportar_clinicas_excel(request):
	from .models import Clinica
	campos = ["nome", "endereco", "bairro", "cidade", "telefone"]
	queryset = Clinica.objects.all()
	import tempfile
	with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
		exportar_excel_profissional(queryset, campos, tmp.name)
		tmp.seek(0)
		response = HttpResponse(tmp.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
		response['Content-Disposition'] = 'attachment; filename="clinicas.xlsx"'
		return response

def exportar_pacientes_excel(request):
	from .models import Paciente
	import pandas as pd
	enderecos_path = Path(__file__).resolve().parent.parent / 'enderecos_sp.csv'
	enderecos_dict = {}
	if enderecos_path.exists():
		enderecos_df = pd.read_csv(enderecos_path)
		enderecos_dict = {row['nome']: row for _, row in enderecos_df.iterrows()}

	campos = ["nome", "idade", "peso", "endereco", "referencia", "telefone", "tratamento", "oxigenio", "oxigenio_litros_min", "observacoes", "evolucao", "status", "destino_nome", "destino_endereco_completo"]
	pacientes = []
	for obj in Paciente.objects.all():
		destino_nome = getattr(obj, 'referencia', '')  # Supondo que o campo referencia seja o nome do destino
		endereco_info = enderecos_dict.get(destino_nome, {})
		endereco_completo = ""
		if endereco_info:
			endereco_completo = f"{endereco_info.get('logradouro','')} {endereco_info.get('numero','')}, {endereco_info.get('bairro','')}, {endereco_info.get('municipio','')} - CEP {endereco_info.get('cep','')}"
		pacientes.append([
			obj.nome, obj.idade, obj.peso, obj.endereco, obj.referencia, obj.telefone, obj.tratamento, obj.oxigenio, obj.oxigenio_litros_min, obj.observacoes, obj.evolucao, obj.status,
			destino_nome, endereco_completo
		])

	# FunÃ§Ã£o de exportaÃ§Ã£o adaptada para lista de listas
	from openpyxl import Workbook
	from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
	from datetime import date
	wb = Workbook()
	ws = wb.active
	ws.title = "Pacientes"
	header_font = Font(bold=True, color="FFFFFF")
	header_fill = PatternFill("solid", fgColor="1976D2")
	important_fill = PatternFill("solid", fgColor="FFEB3B")
	normal_fill = PatternFill("solid", fgColor="E3F2FD")
	border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
	align = Alignment(horizontal="center", vertical="center")
	ws.append(campos)
	for col, _ in enumerate(campos, 1):
		cell = ws.cell(row=1, column=col)
		cell.font = header_font
		cell.fill = header_fill
		cell.alignment = align
		cell.border = border
	for row in pacientes:
		ws.append(row)
		for col, valor in enumerate(row, 1):
			cell = ws.cell(row=ws.max_row, column=col)
			if campos[col-1].lower() in ["nome", "status", "patrimonio", "destino_nome"]:
				cell.fill = important_fill
			else:
				cell.fill = normal_fill
			cell.alignment = align
			cell.border = border
	ws.append([""] * len(campos))
	ws.append([f"Planilha gerada em: {date.today().strftime('%d/%m/%Y')}"] + [""] * (len(campos)-1))
	for col in ws.columns:
		max_length = 0
		col_letter = col[0].column_letter
		for cell in col:
			try:
				if len(str(cell.value)) > max_length:
					max_length = len(str(cell.value))
			except:
				pass
		ws.column_dimensions[col_letter].width = max_length + 2
	ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
	ws.page_setup.paperSize = ws.PAPERSIZE_A4
	ws.page_margins.left = 0.5
	ws.page_margins.right = 0.5
	ws.page_margins.top = 0.5
	ws.page_margins.bottom = 0.5
	import tempfile
	with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
		wb.save(tmp.name)
		tmp.seek(0)
		response = HttpResponse(tmp.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
		response['Content-Disposition'] = 'attachment; filename="pacientes.xlsx"'
		return response

def preview_pacientes(request):
	from .models import Paciente
	import pandas as pd
	enderecos_path = Path(__file__).resolve().parent.parent / 'enderecos_sp.csv'
	enderecos_dict = {}
	if enderecos_path.exists():
		enderecos_df = pd.read_csv(enderecos_path)
		enderecos_dict = {row['nome']: row for _, row in enderecos_df.iterrows()}
	campos = ["nome", "idade", "peso", "endereco", "referencia", "telefone", "tratamento", "oxigenio", "oxigenio_litros_min", "observacoes", "evolucao", "status", "destino_nome", "destino_endereco_completo"]
	pacientes = []
	for obj in Paciente.objects.all():
		destino_nome = getattr(obj, 'referencia', '')
		endereco_info = enderecos_dict.get(destino_nome, {})
		endereco_completo = ""
		if endereco_info:
			endereco_completo = f"{endereco_info.get('logradouro','')} {endereco_info.get('numero','')}, {endereco_info.get('bairro','')}, {endereco_info.get('municipio','')} - CEP {endereco_info.get('cep','')}"
		pacientes.append([
			obj.nome, obj.idade, obj.peso, obj.endereco, obj.referencia, obj.telefone, obj.tratamento, obj.oxigenio, obj.oxigenio_litros_min, obj.observacoes, obj.evolucao, obj.status,
			destino_nome, endereco_completo
		])
	return render(request, 'polls/preview_pacientes.html', {'campos': campos, 'pacientes': pacientes})


def _obter_pastas_dados_recebidos():
	"""Retorna e garante a estrutura de pastas para arquivos recebidos."""
	base_dir = Path(getattr(settings, 'DADOS_RECEBIDOS_DIR', Path(__file__).resolve().parent.parent / 'dados_recebidos'))
	pastas = {
		'base': base_dir,
		'entrada': base_dir / 'entrada',
		'processados': base_dir / 'processados',
		'arquivados': base_dir / 'arquivados',
		'rejeitados': base_dir / 'rejeitados',
	}
	for pasta in pastas.values():
		pasta.mkdir(parents=True, exist_ok=True)
	return pastas


def _ler_dataframe_importacao_pacientes(arquivo, nome_arquivo=None):
	"""Lê CSV/XLS/XLSX e retorna DataFrame para pré-importação de pacientes."""
	import pandas as pd

	nome_arquivo = nome_arquivo or getattr(arquivo, 'name', '')
	extensao = Path(nome_arquivo).suffix.lower()
	if extensao == '.csv':
		return pd.read_csv(arquivo)
	if extensao in ('.xls', '.xlsx'):
		return pd.read_excel(arquivo)
	raise ValueError('Formato de arquivo não suportado. Use CSV ou Excel.')


def _construir_formulario_importacao_paciente(df):
	"""Monta o formulário de revisão a partir da primeira linha do arquivo importado."""
	import pandas as pd
	from .models import Paciente
	from .forms import PacienteForm

	if df.empty:
		raise ValueError('O arquivo está vazio.')

	campos_modelo = [f.name for f in Paciente._meta.fields]
	row = df.iloc[0]
	dados = {campo: row[campo] for campo in campos_modelo if campo in row and pd.notnull(row[campo])}
	dados.pop('id', None)
	return PacienteForm(initial=dados)


def _render_revisao_importacao_paciente(request, form_web, arquivo_origem_nome='', arquivo_origem_tipo=''):
	"""Renderiza a tela padrão de pacientes com a área de revisão aberta."""
	from .models import Paciente
	from .forms import PacienteForm

	return render(request, 'transporte_pacientes/cadastrar_paciente.html', {
		'form': PacienteForm(),
		'form_web': form_web,
		'importado_via_web': True,
		'pacientes': Paciente.objects.all(),
		'arquivo_origem_nome': arquivo_origem_nome,
		'arquivo_origem_tipo': arquivo_origem_tipo,
	})


def _mover_arquivo_recebido(nome_arquivo, destino):
	"""Move arquivo da pasta de entrada para o destino informado, evitando sobrescrita."""
	pastas = _obter_pastas_dados_recebidos()
	entrada_dir = pastas['entrada'].resolve()
	origem = (entrada_dir / nome_arquivo).resolve()
	try:
		origem.relative_to(entrada_dir)
	except ValueError as exc:
		raise ValueError('Nome de arquivo inválido.') from exc

	if not origem.exists():
		raise FileNotFoundError(f'Arquivo não encontrado: {nome_arquivo}')

	destino_dir = pastas[destino]
	destino_path = destino_dir / origem.name
	if destino_path.exists():
		destino_path = destino_dir / f"{origem.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{origem.suffix}"

	shutil.move(str(origem), str(destino_path))
	return destino_path


def arquivos_recebidos_pacientes(request):
	"""Lista arquivos CSV/Excel recebidos e permite iniciar a importação com um clique."""
	from django.contrib import messages

	pastas = _obter_pastas_dados_recebidos()
	entrada_dir = pastas['entrada']
	permitidos = {'.csv', '.xls', '.xlsx'}

	if request.method == 'POST':
		nome_arquivo = (request.POST.get('arquivo_nome') or '').strip()
		if not nome_arquivo:
			messages.warning(request, 'Selecione um arquivo válido para importar.')
			return redirect('transporte_pacientes:arquivos_recebidos_pacientes')

		arquivo_path = (entrada_dir / nome_arquivo).resolve()
		try:
			arquivo_path.relative_to(entrada_dir.resolve())
		except ValueError:
			messages.error(request, 'Arquivo informado é inválido.')
			return redirect('transporte_pacientes:arquivos_recebidos_pacientes')

		if not arquivo_path.exists() or arquivo_path.suffix.lower() not in permitidos:
			messages.error(request, 'Arquivo não encontrado ou formato não permitido.')
			return redirect('transporte_pacientes:arquivos_recebidos_pacientes')

		try:
			df = _ler_dataframe_importacao_pacientes(arquivo_path, arquivo_path.name)
			form_web = _construir_formulario_importacao_paciente(df)
			messages.info(request, f'Arquivo "{arquivo_path.name}" carregado para revisão.')
			return _render_revisao_importacao_paciente(
				request,
				form_web,
				arquivo_origem_nome=arquivo_path.name,
				arquivo_origem_tipo='dados_recebidos',
			)
		except Exception as exc:
			try:
				_mover_arquivo_recebido(arquivo_path.name, 'rejeitados')
				messages.error(request, f'Arquivo "{arquivo_path.name}" rejeitado durante a leitura: {exc}')
			except Exception:
				messages.error(request, f'Erro ao preparar o arquivo "{arquivo_path.name}": {exc}')
			return redirect('transporte_pacientes:arquivos_recebidos_pacientes')

	arquivos_recebidos = []
	for arquivo in sorted(entrada_dir.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True):
		if arquivo.is_file() and arquivo.suffix.lower() in permitidos:
			arquivos_recebidos.append({
				'nome': arquivo.name,
				'extensao': arquivo.suffix.lower().lstrip('.').upper(),
				'tamanho_kb': max(1, round(arquivo.stat().st_size / 1024)),
				'modificado_em': datetime.fromtimestamp(arquivo.stat().st_mtime),
			})

	return render(request, 'transporte_pacientes/arquivos_recebidos.html', {
		'arquivos_recebidos': arquivos_recebidos,
		'pasta_entrada': entrada_dir,
	})

def cadastrar_paciente(request):
	from .models import Paciente
	from django.contrib import messages
	from .forms import PacienteForm
	from .forms_import import PacienteImportForm
	import logging
	logger = logging.getLogger("paciente_view")
	form_web = None
	importado_via_web = False
	arquivo_origem_nome = ''
	arquivo_origem_tipo = ''
	if request.method == 'POST':
		# ImportaÃ§Ã£o de pacientes via upload
		if 'importar_pacientes' in request.POST:
			form_import = PacienteImportForm(request.POST, request.FILES)
			if form_import.is_valid():
				arquivo = request.FILES['arquivo_importacao']
				try:
					df = _ler_dataframe_importacao_pacientes(arquivo, arquivo.name)
					form_web = _construir_formulario_importacao_paciente(df)
					logger.warning("[DEBUG] Importação: exibindo revisão de dados web")
					return _render_revisao_importacao_paciente(request, form_web, arquivo_origem_tipo='upload_manual')
				except Exception as e:
					messages.error(request, f"Erro ao processar arquivo: {e}")
					return redirect('transporte_pacientes:cadastrar_paciente')
		# Salvando dados revisados do formulÃ¡rio web
		if 'salvar_web' in request.POST:
			arquivo_origem_nome = (request.POST.get('arquivo_origem_nome') or '').strip()
			arquivo_origem_tipo = (request.POST.get('arquivo_origem_tipo') or '').strip()
			form_web = PacienteForm(request.POST)
			if form_web.is_valid():
				form_web.save()
				if arquivo_origem_tipo == 'dados_recebidos' and arquivo_origem_nome:
					try:
						_mover_arquivo_recebido(arquivo_origem_nome, 'processados')
					except Exception as exc:
						messages.warning(request, f'Paciente salvo, mas não foi possível mover o arquivo recebido: {exc}')
				messages.success(request, 'Paciente importado e revisado salvo com sucesso!')
				return redirect('transporte_pacientes:cadastrar_paciente')
			else:
				return _render_revisao_importacao_paciente(request, form_web, arquivo_origem_nome, arquivo_origem_tipo)
		# ExclusÃ£o individual
		if 'excluir_id' in request.POST:
			Paciente.objects.filter(id=request.POST['excluir_id']).delete()
			messages.success(request, 'Paciente excluÃ­do com sucesso!')
			return redirect('transporte_pacientes:cadastrar_paciente')
		# ExclusÃ£o mÃºltipla
		elif 'excluir_selecionados' in request.POST:
			ids = request.POST.getlist('excluir_ids')
			if ids:
				Paciente.objects.filter(id__in=ids).delete()
				messages.success(request, f'{len(ids)} paciente(s) excluÃ­do(s) com sucesso!')
			else:
				messages.warning(request, 'Nenhum paciente selecionado para exclusÃ£o.')
			return redirect('transporte_pacientes:cadastrar_paciente')
		# Cadastro manual
		form = PacienteForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Paciente cadastrado com sucesso!')
			return redirect('transporte_pacientes:cadastrar_paciente')
		else:
			first_error = '; '.join([f"{k}: {', '.join(v)}" for k, v in form.errors.items()])
			if first_error:
				messages.error(request, f'Não foi possível cadastrar o paciente. {first_error}')
			else:
				messages.error(request, 'Não foi possível cadastrar o paciente. Verifique os campos obrigatórios.')
			logger.warning("Falha de validação ao cadastrar paciente", extra={"erros": form.errors.as_json()})
	else:
		form = PacienteForm()
	from django.db.models import Exists, OuterRef, BooleanField, Value, Case, When
	from .models import Transporte
	# Evita pacientes duplicados na listagem por nome, idade e telefone (em Python, para compatibilidade com todos os bancos)
	pacientes_qs = Paciente.objects.all().order_by('nome', 'idade', 'telefone')
	pacientes = []
	seen = set()
	for p in pacientes_qs:
		key = (p.nome, p.idade, p.telefone)
		if key not in seen:
			pacientes.append(p)
			seen.add(key)
	# Contador: total de pacientes + acompanhantes
	total_pacientes = len(pacientes)
	total_acompanhantes = sum(getattr(p, 'acompanhantes', 0) for p in pacientes)
	total_geral = total_pacientes + total_acompanhantes
	return render(request, 'transporte_pacientes/cadastrar_paciente.html', {
		'form': form,
		'form_web': form_web,
		'importado_via_web': importado_via_web,
		'pacientes': pacientes,
		'arquivo_origem_nome': arquivo_origem_nome,
		'arquivo_origem_tipo': arquivo_origem_tipo,
		'total_pacientes': total_pacientes,
		'total_acompanhantes': total_acompanhantes,
		'total_geral': total_geral,
	})

def cadastrar_veiculo(request):
	from django.contrib import messages
	sucesso = None
	from django.contrib import messages
	if request.method == 'POST':
		if 'excluir_id' in request.POST:
			Veiculo.objects.filter(id=request.POST['excluir_id']).delete()
			messages.success(request, 'VeÃ­culo excluÃ­do com sucesso!')
			return redirect('transporte_pacientes:cadastrar_veiculo')
		form = VeiculoForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'VeÃ­culo cadastrado com sucesso!')
			return redirect('transporte_pacientes:cadastrar_veiculo')
		first_error = '; '.join([f"{k}: {', '.join(v)}" for k, v in form.errors.items()])
		messages.error(request, f'Nao foi possivel cadastrar veiculo. {first_error}')
	else:
		form = VeiculoForm()
	veiculos = Veiculo.objects.all()
	return render(request, 'transporte_pacientes/cadastrar_veiculo.html', {'form': form, 'veiculos': veiculos})

def cadastrar_condutor(request):
	from django.contrib import messages
	if request.method == 'POST':
		form = CondutorForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Condutor salvo com sucesso!')
			return redirect('transporte_pacientes:cadastrar_condutor')
		first_error = '; '.join([f"{k}: {', '.join(v)}" for k, v in form.errors.items()])
		messages.error(request, f'Nao foi possivel cadastrar condutor. {first_error}')
	else:
		form = CondutorForm()
	from .models import Condutor
	condutores = Condutor.objects.all().order_by('-id')
	breadcrumbs = [
		{'label': 'Início', 'url': '/'},
		{'label': 'Condutores', 'url': '/condutores/'},
		{'label': 'Cadastrar Condutor', 'url': ''},
	]
	return render(request, 'transporte_pacientes/cadastrar_condutor.html', {
		'form': form,
		'condutores': condutores,
		'breadcrumbs': breadcrumbs,
	})

def cadastrar_clinica(request):
	from django.contrib import messages
	from .models import Clinica
	if request.method == 'POST':
		form = ClinicaForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Clinica cadastrada com sucesso!')
			return redirect('transporte_pacientes:cadastrar_clinica')
		first_error = '; '.join([f"{k}: {', '.join(v)}" for k, v in form.errors.items()])
		messages.error(request, f'Nao foi possivel cadastrar clinica. {first_error}')
	else:
		form = ClinicaForm()
	clinicas = Clinica.objects.all()
	breadcrumbs = [
		{'label': 'Início', 'url': '/'},
		{'label': 'Hospitais/Clínicas', 'url': '/clinicas/'},
		{'label': 'Cadastrar Clínica', 'url': ''},
	]
	return render(request, 'transporte_pacientes/cadastrar_clinica.html', {
		'form': form,
		'clinicas': clinicas,
		'unidades_salvas': clinicas,
		'breadcrumbs': breadcrumbs,
	})

def preview_clinicas(request):
    from .models import Clinica
    campos = ["nome", "endereco", "bairro", "cidade", "telefone"]
    clinicas = []
    for obj in Clinica.objects.all():
        clinicas.append([
            obj.nome, obj.endereco, obj.bairro, obj.cidade, obj.telefone
        ])
    return render(request, 'polls/preview_clinicas.html', {'campos': campos, 'clinicas': clinicas})

def preview_condutores(request):
    from .models import Condutor
    campos = ["nome"]
    condutores = []
    for obj in Condutor.objects.all():
        condutores.append([
            obj.nome
        ])
    return render(request, 'polls/preview_condutores.html', {'campos': campos, 'condutores': condutores})

def preview_veiculos(request):
    from .models import Veiculo
    campos = ["tipo_veiculo", "placa", "patrimonio"]
    veiculos = []
    for obj in Veiculo.objects.all():
        veiculos.append([
            obj.tipo_veiculo, obj.placa, obj.patrimonio
        ])
    return render(request, 'polls/preview_veiculos.html', {'campos': campos, 'veiculos': veiculos})

def autocomplete_field(request, field):
    term = request.GET.get('term', '')
    results = set()
    # Paciente
    for obj in Paciente.objects.all():
        valor = getattr(obj, field, None)
        if valor and term.lower() in str(valor).lower():
            results.add(str(valor))
    # Clinica
    for obj in Clinica.objects.all():
        valor = getattr(obj, field, None)
        if valor and term.lower() in str(valor).lower():
            results.add(str(valor))
    # Condutor
    for obj in Condutor.objects.all():
        valor = getattr(obj, field, None)
        if valor and term.lower() in str(valor).lower():
            results.add(str(valor))
    # Veiculo
    for obj in Veiculo.objects.all():
        valor = getattr(obj, field, None)
        if valor and term.lower() in str(valor).lower():
            results.add(str(valor))
    return JsonResponse(list(results), safe=False)

from django.http import JsonResponse
from .models import Paciente

def pacientes_json(request):
	from django.db.models import Exists, OuterRef
	from .models import Transporte
	pacientes = Paciente.objects.annotate(
		ja_alocado=Exists(
			Transporte.objects.filter(paciente=OuterRef('pk'))
		)
	)
	data = [
		{
			'nome': p.nome,
			'endereco': p.endereco,
			'latitude': float(p.latitude) if p.latitude else None,
			'longitude': float(p.longitude) if p.longitude else None,
		}
		for p in pacientes
	]
	return JsonResponse(data, safe=False)

from django.shortcuts import render

def mapa_pacientes(request):
	breadcrumbs = [
		{'label': 'Início', 'url': '/'},
		{'label': 'Pacientes', 'url': '/'},
		{'label': 'Mapa de Pacientes', 'url': ''}
	]
	return render(request, 'transporte_pacientes/mapa_pacientes_novo.html', {'breadcrumbs': breadcrumbs})

def excluir_transporte(request, transporte_id):
    """Exclui um transporte específico por ID."""
    from .models import Transporte
    from django.contrib import messages
    if request.method == 'POST':
        transporte = get_object_or_404(Transporte, id=transporte_id)
        transporte.delete()
        messages.success(request, 'Transporte excluído com sucesso!')
    return redirect('transporte_pacientes:listar_transportes')

def politica_privacidade(request):
    return render(request, 'politica_privacidade.html')
