from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from polls.models import Clinica, Paciente, Transporte
from polls.views_mapa_operacional import (
    _linha_from_paciente,
    _preencher_destino_compartilhado_em_bloco,
)


class PacienteModelTest(TestCase):
    def test_cadastro_paciente_sem_cadeira_dobravel(self):
        paciente = Paciente.objects.create(
            nome="Teste Paciente",
            idade=30,
            peso=70.5,
            rua="Rua Teste",
            numero="123",
            bairro="Centro",
            cidade="São Paulo",
            estado="SP",
            telefone="11999999999",
        )
        self.assertIsNotNone(paciente.id)

    def test_linha_de_impressao_prioriza_telefone_do_paciente(self):
        paciente = Paciente.objects.create(
            nome="Paciente Impressão",
            ddd="11",
            telefone="99999-1111",
            rua="Rua do Paciente",
            numero="99",
            bairro="Centro",
        )
        clinica = Clinica.objects.create(
            nome="Hospital Teste",
            telefone="2222-3333",
        )
        transporte = Transporte.objects.create(
            paciente=paciente,
            clinica=clinica,
            data_transporte="2026-08-02",
        )

        linha = _linha_from_paciente(paciente, 1, transporte)

        self.assertEqual(linha["telefone"], "11 99999-1111")
        self.assertEqual(linha["destino"], "Hospital Teste")

    def test_impressao_gera_linha_para_cada_paciente_selecionado(self):
        user = get_user_model().objects.create_user(username="tester", password="123")
        self.client.force_login(user)

        clinica = Clinica.objects.create(
            nome="Hospital Teste",
            telefone="2222-3333",
            endereco="Rua A",
            bairro="Centro",
            cidade="São Paulo",
        )
        paciente_1 = Paciente.objects.create(nome="Paciente 1", telefone="1111")
        paciente_2 = Paciente.objects.create(nome="Paciente 2", telefone="2222")
        Transporte.objects.create(
            paciente=paciente_1,
            clinica=clinica,
            data_transporte="2026-08-02",
        )

        response = self.client.get(
            "/mapas-viagem/imprimir/",
            {
                "paciente_ids": f"{paciente_1.id},{paciente_2.id}",
                "data": "2026-08-02",
                "origem": "prefeitura",
                "empresa": "PREFEITURA",
                "numero_viagem": "1a Viagem",
            },
        )

        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        self.assertIn("Paciente 1", html)
        self.assertIn("Paciente 2", html)
        self.assertIn("Hospital Teste", html)
        self.assertIn("Rua A", html)

    def test_impressao_herda_destino_da_clinica_para_paciente_sem_transporte(self):
        user = get_user_model().objects.create_user(username="tester2", password="123")
        self.client.force_login(user)

        clinica = Clinica.objects.create(
            nome="Hospital Teste",
            telefone="2222-3333",
            endereco="Rua A",
            bairro="Centro",
            cidade="São Paulo",
        )
        paciente_1 = Paciente.objects.create(nome="Paciente 1", telefone="1111")
        paciente_2 = Paciente.objects.create(nome="Paciente 2", telefone="2222")
        Transporte.objects.create(
            paciente=paciente_1,
            clinica=clinica,
            data_transporte="2026-08-02",
        )

        response = self.client.get(
            "/mapas-viagem/imprimir/",
            {
                "paciente_ids": f"{paciente_1.id},{paciente_2.id}",
                "data": "2026-08-02",
                "origem": "prefeitura",
                "empresa": "PREFEITURA",
                "numero_viagem": "1a Viagem",
            },
        )

        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        self.assertGreaterEqual(html.count("Hospital Teste"), 2)
        self.assertGreaterEqual(html.count("Rua A"), 2)

    def test_linha_de_impressao_inclui_ponto_de_referencia_do_paciente(self):
        paciente = Paciente.objects.create(
            nome="Paciente Referencia",
            rua="Rua Referência",
            numero="10",
            bairro="Centro",
            referencia="Perto do posto",
        )

        linha = _linha_from_paciente(paciente, 1, None)

        self.assertEqual(linha["referencia"], "Perto do posto")

    def test_linha_de_impressao_popula_observacao_com_referencia_e_notas(self):
        paciente = Paciente.objects.create(
            nome="Paciente Observacao",
            referencia="Perto da igreja",
            observacoes="Necessita apoio",
        )
        transporte = Transporte.objects.create(
            paciente=paciente,
            data_transporte="2026-08-02",
            observacoes="Chegar cedo",
        )

        linha = _linha_from_paciente(paciente, 1, transporte)

        self.assertIn("Perto da igreja", linha["observacao"])
        self.assertIn("Necessita apoio", linha["observacao"])
        self.assertIn("Chegar cedo", linha["observacao"])

    def test_impressao_sinaliza_coluna_de_observacao_so_quando_houver_conteudo(self):
        user = get_user_model().objects.create_user(username="tester_obs", password="123")
        self.client.force_login(user)

        paciente = Paciente.objects.create(nome="Paciente Sem Obs")
        Transporte.objects.create(
            paciente=paciente,
            data_transporte="2026-08-02",
        )

        response = self.client.get(
            "/mapas-viagem/imprimir/",
            {
                "paciente_ids": str(paciente.id),
                "data": "2026-08-02",
                "origem": "prefeitura",
                "empresa": "PREFEITURA",
                "numero_viagem": "1a Viagem",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["blocos"][0]["mostrar_coluna_observacao"])

    def test_linha_de_impressao_calcula_idade_a_partir_da_data_de_nascimento(self):
        paciente = Paciente.objects.create(
            nome="Paciente Idade",
            data_nascimento=date(1990, 5, 15),
        )

        linha = _linha_from_paciente(paciente, 1, None)

        self.assertEqual(linha["idade"], "36")

    def test_bloco_de_impressao_preenche_destino_compartilhado_para_todas_as_linhas(self):
        clinica = Clinica.objects.create(
            nome="Hospital Compartilhado",
            endereco="Rua do Hospital",
            bairro="Centro",
            cidade="São Paulo",
        )
        paciente_1 = Paciente.objects.create(nome="Paciente A", telefone="1111")
        paciente_2 = Paciente.objects.create(nome="Paciente B", telefone="2222")

        bloco = {
            "linhas": [
                _linha_from_paciente(paciente_1, 1, None, clinica_fallback=clinica),
                _linha_from_paciente(paciente_2, 2, None, clinica_fallback=clinica),
            ]
        }

        _preencher_destino_compartilhado_em_bloco(bloco)

        self.assertEqual(bloco["linhas"][0]["destino"], "Hospital Compartilhado")
        self.assertEqual(bloco["linhas"][1]["destino"], "Hospital Compartilhado")
        self.assertIn("Rua do Hospital", bloco["linhas"][1]["endereco_clinica"])


class PacienteRouteRegressionTest(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="tester_routes", password="123")
        self.client.force_login(user)

    def test_paciente_principal_continua_abindo_o_formulario_completo(self):
        response = self.client.get(reverse("transporte_pacientes:cadastrar_paciente"))
        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8", errors="ignore")
        self.assertIn("Cadastro e Gerenciamento de Pacientes", html)
        self.assertNotIn("Abrir formulario completo", html)

    def test_formulario_simples_mostra_botao_do_completo_no_topo(self):
        response = self.client.get(
            reverse("transporte_pacientes:cadastrar_paciente_simples")
        )
        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8", errors="ignore")
        botao_pos = html.find("Abrir formulario completo")
        salvar_pos = html.find("Salvar ficha")

        self.assertNotEqual(botao_pos, -1)
        self.assertNotEqual(salvar_pos, -1)
        self.assertLess(botao_pos, salvar_pos)
        self.assertIn("/pacientes/cadastrar-completo/", html)

    def test_formulario_simples_mostra_sucesso_e_reinicia_para_novo_cadastro(self):
        response = self.client.post(
            reverse("transporte_pacientes:cadastrar_paciente_simples"),
            {
                "nome": "Paciente Fluxo Rapido",
                "rua": "Rua Teste",
                "numero": "10",
                "bairro": "Centro",
                "cidade": "Sao Paulo",
                "servico_status": "ativo",
                "acompanhantes": "0",
                "consentimento_lgpd": "on",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8", errors="ignore")
        self.assertIn("Paciente \"Paciente Fluxo Rapido\" cadastrado com sucesso!", html)
        self.assertFalse(response.context["form"].is_bound)
        self.assertIn('id="id_nome"', html)
