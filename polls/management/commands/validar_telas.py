from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.test import Client
from django.urls import reverse


class Command(BaseCommand):
    help = "Valida automaticamente as principais telas do sistema sem alterar dados."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            default="AMBULANCIA192",
            help="Usuario para autenticar no teste (default: AMBULANCIA192).",
        )
        parser.add_argument(
            "--create-user",
            action="store_true",
            help="Cria o usuario informado como superuser/staff caso nao exista.",
        )

    def handle(self, *args, **options):
        username = options["username"]
        create_user = options["create_user"]

        user = self._get_user(username=username, create_user=create_user)

        client = Client(HTTP_HOST="127.0.0.1", raise_request_exception=False)
        client.force_login(user)

        checks = []

        # 1) Configuracao de sessao esperada
        checks.append(
            (
                "Sessao em 8h",
                settings.SESSION_COOKIE_AGE == 28800,
                f"SESSION_COOKIE_AGE={settings.SESSION_COOKIE_AGE}",
            )
        )

        # 2) Login page publica
        login_response = client.get("/login/")
        login_ok = login_response.status_code == 200
        checks.append(("Tela de login", login_ok, f"status={login_response.status_code}"))

        # 3) Telas principais com aviso de template ativo
        template_routes = [
            ("cadastrar_paciente", "cadastrar_paciente.html"),
            ("cadastrar_transporte", "cadastrar_transporte.html"),
            ("cadastrar_transporte_lote", "cadastrar_transporte_lote.html"),
            ("listar_transportes", "listar_transportes.html"),
            ("mapa_pacientes", "mapa_pacientes.html"),
            ("cadastrar_clinica", "cadastrar_clinica.html"),
        ]

        for route_name, template_name in template_routes:
            ok, detail = self._check_route_contains(
                client=client,
                route_name=route_name,
                expected_strings=["Aviso de edição:", template_name],
            )
            checks.append((f"Aviso em {route_name}", ok, detail))

        # 4) Regras de rotulo no lote
        ok_lote, detail_lote = self._check_route_contains(
            client=client,
            route_name="cadastrar_transporte_lote",
            expected_strings=["Horário Saída", "(opcional)", "Horário Consulta"],
        )
        checks.append(("Rotulos de horario no lote", ok_lote, detail_lote))

        failed = [c for c in checks if not c[1]]

        self.stdout.write("\n=== Resultado da validacao automatica ===")
        for title, ok, detail in checks:
            prefix = "[OK]" if ok else "[ERRO]"
            self.stdout.write(f"{prefix} {title} - {detail}")

        if failed:
            raise CommandError(
                f"Validacao finalizada com {len(failed)} falha(s). Veja os itens [ERRO] acima."
            )

        self.stdout.write(self.style.SUCCESS("\nValidacao concluida: tudo certo."))

    def _get_user(self, username, create_user):
        User = get_user_model()
        user = User.objects.filter(username=username).first()
        if user:
            return user

        if not create_user:
            raise CommandError(
                f"Usuario '{username}' nao encontrado. Rode com --create-user para criar automaticamente."
            )

        user = User.objects.create_superuser(
            username=username,
            email="auto.validacao@local",
            password="trocar123",
        )
        self.stdout.write(
            self.style.WARNING(
                f"Usuario '{username}' criado automaticamente para validacao (senha temporaria: trocar123)."
            )
        )
        return user

    def _check_route_contains(self, client, route_name, expected_strings):
        url = reverse(f"transporte_pacientes:{route_name}")
        try:
            response = client.get(url)
        except Exception as exc:  # pragma: no cover - protecao extra para execucao manual
            return False, f"excecao={exc.__class__.__name__} url={url}"

        if response.status_code != 200:
            return False, f"status={response.status_code} url={url}"

        html = response.content.decode("utf-8", errors="ignore")
        missing = [s for s in expected_strings if s not in html]
        if missing:
            return False, f"faltando={missing} url={url}"

        return True, f"status=200 url={url}"
