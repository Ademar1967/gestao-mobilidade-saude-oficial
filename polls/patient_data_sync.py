from __future__ import annotations

import csv
from pathlib import Path

from django.conf import settings

from .models import Paciente

PATIENT_CSV_HEADER = [
    "nome",
    "cartao_sis",
    "idade",
    "peso",
    "rua",
    "numero",
    "bairro",
    "cidade",
    "estado",
    "cep",
    "endereco",
    "referencia",
    "ddd",
    "telefone",
    "tratamento",
    "oxigenio",
    "oxigenio_litros_min",
    "observacoes",
    "evolucao",
    "status",
    "maca",
    "cadeirante",
    "acompanhantes",
    "consentimento_lgpd",
    "horario_consulta",
    "servico_status",
    "servico_ativo",
    "motivo_inativacao",
    "observacao_inativacao",
    "latitude",
    "longitude",
]


def _base_dir() -> Path:
    return Path(settings.BASE_DIR)


def _csv_path() -> Path:
    return _base_dir() / "dados_pacientes.csv"


def _to_bool(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "t", "yes", "sim", "on"}


def _to_int(value: object, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default


def _row_value(row: dict[str, object], key: str) -> str:
    return str(row.get(key, "") or "").strip()


def sync_patient_data_csv() -> None:
    csv_path = _csv_path()
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    pacientes = Paciente.objects.order_by("id")
    with csv_path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.writer(fp)
        writer.writerow(PATIENT_CSV_HEADER)
        for p in pacientes:
            writer.writerow(
                [
                    p.nome or "",
                    p.cartao_sis or "",
                    p.idade if p.idade is not None else "",
                    p.peso if p.peso is not None else "",
                    p.rua or "",
                    p.numero or "",
                    p.bairro or "",
                    p.cidade or "",
                    p.estado or "",
                    p.cep or "",
                    p.endereco or "",
                    p.referencia or "",
                    p.ddd or "",
                    p.telefone or "",
                    p.tratamento or "",
                    "1" if p.oxigenio else "0",
                    p.oxigenio_litros_min if p.oxigenio_litros_min is not None else "",
                    p.observacoes or "",
                    p.evolucao or "",
                    p.status or "",
                    "1" if p.maca else "0",
                    "1" if p.cadeirante else "0",
                    p.acompanhantes if p.acompanhantes is not None else 0,
                    "1" if p.consentimento_lgpd else "0",
                    p.horario_consulta.isoformat() if p.horario_consulta else "",
                    p.servico_status or "ativo",
                    "1" if p.servico_ativo else "0",
                    p.motivo_inativacao or "",
                    p.observacao_inativacao or "",
                    p.latitude if p.latitude is not None else "",
                    p.longitude if p.longitude is not None else "",
                ]
            )


def seed_patients_from_csv_if_empty() -> None:
    if Paciente.objects.exists():
        return

    csv_path = _csv_path()
    if not csv_path.exists():
        return

    with csv_path.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            nome = _row_value(row, "nome")
            if not nome:
                continue

            defaults = {
                "cartao_sis": _row_value(row, "cartao_sis"),
                "idade": _to_int(_row_value(row, "idade"), default=0) or None,
                "peso": _row_value(row, "peso") or None,
                "rua": _row_value(row, "rua"),
                "numero": _row_value(row, "numero"),
                "bairro": _row_value(row, "bairro"),
                "cidade": _row_value(row, "cidade"),
                "estado": _row_value(row, "estado"),
                "cep": _row_value(row, "cep"),
                "endereco": _row_value(row, "endereco"),
                "referencia": _row_value(row, "referencia"),
                "ddd": _row_value(row, "ddd"),
                "telefone": _row_value(row, "telefone"),
                "tratamento": _row_value(row, "tratamento"),
                "oxigenio": _to_bool(row.get("oxigenio")),
                "oxigenio_litros_min": _row_value(row, "oxigenio_litros_min") or None,
                "observacoes": _row_value(row, "observacoes"),
                "evolucao": _row_value(row, "evolucao"),
                "status": _row_value(row, "status"),
                "maca": _to_bool(row.get("maca")),
                "cadeirante": _to_bool(row.get("cadeirante")),
                "acompanhantes": _to_int(_row_value(row, "acompanhantes"), default=0),
                "consentimento_lgpd": _to_bool(row.get("consentimento_lgpd")),
                "horario_consulta": _row_value(row, "horario_consulta") or None,
                "servico_status": _row_value(row, "servico_status") or "ativo",
                "servico_ativo": _to_bool(row.get("servico_ativo")),
                "motivo_inativacao": _row_value(row, "motivo_inativacao"),
                "observacao_inativacao": _row_value(row, "observacao_inativacao"),
                "latitude": _row_value(row, "latitude") or None,
                "longitude": _row_value(row, "longitude") or None,
            }

            ddd = defaults.get("ddd", "")
            telefone = defaults.get("telefone", "")
            Paciente.objects.update_or_create(
                nome=nome,
                ddd=ddd,
                telefone=telefone,
                defaults=defaults,
            )
