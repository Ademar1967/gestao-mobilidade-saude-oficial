from django.test import TestCase
import tempfile
from pathlib import Path
from django.test import override_settings
from polls.models import Paciente, Veiculo, Condutor, Clinica, Enfermagem, Transporte
from django.urls import reverse
# --- TESTES DE MODELS ---
class ModelsTestCase(TestCase):
	def test_criar_paciente(self):
		paciente = Paciente.objects.create(nome='Paciente Model')
		self.assertEqual(str(paciente), 'Paciente Model')

	def test_criar_clinica(self):
		clinica = Clinica.objects.create(nome='Clínica Model')
		self.assertEqual(str(clinica), 'Clínica Model')

	def test_criar_veiculo(self):
		veiculo = Veiculo.objects.create(tipo_veiculo='ambulancia', placa='XYZ1234', patrimonio='P999')
		self.assertIn('Ambulância', str(veiculo))

	def test_criar_condutor(self):
		condutor = Condutor.objects.create(nome='Condutor Model')
		self.assertEqual(str(condutor), 'Condutor Model')

	def test_criar_enfermagem(self):
		enfermagem = Enfermagem.objects.create(nome='Enfermagem Model')
		self.assertEqual(str(enfermagem), 'Enfermagem Model')

# --- TESTES DE FORMS ---
from polls.forms import PacienteForm, ClinicaForm, VeiculoForm, CondutorForm, EnfermagemForm

class FormsTestCase(TestCase):
	def test_paciente_form_endereco_incompleto(self):
		form = PacienteForm(data={
			'nome': 'Paciente Teste',
			'telefone': '11999999999',
			# Não preenche rua, numero, bairro, cidade
		})
		self.assertFalse(form.is_valid())
		self.assertIn('Preencha todos os campos de endereço: rua, número, bairro e cidade.', str(form.errors))

	def test_paciente_form_valido(self):
		form = PacienteForm(data={
			'nome': 'Paciente Form',
			'telefone': '11999999999',
			'rua': 'Rua Teste',
			'numero': '123',
			'bairro': 'Centro',
			'cidade': 'São Paulo',
		})
		self.assertTrue(form.is_valid())

	def test_clinica_form_valido(self):
		form = ClinicaForm(data={'nome': 'Clínica Form', 'endereco_completo': 'Rua X'})
		self.assertTrue(form.is_valid())

	def test_veiculo_form_valido(self):
		form = VeiculoForm(data={'tipo_veiculo': 'ambulancia', 'placa': 'AAA1111', 'patrimonio': 'P111', 'lotacao': 1})
		self.assertTrue(form.is_valid())

	def test_condutor_form_valido(self):
		form = CondutorForm(data={'nome': 'Condutor Form'})
		self.assertTrue(form.is_valid())

	def test_enfermagem_form_valido(self):
		form = EnfermagemForm(data={'nome': 'Enfermagem Form'})
		self.assertTrue(form.is_valid())

# --- TESTES DE VIEWS (exemplo para home e cadastro de paciente) ---
class ViewsTestCase(TestCase):
	def test_home_view(self):
		url = reverse('transporte_pacientes:home')
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)

	def test_cadastrar_paciente_view(self):
		url = reverse('transporte_pacientes:cadastrar_paciente')
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)

	def test_pacientes_json_geolocalizacao(self):
		# Cria paciente com latitude e longitude
		paciente = Paciente.objects.create(
			nome='Paciente Geo',
			endereco='Rua Teste, 123',
			latitude=-23.55052,
			longitude=-46.633308
		)
		url = reverse('transporte_pacientes:pacientes_json')
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertIn('application/json', response['Content-Type'])
		data = response.json()
		self.assertTrue(any(
			p['nome'] == 'Paciente Geo' and p['latitude'] == -23.55052 and p['longitude'] == -46.633308
			for p in data
		))
from django.urls import reverse
from .models import Paciente, Veiculo, Condutor, Clinica, Enfermagem, Transporte

