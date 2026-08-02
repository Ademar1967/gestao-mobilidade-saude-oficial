from django.test import TestCase
from datetime import time
import tempfile
from pathlib import Path
from django.test import override_settings
from django.conf import settings
from polls.models import Paciente, Veiculo, Condutor, Clinica, Enfermagem, Transporte
from django.urls import reverse


def _secure_request_kwargs():
    if getattr(settings, "SECURE_SSL_REDIRECT", False):
        return {"secure": True}
    return {}


# --- TESTES DE MODELS ---
class ModelsTestCase(TestCase):
    def test_criar_paciente(self):
        paciente = Paciente.objects.create(nome="Paciente Model")
        self.assertEqual(str(paciente), "Paciente Model")

    def test_criar_clinica(self):
        clinica = Clinica.objects.create(nome="Clínica Model")
        self.assertEqual(str(clinica), "Clínica Model")

    def test_criar_veiculo(self):
        veiculo = Veiculo.objects.create(
            tipo_veiculo="ambulancia", placa="XYZ1234", patrimonio="P999"
        )
        self.assertIn("Ambulância", str(veiculo))

    def test_criar_condutor(self):
        condutor = Condutor.objects.create(nome="Condutor Model")
        self.assertEqual(str(condutor), "Condutor Model")

    def test_criar_enfermagem(self):
        enfermagem = Enfermagem.objects.create(nome="Enfermagem Model")
        self.assertEqual(str(enfermagem), "Enfermagem Model")


# --- TESTES DE FORMS ---
from polls.forms import (
    PacienteForm,
    ClinicaForm,
    VeiculoForm,
    CondutorForm,
    EnfermagemForm,
)


