from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from polls.forms import TransporteForm
from polls.models import Clinica, Condutor, Paciente, Transporte, Veiculo
from polls.views_mapa_operacional import (
    _blocos_espelhados,
    _linha_from_paciente,
    _metadata_viagem_bloco,
    _preencher_destino_compartilhado_em_bloco,
)


class PacienteModelTest(TestCase):
    def test_fluxo_lote_mantem_sequencia_de_viagem_e_bloco_na_mesma_pagina(self):
        user = get_user_model().objects.create_user(username="tester_fluxo", password="123")
        self.client.force_login(user)

        paciente = Paciente.objects.create(nome="Paciente Fluxo", telefone="11999999999")
        veiculo = Veiculo.objects.create(tipo_veiculo="ambulancia", patrimonio="AMB-001", lotacao=4)
        condutor = Condutor.objects.create(nome="Condutor Fluxo")

        session = self.client.session
        session["paciente_ids_lote"] = [str(paciente.id)]
        session["fluxo_lote"] = {"viagem_atual": 1, "bloco_atual": 1}
        session.save()

        response = self.client.post(
            reverse("transporte_pacientes:cadastrar_transporte_lote"),
            {
                "paciente_ids_lote": [str(paciente.id)],
                "pacientes": [str(paciente.id)],
                "modo_lote": "misto",
                "veiculo": str(veiculo.id),
                "condutor": str(condutor.id),
                "data_transporte": "2026-08-20",
                "tipo_transporte": "CONSULTA",
                "numero_viagem": "1",
                "numero_bloco": "1",
                "clinica_1": "",
                "clinica_manual_1": "Clínica Fluxo",
                "forcar_duplicado": "0",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session["fluxo_lote"]["viagem_atual"], 2)
        self.assertEqual(self.client.session["fluxo_lote"]["bloco_atual"], 2)

        response_get = self.client.get(reverse("transporte_pacientes:cadastrar_transporte_lote"))
        self.assertEqual(response_get.status_code, 200)
        self.assertEqual(response_get.context["numero_viagem"], 2)
        self.assertEqual(response_get.context["numero_bloco"], 2)

    def test_veiculo_manual_ambiguuo_nao_deve_virar_van_automaticamente(self):
        paciente = Paciente.objects.create(nome="Paciente Ambíguo", telefone="11999999999")
        form = TransporteForm(
            data={
                "paciente": paciente.pk,
                "data_transporte": "2026-08-20",
                "veiculo_livre": "AMBULANCIA 01",
                "tipo_transporte": "CONSULTA",
            }
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        veiculo = form.cleaned_data["veiculo"]
        self.assertEqual(veiculo.tipo_veiculo, "ambulancia")
        self.assertEqual(veiculo.patrimonio, "AMBULANCIA 01")
        self.assertFalse(veiculo.placa)

        form_van = TransporteForm(
            data={
                "paciente": paciente.pk,
                "data_transporte": "2026-08-20",
                "veiculo_livre": "ABC-1234",
                "tipo_transporte": "CONSULTA",
            }
        )

        self.assertTrue(form_van.is_valid(), form_van.errors.as_json())
        veiculo_van = form_van.cleaned_data["veiculo"]
        self.assertEqual(veiculo_van.tipo_veiculo, "van")
        self.assertEqual(veiculo_van.placa, "ABC-1234")

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

    def test_impressao_preserva_ordem_numerica_dos_pacientes_no_bloco(self):
        user = get_user_model().objects.create_user(username="tester_ordem", password="123")
        self.client.force_login(user)

        paciente_z = Paciente.objects.create(nome="Paciente Zulu", telefone="1111")
        paciente_a = Paciente.objects.create(nome="Paciente Alpha", telefone="2222")
        paciente_m = Paciente.objects.create(nome="Paciente Médio", telefone="3333")

        for paciente in [paciente_z, paciente_a, paciente_m]:
            Transporte.objects.create(
                paciente=paciente,
                data_transporte="2026-08-02",
            )

        response = self.client.get(
            "/mapas-viagem/imprimir/",
            {
                "data": "2026-08-02",
                "origem": "prefeitura",
                "empresa": "PREFEITURA",
                "numero_viagem": "1a Viagem",
            },
        )

        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        self.assertIn("<th style=\"width:24px;\">ID</th>", html)
        self.assertIn(f">{paciente_z.id}</td>", html)
        self.assertIn(f">{paciente_a.id}</td>", html)
        self.assertIn(f">{paciente_m.id}</td>", html)

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

    def test_linha_de_impressao_remove_caractere_invalido_sem_perder_texto(self):
        paciente = Paciente.objects.create(
            nome="Paciente Especial",
            rua="Rua da Igreja",
            bairro="Centro",
        )
        clinica = Clinica.objects.create(
            nome="HOSPITAL SAGRADA FAMILIA � Maua",
            endereco="Rua do Hospital �",
            bairro="Maua",
            cidade="Sao Paulo",
        )

        linha = _linha_from_paciente(paciente, 1, None, clinica_fallback=clinica)

        self.assertNotIn("�", linha["destino"])
        self.assertNotIn("�", linha["endereco_clinica"])
        self.assertIn("HOSPITAL SAGRADA FAMILIA", linha["destino"])
        self.assertIn("Maua", linha["destino"])

    def test_linha_de_impressao_exibe_numero_real_de_acompanhantes_no_campo_ac(self):
        paciente = Paciente.objects.create(
            nome="Paciente Acompanhado",
            acompanhantes=2,
            rua="Rua da Igreja",
            bairro="Centro",
        )

        linha = _linha_from_paciente(paciente, 1, None)

        self.assertEqual(linha["acompanhante_marca"], "2")
        self.assertEqual(linha["acompanhantes"], 2)

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

    def test_metadata_de_bloco_organiza_viagem_e_bloco_com_separacao_entre_grupos(self):
        blocos = [
            {"linhas": [], "vazios": []},
            {"linhas": [], "vazios": []},
        ]

        blocos = _metadata_viagem_bloco(blocos, "2a Viagem")

        self.assertEqual(blocos[0]["trip_num"], 2)
        self.assertEqual(blocos[0]["bloco_num"], 1)
        self.assertEqual(blocos[0]["label"], "VIAGEM 2 — BLOCO 1")
        self.assertEqual(blocos[1]["label"], "VIAGEM 2 — BLOCO 2")

        self.assertFalse(blocos[0]["mostrar_separador_antes"])
        self.assertTrue(blocos[1]["mostrar_separador_antes"])

    def test_ordem_das_linhas_reinicia_por_viagem_ao_agrupamento(self):
        linhas = [
            {"paciente_id": 1, "acompanhantes": 0, "data_transporte": "2026-08-02", "veiculo_id": 10, "condutor_id": 21},
            {"paciente_id": 2, "acompanhantes": 0, "data_transporte": "2026-08-02", "veiculo_id": 10, "condutor_id": 21},
            {"paciente_id": 3, "acompanhantes": 0, "data_transporte": "2026-08-02", "veiculo_id": 11, "condutor_id": 22},
            {"paciente_id": 4, "acompanhantes": 0, "data_transporte": "2026-08-02", "veiculo_id": 11, "condutor_id": 22},
        ]

        blocos = _blocos_espelhados(linhas, 50)
        ordens = []
        for bloco in blocos:
            for linha in bloco["linhas"]:
                if not linha.get("separador"):
                    ordens.append(linha["ordem"])

        self.assertEqual(ordens, [1, 2, 1, 2])

    def test_linhas_de_viagens_distintas_na_mesma_data_sao_agrupadas_em_fluxo_continuo(self):
        condutor_1 = {"id": 1, "nome": "Motorista A"}
        condutor_2 = {"id": 2, "nome": "Motorista B"}
        veiculo_1 = {"id": 10, "placa": "ABC-1234"}
        veiculo_2 = {"id": 11, "placa": "XYZ-9876"}

        linhas = [
            {"paciente_id": 1, "acompanhantes": 0, "data_transporte": "2026-08-02", "veiculo_id": veiculo_1["id"], "condutor_id": condutor_1["id"]},
            {"paciente_id": 2, "acompanhantes": 0, "data_transporte": "2026-08-02", "veiculo_id": veiculo_2["id"], "condutor_id": condutor_2["id"]},
        ]

        blocos = _blocos_espelhados(linhas, 50)

        self.assertEqual(len(blocos), 2)
        self.assertEqual(blocos[0]["trip_num"], 1)
        self.assertEqual(blocos[0]["bloco_num"], 1)
        self.assertEqual(blocos[1]["trip_num"], 2)
        self.assertEqual(blocos[1]["bloco_num"], 2)
        self.assertEqual(blocos[0]["label"], "VIAGEM 1 — BLOCO 1")
        self.assertEqual(blocos[1]["label"], "VIAGEM 2 — BLOCO 2")


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

    def test_formulario_principal_mostra_feedback_de_sucesso_apos_salvar(self):
        response = self.client.post(
            reverse("transporte_pacientes:cadastrar_paciente"),
            {
                "nome": "Paciente Principal Fluxo",
                "rua": "Rua Teste",
                "numero": "11",
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
        self.assertIn("Cadastro salvo com sucesso. Formulario reiniciado para novo paciente.", html)

    def test_lote_exibe_status_visual_de_pacientes_alocados_e_pendentes(self):
        user = get_user_model().objects.create_user(username="tester_lote_status", password="123")
        self.client.force_login(user)

        paciente_alocado = Paciente.objects.create(
            nome="Paciente Alocado",
            rua="Rua Teste",
            numero="10",
            bairro="Centro",
            cidade="Sao Paulo",
            servico_status="ativo",
        )
        paciente_pendente = Paciente.objects.create(
            nome="Paciente Pendente",
            rua="Rua Teste",
            numero="11",
            bairro="Centro",
            cidade="Sao Paulo",
            servico_status="ativo",
        )
        Transporte.objects.create(
            paciente=paciente_alocado,
            data_transporte=date.today(),
            tipo_transporte="CONSULTA",
        )

        response = self.client.get(
            reverse("transporte_pacientes:cadastrar_transporte_lote"),
            {
                "paciente_ids": f"{paciente_alocado.id},{paciente_pendente.id}",
                "data_transporte": date.today().isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8", errors="ignore")
        self.assertIn("status-alocado", html)
        self.assertIn("status-pendente", html)
        self.assertIn("Paciente Alocado", html)
        self.assertIn("Paciente Pendente", html)

    def test_cadastro_em_lote_mantem_fluxo_aberto_apos_salvar(self):
        user = get_user_model().objects.create_user(username="tester_lote", password="123")
        self.client.force_login(user)

        paciente = Paciente.objects.create(
            nome="Paciente Lote Fluxo",
            rua="Rua Teste",
            numero="99",
            bairro="Centro",
            cidade="Sao Paulo",
            servico_status="ativo",
        )
        veiculo = Veiculo.objects.create(tipo_veiculo="van", placa="ABC-1234", lotacao=10)
        condutor = Condutor.objects.create(nome="Condutor Fluxo")

        response = self.client.post(
            reverse("transporte_pacientes:cadastrar_transporte_lote"),
            {
                "pacientes": [str(paciente.id)],
                "modo_lote": "misto",
                "veiculo": str(veiculo.id),
                "condutor": str(condutor.id),
                "tipo_transporte": "CONSULTA",
                "data_transporte": date.today().isoformat(),
                f"clinica_manual_{paciente.id}": "Hospital Teste",
                "forcar_excesso_lotacao": "0",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "salvo com sucesso")
        self.assertContains(response, "continue alocando")
        self.assertContains(response, reverse("transporte_pacientes:cadastrar_transporte_lote"))
        self.assertContains(response, "Paciente Lote Fluxo")