# --- TESTES AUTOMATIZADOS DO FLUXO DE TRANSPORTE ---
class TransporteTestCase(TestCase):
	def setUp(self):
		# Criar dados básicos para os testes
		self.paciente = Paciente.objects.create(nome='Teste Paciente')
		self.veiculo = Veiculo.objects.create(tipo_veiculo='ambulancia', placa='ABC1234', patrimonio='P123')
		self.condutor = Condutor.objects.create(nome='Condutor Teste')
		self.clinica = Clinica.objects.create(nome='Clínica Teste')
		self.enfermagem = Enfermagem.objects.create(nome='Equipe Teste')

	def test_cadastro_transporte(self):
		# Testa se é possível cadastrar um transporte
		transporte = Transporte.objects.create(
			paciente=self.paciente,
			veiculo=self.veiculo,
			condutor=self.condutor,
			clinica=self.clinica,
			enfermagem=self.enfermagem,
			data_transporte='2026-03-08',
			hora_saida='08:00',
			hora_chegada='09:00',
			observacoes='Teste de transporte'
		)
		self.assertEqual(str(transporte), f"Transporte de {self.paciente} para {self.clinica} em 2026-03-08")


class ArquivosRecebidosViewTestCase(TestCase):
	def test_lista_arquivos_recebidos_em_pasta_entrada(self):
		with tempfile.TemporaryDirectory() as temp_dir:
			base_dir = Path(temp_dir)
			entrada_dir = base_dir / 'entrada'
			entrada_dir.mkdir(parents=True, exist_ok=True)
			(entrada_dir / 'pacientes_teste.csv').write_text('nome,rua,numero,bairro,cidade\nPaciente 1,Rua A,10,Centro,Sao Paulo\n', encoding='utf-8')

			with override_settings(DADOS_RECEBIDOS_DIR=base_dir):
				response = self.client.get(reverse('transporte_pacientes:arquivos_recebidos_pacientes'))

			self.assertEqual(response.status_code, 200)
			self.assertContains(response, 'pacientes_teste.csv')

	def test_salvar_revisao_move_arquivo_para_processados(self):
		with tempfile.TemporaryDirectory() as temp_dir:
			base_dir = Path(temp_dir)
			(base_dir / 'entrada').mkdir(parents=True, exist_ok=True)
			(base_dir / 'processados').mkdir(parents=True, exist_ok=True)
			arquivo = base_dir / 'entrada' / 'pacientes_importados.csv'
			arquivo.write_text('nome,rua,numero,bairro,cidade,estado,cep,ddd,telefone\nPaciente Pasta,Rua A,10,Centro,Sao Paulo,SP,12345-678,11,998877665\n', encoding='utf-8')

			with override_settings(DADOS_RECEBIDOS_DIR=base_dir):
				response = self.client.post(reverse('transporte_pacientes:cadastrar_paciente'), {
					'salvar_web': '1',
					'arquivo_origem_nome': 'pacientes_importados.csv',
					'arquivo_origem_tipo': 'dados_recebidos',
					'nome': 'Paciente Pasta',
					'rua': 'Rua A',
					'numero': '10',
					'bairro': 'Centro',
					'cidade': 'Sao Paulo',
					'estado': 'SP',
					'cep': '12345-678',
					'ddd': '11',
					'telefone': '998877665',
				})

			self.assertEqual(response.status_code, 302)
			self.assertTrue(Paciente.objects.filter(nome='Paciente Pasta').exists())
			self.assertFalse(arquivo.exists())
			self.assertTrue(any((base_dir / 'processados').iterdir()))

	def test_view_listar_transportes(self):
		# Testa se a view de listagem de transportes responde corretamente
		Transporte.objects.create(
			paciente=self.paciente,
			veiculo=self.veiculo,
			condutor=self.condutor,
			clinica=self.clinica,
			enfermagem=self.enfermagem,
			data_transporte='2026-03-08',
		)
		url = reverse('transporte_pacientes:listar_transportes')
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Transporte')