class FormsTestCase(TestCase):
    def test_paciente_form_endereco_incompleto(self):
        form = PacienteForm(
            data={
                "nome": "Paciente Teste",
                "telefone": "11999999999",
                # Não preenche rua, numero, bairro, cidade
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Preencha todos os campos de endereço: rua, número, bairro e cidade.",
            str(form.errors),
        )

    def test_paciente_form_valido(self):
        form = PacienteForm(
            data={
                "nome": "Paciente Form",
                "telefone": "11999999999",
                "rua": "Rua Teste",
                "numero": "123",
                "bairro": "Centro",
                "cidade": "São Paulo",
                "servico_status": "ativo",
                "acompanhantes": 0,
                "consentimento_lgpd": True,
            }
        )
        self.assertTrue(form.is_valid())

    def test_clinica_form_valido(self):
        form = ClinicaForm(data={"nome": "Clínica Form", "endereco_completo": "Rua X"})
        self.assertTrue(form.is_valid())

    def test_veiculo_form_valido(self):
        form = VeiculoForm(
            data={
                "tipo_veiculo": "ambulancia",
                "placa": "AAA1111",
                "patrimonio": "P111",
                "lotacao": 1,
            }
        )
        self.assertTrue(form.is_valid())

    def test_condutor_form_valido(self):
        form = CondutorForm(data={"nome": "Condutor Form"})
        self.assertTrue(form.is_valid())

    def test_enfermagem_form_valido(self):
        form = EnfermagemForm(data={"nome": "Enfermagem Form"})
        self.assertTrue(form.is_valid())


# --- TESTES DE VIEWS (exemplo para home e cadastro de paciente) ---
class ViewsTestCase(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model

        self.username = "testuser"
        self.password = "testpass123"
        self.user = get_user_model().objects.create_user(
            username=self.username, password=self.password
        )
        self.client.login(username=self.username, password=self.password)

    def test_home_view(self):
        url = reverse("transporte_pacientes:home")
        response = self.client.get(url, **_secure_request_kwargs())
        self.assertEqual(response.status_code, 200)

    def test_cadastrar_paciente_view(self):
        url = reverse("transporte_pacientes:cadastrar_paciente")
        response = self.client.get(url, **_secure_request_kwargs())
        self.assertEqual(response.status_code, 200)

    def test_pacientes_json_geolocalizacao(self):
        # Cria paciente com latitude e longitude
        paciente = Paciente.objects.create(
            nome="Paciente Geo",
            endereco="Rua Teste, 123",
            latitude=-23.55052,
            longitude=-46.633308,
        )
        url = reverse("transporte_pacientes:pacientes_json")
        response = self.client.get(url, **_secure_request_kwargs())
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/json", response["Content-Type"])
        payload = response.json()
        data = payload.get("pacientes", [])
        self.assertTrue(
            any(
                p["nome"] == "Paciente Geo"
                and p["latitude"] == -23.55052
                and p["longitude"] == -46.633308
                for p in data
            )
        )

    def test_cadastrar_paciente_lista_exibe_todos_os_cadastros(self):
        Paciente.objects.create(
            nome="Paciente Lista 1",
            rua="Rua A",
            numero="10",
            bairro="Centro",
            cidade="Sao Paulo",
        )
        Paciente.objects.create(
            nome="Paciente Lista 2",
            rua="Rua B",
            numero="20",
            bairro="Centro",
            cidade="Sao Paulo",
        )
        response = self.client.get(
            reverse("transporte_pacientes:cadastrar_paciente"),
            **_secure_request_kwargs(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paciente Lista 1")
        self.assertContains(response, "Paciente Lista 2")

    def test_cadastrar_paciente_reaproveita_sem_duplicar_quando_nome_telefone_iguais(
        self,
    ):
        existente = Paciente.objects.create(
            nome="Paciente Reaproveitar",
            rua="Rua Original",
            numero="1",
            bairro="Centro",
            cidade="Sao Paulo",
            estado="SP",
            cep="01000-000",
            ddd="11",
            telefone="999999999",
            consentimento_lgpd=True,
        )

        payload = {
            "nome": "Paciente Reaproveitar",
            "rua": "Rua Atualizada",
            "numero": "99",
            "bairro": "Novo Bairro",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "cep": "02000-000",
            "ddd": "11",
            "telefone": "99999-9999",
            "servico_status": "ativo",
            "acompanhantes": 0,
            "consentimento_lgpd": "on",
        }

        response = self.client.post(
            reverse("transporte_pacientes:cadastrar_paciente"),
            payload,
            **_secure_request_kwargs(),
        )
        self.assertEqual(response.status_code, 302)

        self.assertEqual(
            Paciente.objects.filter(
                nome="Paciente Reaproveitar", telefone="999999999"
            ).count(),
            1,
        )
        existente.refresh_from_db()
        self.assertEqual(existente.rua, "Rua Atualizada")
        self.assertEqual(existente.numero, "99")


from django.urls import reverse
from .models import Paciente, Veiculo, Condutor, Clinica, Enfermagem, Transporte


# --- TESTES AUTOMATIZADOS DO FLUXO DE TRANSPORTE ---
class TransporteTestCase(TestCase):
    def setUp(self):
        # Criar dados básicos para os testes
        self.paciente = Paciente.objects.create(nome="Teste Paciente")
        self.veiculo = Veiculo.objects.create(
            tipo_veiculo="ambulancia", placa="ABC1234", patrimonio="P123"
        )
        self.condutor = Condutor.objects.create(nome="Condutor Teste")
        self.clinica = Clinica.objects.create(nome="Clínica Teste")
        self.enfermagem = Enfermagem.objects.create(nome="Equipe Teste")

    def test_cadastro_transporte(self):
        # Testa se é possível cadastrar um transporte
        transporte = Transporte.objects.create(
            paciente=self.paciente,
            veiculo=self.veiculo,
            condutor=self.condutor,
            clinica=self.clinica,
            enfermagem=self.enfermagem,
            data_transporte="2026-03-08",
            hora_saida="08:00",
            hora_chegada="09:00",
            observacoes="Teste de transporte",
        )
        self.assertEqual(
            str(transporte),
            f"Transporte de {self.paciente} para {self.clinica} em 2026-03-08",
        )


class ArquivosRecebidosViewTestCase(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model

        self.username = "testuser"
        self.password = "testpass123"
        self.user = get_user_model().objects.create_user(
            username=self.username, password=self.password
        )
        self.client.login(username=self.username, password=self.password)
        self.paciente = Paciente.objects.create(nome="Teste Paciente")
        self.veiculo = Veiculo.objects.create(
            tipo_veiculo="ambulancia", placa="ABC1234", patrimonio="P123"
        )
        self.condutor = Condutor.objects.create(nome="Condutor Teste")
        self.clinica = Clinica.objects.create(nome="Clínica Teste")
        self.enfermagem = Enfermagem.objects.create(nome="Equipe Teste")

    def test_lista_arquivos_recebidos_em_pasta_entrada(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            entrada_dir = base_dir / "entrada"
            entrada_dir.mkdir(parents=True, exist_ok=True)
            (entrada_dir / "pacientes_teste.csv").write_text(
                "nome,rua,numero,bairro,cidade\nPaciente 1,Rua A,10,Centro,Sao Paulo\n",
                encoding="utf-8",
            )

            with override_settings(DADOS_RECEBIDOS_DIR=base_dir):
                response = self.client.get(
                    reverse("transporte_pacientes:arquivos_recebidos_pacientes"),
                    **_secure_request_kwargs(),
                )

            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "pacientes_teste.csv")

    def test_salvar_revisao_move_arquivo_para_processados(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            (base_dir / "entrada").mkdir(parents=True, exist_ok=True)
            (base_dir / "processados").mkdir(parents=True, exist_ok=True)
            arquivo = base_dir / "entrada" / "pacientes_importados.csv"
            arquivo.write_text(
                "nome,rua,numero,bairro,cidade,estado,cep,ddd,telefone\nPaciente Pasta,Rua A,10,Centro,Sao Paulo,SP,12345-678,11,998877665\n",
                encoding="utf-8",
            )

            with override_settings(DADOS_RECEBIDOS_DIR=base_dir):
                response = self.client.post(
                    reverse("transporte_pacientes:cadastrar_paciente"),
                    {
                        "salvar_web": "1",
                        "arquivo_origem_nome": "pacientes_importados.csv",
                        "arquivo_origem_tipo": "dados_recebidos",
                        "nome": "Paciente Pasta",
                        "rua": "Rua A",
                        "numero": "10",
                        "bairro": "Centro",
                        "cidade": "Sao Paulo",
                        "estado": "SP",
                        "cep": "12345-678",
                        "ddd": "11",
                        "telefone": "998877665",
                        "consentimento_lgpd": "on",
                        "acompanhantes": 0,
                        "maca": "",
                        "cadeirante": "",
                        "servico_status": "ativo",
                    },
                    **_secure_request_kwargs(),
                )

            self.assertIn(response.status_code, [200, 302])
            self.assertTrue(Paciente.objects.filter(nome="Paciente Pasta").exists())
            self.assertFalse(arquivo.exists())
            self.assertTrue(any((base_dir / "processados").iterdir()))

    def test_view_listar_transportes(self):
        # Testa se a view de listagem de transportes responde corretamente
        Transporte.objects.create(
            paciente=self.paciente,
            veiculo=self.veiculo,
            condutor=self.condutor,
            clinica=self.clinica,
            enfermagem=self.enfermagem,
            data_transporte="2026-03-08",
        )
        url = reverse("transporte_pacientes:listar_transportes")
        response = self.client.get(url, **_secure_request_kwargs())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Transporte")

    def test_listar_transportes_coluna_consulta_usa_horario_consulta_do_paciente(self):
        self.paciente.horario_consulta = time(22, 58)
        self.paciente.save(update_fields=["horario_consulta"])

        Transporte.objects.create(
            paciente=self.paciente,
            veiculo=self.veiculo,
            condutor=self.condutor,
            clinica=self.clinica,
            enfermagem=self.enfermagem,
            data_transporte="2026-06-10",
            hora_saida="20:00",
            hora_chegada="21:45",
        )
        url = reverse("transporte_pacientes:listar_transportes")
        response = self.client.get(url, **_secure_request_kwargs())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "22:58")


class ClinicaApiTestCase(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model

        self.username = "testuser"
        self.password = "testpass123"
        self.user = get_user_model().objects.create_user(
            username=self.username, password=self.password
        )
        self.client.login(username=self.username, password=self.password)
        self.clinica = Clinica.objects.create(
            nome="Hospital API",
            endereco="Av. Paulista, 1000",
            bairro="Bela Vista",
            cidade="Sao Paulo",
            telefone="1130004000",
        )

    def test_obter_dados_clinica_sucesso(self):
        url = reverse(
            "transporte_pacientes:obter_dados_clinica",
            kwargs={"clinica_id": self.clinica.id},
        )
        response = self.client.get(url, **_secure_request_kwargs())
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["sucesso"])
        self.assertEqual(data["nome"], "Hospital API")


class EstatisticasFiltroPeriodoTestCase(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model

        self.username = "staffstats"
        self.password = "testpass123"
        self.user = get_user_model().objects.create_user(
            username=self.username,
            password=self.password,
            is_staff=True,
        )
        self.client.login(username=self.username, password=self.password)
        self.paciente = Paciente.objects.create(nome="Paciente Estatistica")
        self.condutor = Condutor.objects.create(nome="Condutor Estatistica")
        self.clinica = Clinica.objects.create(nome="Clinica Estatistica")
        self.enfermagem = Enfermagem.objects.create(nome="Enfermagem Estatistica")
        self.veiculo_jan = Veiculo.objects.create(
            tipo_veiculo="ambulancia", patrimonio="JAN001"
        )
        self.veiculo_fev = Veiculo.objects.create(
            tipo_veiculo="ambulancia", patrimonio="FEV002"
        )

    def test_estatistica_veiculo_respeita_filtro_periodo(self):
        Transporte.objects.create(
            paciente=self.paciente,
            veiculo=self.veiculo_jan,
            condutor=self.condutor,
            clinica=self.clinica,
            enfermagem=self.enfermagem,
            data_transporte="2026-01-15",
        )
        Transporte.objects.create(
            paciente=self.paciente,
            veiculo=self.veiculo_fev,
            condutor=self.condutor,
            clinica=self.clinica,
            enfermagem=self.enfermagem,
            data_transporte="2026-02-10",
        )

        url = reverse("transporte_pacientes:estatistica_veiculo")
        response = self.client.get(
            url,
            {"data_inicio": "2026-01-01", "data_fim": "2026-01-31"},
            **_secure_request_kwargs(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "JAN001")
        self.assertNotContains(response, "FEV002")

    def test_obter_dados_clinica_404(self):
        url = reverse(
            "transporte_pacientes:obter_dados_clinica", kwargs={"clinica_id": 999999}
        )
        response = self.client.get(url, **_secure_request_kwargs())
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data["sucesso"])

    def test_buscar_clinicas_sugestoes(self):
        Clinica.objects.create(
            nome="Hospital Santa Casa",
            endereco="Rua A",
            bairro="Centro",
            cidade="Sao Paulo",
        )
        url = reverse("transporte_pacientes:buscar_clinicas_sugestoes")
        response = self.client.get(url, {"q": "Santa"}, **_secure_request_kwargs())
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["sucesso"])
        self.assertGreaterEqual(len(data["resultados"]), 1)
        self.assertEqual(data["resultados"][0]["nome"], "Hospital Santa Casa")


class PacienteFormRegexValidationTestCase(TestCase):
    def test_cep_invalido(self):
        form = PacienteForm(
            data={
                "nome": "Paciente CEP",
                "rua": "Rua Teste",
                "numero": "10",
                "bairro": "Centro",
                "cidade": "Sao Paulo",
                "estado": "SP",
                "cep": "12345",
                "ddd": "11",
                "telefone": "987654321",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("cep", form.errors)

    def test_ddd_invalido(self):
        form = PacienteForm(
            data={
                "nome": "Paciente DDD",
                "rua": "Rua Teste",
                "numero": "10",
                "bairro": "Centro",
                "cidade": "Sao Paulo",
                "estado": "SP",
                "cep": "12345-678",
                "ddd": "1",
                "telefone": "987654321",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("ddd", form.errors)

    def test_validacao_regex_sucesso(self):
        form = PacienteForm(
            data={
                "nome": "Paciente Valido",
                "rua": "Rua Teste",
                "numero": "10",
                "bairro": "Centro",
                "cidade": "Sao Paulo",
                "estado": "sp",
                "cep": "12345678",
                "ddd": "11",
                "telefone": "998877665",
                "servico_status": "ativo",
                "acompanhantes": 0,
                "consentimento_lgpd": True,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["estado"], "SP")
        self.assertEqual(form.cleaned_data["cep"], "12345-678")


class ModelHelperMethodsTestCase(TestCase):
    def test_paciente_contato_e_endereco_formatado(self):
        paciente = Paciente.objects.create(
            nome="Paciente Metodo",
            rua="Rua A",
            numero="10",
            bairro="Centro",
            cidade="Sao Paulo",
            estado="SP",
            cep="01000-000",
            ddd="11",
            telefone="998887777",
        )
        self.assertEqual(paciente.contato_formatado(), "(11) 998887777")
        self.assertEqual(paciente.logradouro_formatado(), "Rua A, 10")
        self.assertIn("Rua A", paciente.endereco_formatado())
        self.assertIn("01000-000", paciente.endereco_formatado())

    def test_clinica_endereco_resumido(self):
        clinica = Clinica.objects.create(
            nome="Clinica Metodo",
            endereco="Av. Teste, 100",
            bairro="Bairro Teste",
            cidade="Sao Paulo",
        )
        self.assertEqual(
            clinica.endereco_resumido(), "Av. Teste, 100 - Bairro Teste - Sao Paulo"
        )

    def test_transporte_resumo_operacional(self):
        paciente = Paciente.objects.create(nome="Paciente Operacao")
        veiculo = Veiculo.objects.create(tipo_veiculo="ambulancia", patrimonio="VT500")
        condutor = Condutor.objects.create(nome="Condutor Operacao")
        clinica = Clinica.objects.create(nome="Clinica Operacao")
        enfermagem = Enfermagem.objects.create(nome="Enfermagem Operacao")
        transporte = Transporte.objects.create(
            paciente=paciente,
            veiculo=veiculo,
            condutor=condutor,
            clinica=clinica,
            enfermagem=enfermagem,
            data_transporte="2026-03-22",
        )
        resumo = transporte.resumo_operacional()
        self.assertIn("Paciente Operacao", resumo)
        self.assertIn("Clinica Operacao", resumo)


class MasterDataSyncTestCase(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model

        self.username = "syncuser"
        self.password = "testpass123"
        self.user = get_user_model().objects.create_user(
            username=self.username, password=self.password
        )
        self.client.login(username=self.username, password=self.password)

    def test_cadastro_condutor_atualiza_condutores_csv(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            with override_settings(BASE_DIR=base_dir):
                response = self.client.post(
                    reverse("transporte_pacientes:cadastrar_condutor"),
                    {"nome": "CONDUTOR CSV TESTE"},
                    **_secure_request_kwargs(),
                )

            self.assertEqual(response.status_code, 302)
            csv_path = base_dir / "condutores.csv"
            self.assertTrue(csv_path.exists())
            conteudo = csv_path.read_text(encoding="utf-8")
            self.assertIn("CONDUTOR CSV TESTE", conteudo)

    def test_cadastro_enfermagem_atualiza_enfermagem_csv(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            with override_settings(BASE_DIR=base_dir):
                response = self.client.post(
                    reverse("transporte_pacientes:cadastrar_enfermagem"),
                    {"nome": "ENFERMAGEM CSV TESTE"},
                    **_secure_request_kwargs(),
                )

            self.assertEqual(response.status_code, 302)
            csv_path = base_dir / "enfermagem.csv"
            self.assertTrue(csv_path.exists())
            conteudo = csv_path.read_text(encoding="utf-8")
            self.assertIn("ENFERMAGEM CSV TESTE", conteudo)

    def test_fluxo_salvar_e_recarregar_condutor(self):
        nome = "CONDUTOR PERSISTENCIA E2E"
        response = self.client.post(
            reverse("transporte_pacientes:cadastrar_condutor"),
            {"nome": nome},
            **_secure_request_kwargs(),
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Condutor.objects.filter(nome=nome).exists())

        get_response = self.client.get(
            reverse("transporte_pacientes:cadastrar_condutor"),
            **_secure_request_kwargs(),
        )
        self.assertEqual(get_response.status_code, 200)
        self.assertContains(get_response, nome)

    def test_fluxo_salvar_e_recarregar_enfermagem(self):
        nome = "ENFERMAGEM PERSISTENCIA E2E"
        response = self.client.post(
            reverse("transporte_pacientes:cadastrar_enfermagem"),
            {"nome": nome},
            **_secure_request_kwargs(),
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Enfermagem.objects.filter(nome=nome).exists())

        get_response = self.client.get(
            reverse("transporte_pacientes:cadastrar_enfermagem"),
            **_secure_request_kwargs(),
        )
        self.assertEqual(get_response.status_code, 200)
        self.assertContains(get_response, nome)

    def test_fluxo_salvar_e_recarregar_clinica(self):
        nome = "CLINICA PERSISTENCIA E2E"
        response = self.client.post(
            reverse("transporte_pacientes:cadastrar_clinica"),
            {
                "nome": nome,
                "endereco": "Rua Persistencia, 123",
                "bairro": "Centro",
                "cidade": "Sao Paulo",
            },
            **_secure_request_kwargs(),
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Clinica.objects.filter(nome=nome).exists())

        get_response = self.client.get(
            reverse("transporte_pacientes:cadastrar_clinica"),
            **_secure_request_kwargs(),
        )
        self.assertEqual(get_response.status_code, 200)
        self.assertContains(get_response, nome)

    def test_fluxo_salvar_e_recarregar_veiculo(self):
        patrimonio = "VT-PERSIST-001"
        response = self.client.post(
            reverse("transporte_pacientes:cadastrar_veiculo"),
            {
                "tipo_veiculo": "ambulancia",
                "patrimonio": patrimonio,
                "placa": "ABC1D23",
                "lotacao": 1,
            },
            **_secure_request_kwargs(),
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Veiculo.objects.filter(patrimonio=patrimonio).exists())

        get_response = self.client.get(
            reverse("transporte_pacientes:cadastrar_veiculo"),
            **_secure_request_kwargs(),
        )
        self.assertEqual(get_response.status_code, 200)
        self.assertContains(get_response, patrimonio)

    def test_cadastro_paciente_atualiza_dados_pacientes_csv(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            with override_settings(BASE_DIR=base_dir):
                response = self.client.post(
                    reverse("transporte_pacientes:cadastrar_paciente"),
                    {
                        "nome": "PACIENTE CSV FUTURO",
                        "rua": "Rua Persistencia",
                        "numero": "100",
                        "bairro": "Centro",
                        "cidade": "Sao Paulo",
                        "estado": "SP",
                        "cep": "01000-000",
                        "ddd": "11",
                        "telefone": "99999-1111",
                        "consentimento_lgpd": "on",
                        "acompanhantes": 0,
                        "servico_status": "ativo",
                    },
                    **_secure_request_kwargs(),
                )

            self.assertEqual(response.status_code, 302)
            csv_path = base_dir / "dados_pacientes.csv"
            self.assertTrue(csv_path.exists())
            conteudo = csv_path.read_text(encoding="utf-8")
            self.assertIn("PACIENTE CSV FUTURO", conteudo)

    def test_reidrata_pacientes_do_csv_quando_banco_vazio(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            csv_path = base_dir / "dados_pacientes.csv"
            csv_path.write_text(
                "nome,ddd,telefone,rua,numero,bairro,cidade,estado,cep,consentimento_lgpd,servico_status,servico_ativo,acompanhantes\n"
                "PACIENTE REIDRATADO,11,988887777,Rua Volta,200,Centro,Sao Paulo,SP,02000-000,1,ativo,1,0\n",
                encoding="utf-8",
            )

            self.assertFalse(
                Paciente.objects.filter(nome="PACIENTE REIDRATADO").exists()
            )
            with override_settings(BASE_DIR=base_dir):
                response = self.client.get(
                    reverse("transporte_pacientes:cadastrar_paciente"),
                    **_secure_request_kwargs(),
                )

            self.assertEqual(response.status_code, 200)
            self.assertTrue(
                Paciente.objects.filter(nome="PACIENTE REIDRATADO").exists()
            )
