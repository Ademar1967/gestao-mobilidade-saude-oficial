from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from polls.models import Clinica, Veiculo


class AutocompleteProtecaoTest(TestCase):
    def test_exportacao_pacientes_exige_login(self):
        # Desloga o usuário
        self.client.logout()
        url = '/pacientes/exportar_csv/'
        resp = self.client.get(url)
        # Deve ser redirect (302) para login ou 401 para API
        self.assertIn(resp.status_code, [302, 401], "Exportação de pacientes deveria exigir autenticação!")
    def test_cookie_sessao_seguro(self):
        # Realiza login
        self.client.logout()
        login_url = reverse('login')
        resp = self.client.post(login_url, {'username': 'teste_autocomplete', 'password': 'segredo123'}, follow=True)
        # Procura o cookie de sessão
        session_cookie = None
        for c in resp.client.cookies.values():
            if c.key == 'sessionid':
                session_cookie = c
                break
        self.assertIsNotNone(session_cookie, 'Cookie de sessão não encontrado após login!')
        # Verifica flags de segurança
        self.assertTrue(session_cookie.get('httponly', False), 'Cookie de sessão deve ser HttpOnly!')
        self.assertTrue(session_cookie.get('secure', False), 'Cookie de sessão deve ser Secure!')
        self.assertIn(session_cookie.get('samesite', '').lower(), ['lax', 'strict'], 'Cookie de sessão deve ter SameSite Lax ou Strict!')

    def test_endpoints_sensiveis_exigem_login(self):
        # Desloga o usuário
        self.client.logout()

        # Endpoints sensíveis: autocomplete de pacientes e outros que retornam dados pessoais
        endpoints = [
            reverse("transporte_pacientes:buscar_pacientes_sugestoes"),
            # Adicione outros endpoints sensíveis se necessário
        ]
        for url in endpoints:
            resp = self.client.get(url, {"q": "Teste"})
            # Pode ser redirect (302) para login ou 401 para API
            self.assertIn(resp.status_code, [302, 401], f"Endpoint {url} deveria exigir autenticação!")

    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="teste_autocomplete",
            password="segredo123",
        )
        self.client.force_login(self.user)

        Veiculo.objects.create(
            tipo_veiculo="ambulancia",
            patrimonio="AMB-1234",
            placa="",
            lotacao=1,
        )
        Veiculo.objects.create(
            tipo_veiculo="van",
            patrimonio="VAN-IGNORADO",
            placa="ABC1D23",
            lotacao=12,
        )
        Clinica.objects.create(
            nome="Hospital Teste Centro",
            endereco="Rua Exemplo, 100",
            bairro="Centro",
            cidade="Sao Paulo",
            telefone="11999999999",
        )

    def test_pagina_transporte_contem_inicializacao_critica_autocomplete(self):
        response = self.client.get(reverse("transporte_pacientes:cadastrar_transporte"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8", errors="ignore")

        # Campos manuais criticos do autocomplete no formulario
        self.assertIn('id="id_veiculo_livre"', html)
        self.assertIn('id="id_clinica_manual"', html)

        # Inicializacao principal: veiculo via helper ajax e clinica via bloco dedicado
        self.assertIn("initAutocompleteAjax('id_veiculo_livre'", html)
        self.assertIn("var $input = jQuery('#id_clinica_manual')", html)
        self.assertIn("buscarEnderecoPorNome", html)
        self.assertIn("function nomeBase(", html)
        self.assertIn("split('—')", html)

        # Fallback nativo com datalist (camada de resiliencia)
        self.assertIn("initNativeAutocompleteFallback('id_veiculo_livre'", html)
        self.assertIn("initNativeAutocompleteFallback('id_clinica_manual'", html)

    def test_api_veiculos_sugestoes_retorna_resultados(self):
        response = self.client.get(
            reverse("transporte_pacientes:buscar_veiculos_sugestoes"),
            {"q": "AMB"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("sucesso"))
        self.assertGreaterEqual(len(data.get("resultados", [])), 1)

    def test_api_clinicas_sugestoes_retorna_resultados(self):
        response = self.client.get(
            reverse("transporte_pacientes:buscar_clinicas_sugestoes"),
            {"q": "Hosp"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("sucesso"))
        self.assertGreaterEqual(len(data.get("resultados", [])), 1)