class ClinicaApiTestCase(TestCase):
	def setUp(self):
		self.clinica = Clinica.objects.create(
			nome='Hospital API',
			endereco='Av. Paulista, 1000',
			bairro='Bela Vista',
			cidade='Sao Paulo',
			telefone='1130004000',
		)

	def test_obter_dados_clinica_sucesso(self):
		url = reverse('transporte_pacientes:obter_dados_clinica', kwargs={'clinica_id': self.clinica.id})
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		data = response.json()
		self.assertTrue(data['sucesso'])
		self.assertEqual(data['nome'], 'Hospital API')
		self.assertEqual(data['bairro'], 'Bela Vista')

	def test_obter_dados_clinica_404(self):
		url = reverse('transporte_pacientes:obter_dados_clinica', kwargs={'clinica_id': 999999})
		response = self.client.get(url)
		self.assertEqual(response.status_code, 404)
		data = response.json()
		self.assertFalse(data['sucesso'])

	def test_buscar_clinicas_sugestoes(self):
		Clinica.objects.create(nome='Hospital Santa Casa', endereco='Rua A', bairro='Centro', cidade='Sao Paulo')
		url = reverse('transporte_pacientes:buscar_clinicas_sugestoes')
		response = self.client.get(url, {'q': 'Santa'})
		self.assertEqual(response.status_code, 200)
		data = response.json()
		self.assertTrue(data['sucesso'])
		self.assertGreaterEqual(len(data['resultados']), 1)
		self.assertEqual(data['resultados'][0]['nome'], 'Hospital Santa Casa')


class PacienteFormRegexValidationTestCase(TestCase):
	def test_cep_invalido(self):
		form = PacienteForm(data={
			'nome': 'Paciente CEP',
			'rua': 'Rua Teste',
			'numero': '10',
			'bairro': 'Centro',
			'cidade': 'Sao Paulo',
			'estado': 'SP',
			'cep': '12345',
			'ddd': '11',
			'telefone': '987654321',
		})
		self.assertFalse(form.is_valid())
		self.assertIn('cep', form.errors)

	def test_ddd_invalido(self):
		form = PacienteForm(data={
			'nome': 'Paciente DDD',
			'rua': 'Rua Teste',
			'numero': '10',
			'bairro': 'Centro',
			'cidade': 'Sao Paulo',
			'estado': 'SP',
			'cep': '12345-678',
			'ddd': '1',
			'telefone': '987654321',
		})
		self.assertFalse(form.is_valid())
		self.assertIn('ddd', form.errors)

	def test_validacao_regex_sucesso(self):
		form = PacienteForm(data={
			'nome': 'Paciente Valido',
			'rua': 'Rua Teste',
			'numero': '10',
			'bairro': 'Centro',
			'cidade': 'Sao Paulo',
			'estado': 'sp',
			'cep': '12345678',
			'ddd': '11',
			'telefone': '998877665',
		})
		self.assertTrue(form.is_valid(), form.errors)
		self.assertEqual(form.cleaned_data['estado'], 'SP')
		self.assertEqual(form.cleaned_data['cep'], '12345-678')


class ModelHelperMethodsTestCase(TestCase):
	def test_paciente_contato_e_endereco_formatado(self):
		paciente = Paciente.objects.create(
			nome='Paciente Metodo',
			rua='Rua A',
			numero='10',
			bairro='Centro',
			cidade='Sao Paulo',
			estado='SP',
			cep='01000-000',
			ddd='11',
			telefone='998887777',
		)
		self.assertEqual(paciente.contato_formatado(), '(11) 998887777')
		self.assertEqual(paciente.logradouro_formatado(), 'Rua A, 10')
		self.assertIn('Rua A', paciente.endereco_formatado())
		self.assertIn('01000-000', paciente.endereco_formatado())

	def test_clinica_endereco_resumido(self):
		clinica = Clinica.objects.create(
			nome='Clinica Metodo',
			endereco='Av. Teste, 100',
			bairro='Bairro Teste',
			cidade='Sao Paulo',
		)
		self.assertEqual(clinica.endereco_resumido(), 'Av. Teste, 100 - Bairro Teste - Sao Paulo')

	def test_transporte_resumo_operacional(self):
		paciente = Paciente.objects.create(nome='Paciente Operacao')
		veiculo = Veiculo.objects.create(tipo_veiculo='ambulancia', patrimonio='VT500')
		condutor = Condutor.objects.create(nome='Condutor Operacao')
		clinica = Clinica.objects.create(nome='Clinica Operacao')
		enfermagem = Enfermagem.objects.create(nome='Enfermagem Operacao')
		transporte = Transporte.objects.create(
			paciente=paciente,
			veiculo=veiculo,
			condutor=condutor,
			clinica=clinica,
			enfermagem=enfermagem,
			data_transporte='2026-03-22',
		)
		resumo = transporte.resumo_operacional()
		self.assertIn('Paciente Operacao', resumo)
		self.assertIn('Clinica Operacao', resumo)
