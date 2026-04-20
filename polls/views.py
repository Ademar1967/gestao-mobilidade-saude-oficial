from django.db import models
from django.http import JsonResponse
from django.views.decorators.http import require_GET
# --- AUTOCOMPLETE DE VEÍCULOS (AMBULÂNCIA POR PATRIMÔNIO, VAN POR PLACA) ---
@require_GET
def buscar_veiculos_sugestoes(request):
	from .models import Veiculo
	termo = (request.GET.get('q') or '').strip()
	if len(termo) < 2:
		return JsonResponse({'sucesso': True, 'resultados': []})
	queryset = (
		Veiculo.objects.only('id', 'nome', 'patrimonio', 'placa', 'tipo_veiculo')
		.filter(
			(
				(models.Q(tipo_veiculo='ambulancia') & models.Q(patrimonio__icontains=termo)) |
				(models.Q(tipo_veiculo='van') & models.Q(placa__icontains=termo)) |
				(models.Q(nome__icontains=termo))
			)
		)
		.order_by('tipo_veiculo', 'patrimonio', 'placa')[:8]
	)
	resultados = []
	for v in queryset:
		resultados.append({
			'id': v.id,
			'nome': v.nome,
			'patrimonio': v.patrimonio or '',
			'placa': v.placa or '',
			'tipo': v.tipo_veiculo,
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
	"""Retorna sugestoes de clinicas por nome para autocomplete no formulario."""
	from django.http import JsonResponse
	from .models import Clinica
	termo = (request.GET.get('q') or '').strip()
	if len(termo) < 2:
		return JsonResponse({'sucesso': True, 'resultados': []})
	queryset = (
		Clinica.objects
		.only('id', 'nome', 'endereco', 'bairro', 'cidade', 'telefone')
		.filter(nome__icontains=termo)
		.order_by('nome')[:8]
	)
	resultados = [
		{
			'id': c.id,
			'nome': c.nome,
			'endereco': c.endereco or '',
			'bairro': c.bairro or '',
			'cidade': c.cidade or '',
			'telefone': c.telefone or '',
		}
		for c in queryset
	]
	audit_logger.info("Sugestoes de clinica consultadas", extra={"termo": termo, "quantidade": len(resultados)})
	return JsonResponse({'sucesso': True, 'resultados': resultados})


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
	from .models import Paciente
	paciente_id = request.GET.get('paciente_id')
	from .models import Paciente
	from .models import Veiculo
	veiculos = Veiculo.objects.all().order_by('tipo_veiculo', 'patrimonio', 'placa')
	if request.method == 'POST':
		form = TransporteForm(request.POST)
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
			from django.contrib import messages
			if hasattr(form, 'novo_veiculo_cadastrado') and form.novo_veiculo_cadastrado:
				messages.success(request, 'Veículo cadastrado com sucesso!')
			elif hasattr(form, 'veiculo_ja_existia') and form.veiculo_ja_existia:
				messages.warning(request, 'Atenção: Este veículo já estava cadastrado e foi apenas selecionado. Não é possível cadastrar o mesmo veículo duas vezes.')
			messages.success(request, 'Transporte cadastrado com sucesso!')
			# Após salvar, exibe mensagem e mantém usuário na tela de cadastro
			form = TransporteForm()  # Limpa o formulário
			return render(request, 'transporte_pacientes/cadastrar_transporte.html', {'form': form, 'veiculos': veiculos})
		audit_logger.warning("Falha de validacao ao cadastrar transporte", extra={"erros": form.errors.as_json()})
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

def listar_transportes(request):
	"""Lista todos os transportes ordenados por data e hora de saida."""
	transportes = Transporte.objects.select_related('paciente', 'veiculo', 'condutor', 'clinica', 'enfermagem').order_by('-data_transporte', '-hora_saida')
	return render(request, 'transporte_pacientes/listar_transportes.html', {'transportes': transportes})
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
	else:
		form = EnfermagemForm()
	enfermagens = Enfermagem.objects.all().order_by('-id')
	return render(request, 'transporte_pacientes/cadastrar_enfermagem.html', {'form': form, 'enfermagens': enfermagens})
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
# Autocomplete AJAX para endereÃ§o de unidade de saÃºde
def autocomplete_endereco_unidade(request):
	import unicodedata
	import logging
	try:
		from rapidfuzz import process, fuzz
	except ImportError:
		process = None
		fuzz = None
	def normalize(s):
		return unicodedata.normalize('NFKD', str(s)).encode('ASCII', 'ignore').decode('ASCII').lower()
	term = normalize(request.GET.get('term', ''))
	# Corrige para garantir que o arquivo adicional seja buscado na raiz do projeto
	import os
	base_dir = Path(__file__).resolve().parent.parent
	project_root = base_dir.parent if (base_dir / 'manage.py').exists() else base_dir
	path2 = base_dir / 'enderecos_sp_hospitais_referencia_corrigido.csv'
	path3 = project_root / 'enderecos_sp_hospitais_adicionais.csv'
	resultados = []
	try:
		# Tenta ler apenas os arquivos de hospitais disponíveis
		frames = []
		try:
			df2 = pd.read_csv(path2, sep=',', encoding='utf-8', quoting=0, on_bad_lines='warn')
			frames.append(df2)
		except Exception as e:
			logging.warning(f"[AUTOCOMPLETE] Falha ao ler {path2}: {e}")
		try:
			df3 = pd.read_csv(path3, sep=',', encoding='utf-8', quoting=0, on_bad_lines='warn')
			frames.append(df3)
		except Exception as e:
			logging.warning(f"[AUTOCOMPLETE] Falha ao ler {path3}: {e}")
		if not frames:
			return JsonResponse({'error': 'Nenhum arquivo de hospitais disponível.'}, status=500)
		df = pd.concat(frames, ignore_index=True)
		if term:
			# Verifica se as colunas existem
			for col in ['nome','logradouro','numero','bairro','municipio','cep']:
				if col not in df.columns:
					logging.error(f"[AUTOCOMPLETE] Coluna ausente: {col}")
					return JsonResponse({'error': f'Coluna ausente: {col}'}, status=500)
			nomes_normalizados = df['nome'].apply(normalize)
			# Busca direta
			mask = nomes_normalizados.str.contains(term)
			encontrados = df[mask]
			# Sempre faz busca fuzzy se menos de 10 resultados
			indices_usados = set(encontrados.index.tolist())
			if encontrados.shape[0] < 10 and process and fuzz:
				nomes_lista = nomes_normalizados.tolist()
				fuzzy_matches = process.extract(term, nomes_lista, scorer=fuzz.WRatio, limit=20)
				fuzzy_indices = [m[2] for m in fuzzy_matches if m[1] > 60 and m[2] not in indices_usados]
				for idx in fuzzy_indices:
					row = df.iloc[idx]
					endereco_completo = f"{row['logradouro']}, {row['numero']}, {row['bairro']}, {row['municipio']}, {row['cep']}"
					resultados.append({
						'label': row['nome'],
						'value': endereco_completo,
						'logradouro': row['logradouro'],
						'numero': int(row['numero']) if hasattr(row['numero'], 'item') or str(type(row['numero'])).startswith("<class 'numpy.") else row['numero'],
						'cep': row['cep']
					})
					indices_usados.add(idx)
					if len(resultados) + encontrados.shape[0] >= 10:
						break
			# Resultados diretos
			for _, row in encontrados.head(10 - len(resultados)).iterrows():
				endereco_completo = f"{row['logradouro']}, {row['numero']}, {row['bairro']}, {row['municipio']}, {row['cep']}"
				resultados.append({
					'label': row['nome'],
					'value': endereco_completo,
					'logradouro': row['logradouro'],
					'numero': int(row['numero']) if hasattr(row['numero'], 'item') or str(type(row['numero'])).startswith("<class 'numpy.") else row['numero'],
					'cep': row['cep']
				})
		# Remover duplicados mantendo ordem
		seen = set()
		resultados_unicos = []
		for r in resultados:
			if r['label'] not in seen:
				resultados_unicos.append(r)
				seen.add(r['label'])
		logging.warning(f"[AUTOCOMPLETE] term: {term} | resultados: {resultados_unicos}")
		return JsonResponse(resultados_unicos, safe=False)
	except Exception as e:
		# Tratamento de erro: loga e retorna erro amigÃ¡vel
		logging.error(f"[AUTOCOMPLETE] Erro: {e}")
		return JsonResponse({'error': str(e)}, status=500)
from django.shortcuts import render
from .models import Veiculo, Condutor, Clinica, Paciente
from .excel_utils import exportar_excel_profissional
import tempfile
from django.shortcuts import render, redirect
from .forms import PacienteForm, VeiculoForm, CondutorForm, ClinicaForm
from django.http import HttpResponse, JsonResponse

def home(request):
	"""Pagina inicial do app exibindo as unidades de saude cadastradas."""
	from .models import Clinica
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
	enderecos_df = pd.read_csv(enderecos_path)
	enderecos_dict = {row['nome']: row for _, row in enderecos_df.iterrows()}

	campos = ["nome", "idade", "peso", "endereco", "referencia", "telefone", "tratamento", "oxigenio", "observacoes", "evolucao", "status", "destino_nome", "destino_endereco_completo"]
	pacientes = []
	for obj in Paciente.objects.all():
		destino_nome = getattr(obj, 'referencia', '')  # Supondo que o campo referencia seja o nome do destino
		endereco_info = enderecos_dict.get(destino_nome, {})
		endereco_completo = ""
		if endereco_info:
			endereco_completo = f"{endereco_info.get('logradouro','')} {endereco_info.get('numero','')}, {endereco_info.get('bairro','')}, {endereco_info.get('municipio','')} - CEP {endereco_info.get('cep','')}"
		pacientes.append([
			obj.nome, obj.idade, obj.peso, obj.endereco, obj.referencia, obj.telefone, obj.tratamento, obj.oxigenio, obj.observacoes, obj.evolucao, obj.status,
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
    enderecos_df = pd.read_csv(enderecos_path)
    enderecos_dict = {row['nome']: row for _, row in enderecos_df.iterrows()}
    campos = ["nome", "idade", "peso", "endereco", "referencia", "telefone", "tratamento", "oxigenio", "observacoes", "evolucao", "status", "destino_nome", "destino_endereco_completo"]
    pacientes = []
    for obj in Paciente.objects.all():
        destino_nome = getattr(obj, 'referencia', '')
        endereco_info = enderecos_dict.get(destino_nome, {})
        endereco_completo = ""
        if endereco_info:
            endereco_completo = f"{endereco_info.get('logradouro','')} {endereco_info.get('numero','')}, {endereco_info.get('bairro','')}, {endereco_info.get('municipio','')} - CEP {endereco_info.get('cep','')}"
        pacientes.append([
            obj.nome, obj.idade, obj.peso, obj.endereco, obj.referencia, obj.telefone, obj.tratamento, obj.oxigenio, obj.observacoes, obj.evolucao, obj.status,
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
	total_acompanhantes = sum(1 for p in pacientes if getattr(p, 'acompanhante', False))
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
	else:
		form = CondutorForm()
	from .models import Condutor
	condutores = Condutor.objects.all().order_by('-id')
	return render(request, 'transporte_pacientes/cadastrar_condutor.html', {'form': form, 'condutores': condutores})

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
	return render(request, 'transporte_pacientes/cadastrar_clinica.html', {'form': form, 'clinicas': clinicas, 'unidades_salvas': clinicas})

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
    return render(request, 'transporte_pacientes/mapa_pacientes.html')

def excluir_transporte(request, transporte_id):
    """Exclui um transporte específico por ID."""
    from .models import Transporte
    from django.contrib import messages
    if request.method == 'POST':
        transporte = get_object_or_404(Transporte, id=transporte_id)
        transporte.delete()
        messages.success(request, 'Transporte excluído com sucesso!')
    return redirect('transporte_pacientes:listar_transportes')

