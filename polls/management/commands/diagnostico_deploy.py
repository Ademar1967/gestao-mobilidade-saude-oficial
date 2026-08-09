import hashlib
import os
import platform
import re
import sys
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import get_template
from django.urls import reverse


class Command(BaseCommand):
    help = "Exibe diagnostico de deploy para facilitar investigacao no Render logs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Falha com erro se encontrar problema critico em templates/rotas.",
        )

    def handle(self, *args, **options):
        strict = bool(options.get("strict"))
        warnings = []

        self.stdout.write("[DEPLOY_DIAG] ===== INICIO =====")
        self.stdout.write(f"[DEPLOY_DIAG] CWD={os.getcwd()}")
        self.stdout.write(
            f"[DEPLOY_DIAG] PYTHON={sys.version.split()[0]} ({platform.python_implementation()})"
        )
        self.stdout.write(f"[DEPLOY_DIAG] EXECUTABLE={sys.executable}")

        import django  # import local para garantir leitura da versao ativa

        self.stdout.write(f"[DEPLOY_DIAG] DJANGO={django.get_version()}")
        self.stdout.write(
            f"[DEPLOY_DIAG] DJANGO_SETTINGS_MODULE={os.environ.get('DJANGO_SETTINGS_MODULE', '<nao definido>')}"
        )
        self.stdout.write(f"[DEPLOY_DIAG] DEBUG={settings.DEBUG}")
        self.stdout.write(f"[DEPLOY_DIAG] ALLOWED_HOSTS={settings.ALLOWED_HOSTS}")
        self.stdout.write(
            f"[DEPLOY_DIAG] CSRF_TRUSTED_ORIGINS={getattr(settings, 'CSRF_TRUSTED_ORIGINS', [])}"
        )

        app_cfg = apps.get_app_config("polls")
        self.stdout.write(
            "[DEPLOY_DIAG] APP polls "
            f"name={app_cfg.name} label={app_cfg.label} verbose_name={app_cfg.verbose_name}"
        )

        self._check_route("transporte_pacientes:cadastrar_paciente", warnings)
        self._check_route("transporte_pacientes:cadastrar_paciente_simples", warnings)

        template_specs = [
            (
                "transporte_pacientes/cadastrar_paciente.html",
                "Cadastro e Gerenciamento de Pacientes",
            ),
            (
                "transporte_pacientes/cadastrar_paciente_simples.html",
                "Horario",
            ),
        ]

        for tpl_name, required_text in template_specs:
            self._check_template(tpl_name, required_text, warnings)

        if warnings:
            self.stdout.write("[DEPLOY_DIAG] AVISOS:")
            for item in warnings:
                self.stdout.write(f"[DEPLOY_DIAG] - {item}")
        else:
            self.stdout.write("[DEPLOY_DIAG] Nenhum aviso detectado.")

        self.stdout.write("[DEPLOY_DIAG] ===== FIM =====")

        if strict and warnings:
            raise CommandError(
                f"Diagnostico encontrou {len(warnings)} alerta(s). Veja logs [DEPLOY_DIAG]."
            )

    def _check_route(self, route_name, warnings):
        try:
            url = reverse(route_name)
            self.stdout.write(f"[DEPLOY_DIAG] ROTA {route_name} -> {url}")
        except Exception as exc:  # pragma: no cover - diagnostico defensivo
            warnings.append(f"Nao foi possivel resolver rota {route_name}: {exc}")

    def _check_template(self, template_name, required_text, warnings):
        try:
            template = get_template(template_name)
            origin_name = getattr(getattr(template, "origin", None), "name", None)
        except Exception as exc:  # pragma: no cover - diagnostico defensivo
            warnings.append(f"Template ausente {template_name}: {exc}")
            return

        if not origin_name:
            warnings.append(f"Template sem origem resolvida: {template_name}")
            return

        template_path = Path(origin_name)
        if not template_path.exists():
            warnings.append(f"Arquivo de template nao encontrado: {origin_name}")
            return

        content = template_path.read_text(encoding="utf-8", errors="ignore")
        sha = hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()[:12]
        first_nonempty = ""
        for line in content.splitlines():
            if line.strip():
                first_nonempty = line.strip()
                break

        self.stdout.write(
            f"[DEPLOY_DIAG] TEMPLATE {template_name} path={template_path.name} sha12={sha}"
        )
        self.stdout.write(f"[DEPLOY_DIAG] TEMPLATE_FIRST_LINE {first_nonempty}")

        if "{% extends 'base.html' %}" not in first_nonempty:
            warnings.append(
                f"{template_name}: primeira linha util nao e extends base.html"
            )

        has_style_open = "<style" in content
        has_style_close = "</style>" in content
        self.stdout.write(
            f"[DEPLOY_DIAG] TEMPLATE_STYLE_TAGS open={has_style_open} close={has_style_close}"
        )
        if has_style_open and not has_style_close:
            warnings.append(f"{template_name}: bloco <style> sem fechamento </style>")

        if required_text not in content:
            warnings.append(
                f"{template_name}: texto esperado nao encontrado ({required_text})"
            )

        suspicious_pattern = re.search(
            r"\.ficha-campo-peso\s+\.input-group\s*\{[^}]*\}\s*Hor[áa]rio",
            content,
            flags=re.IGNORECASE | re.DOTALL,
        )
        self.stdout.write(
            "[DEPLOY_DIAG] TEMPLATE_SUSPECT_PATTERN="
            f"{'yes' if bool(suspicious_pattern) else 'no'}"
        )
        if suspicious_pattern:
            warnings.append(
                f"{template_name}: encontrado padrao suspeito de CSS vazando para texto"
            )
