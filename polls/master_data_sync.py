from __future__ import annotations

import csv
from pathlib import Path

from django.conf import settings

from .models import Clinica, Condutor, Enfermagem, Veiculo


def _base_dir() -> Path:
    return Path(settings.BASE_DIR)


def _write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.writer(fp)
        writer.writerow(header)
        writer.writerows(rows)


def sync_master_data_csvs() -> None:
    """Atualiza os CSVs-base usados para reidratacao de cadastros no startup."""
    base_dir = _base_dir()

    condutores_rows = [
        [nome]
        for nome in Condutor.objects.order_by("nome").values_list("nome", flat=True)
        if (nome or "").strip()
    ]
    _write_csv(base_dir / "condutores.csv", ["nome"], condutores_rows)

    enfermagem_rows = [
        [nome]
        for nome in Enfermagem.objects.order_by("nome").values_list("nome", flat=True)
        if (nome or "").strip()
    ]
    _write_csv(base_dir / "enfermagem.csv", ["nome"], enfermagem_rows)

    clinicas_rows = [
        [
            c.nome or "",
            c.endereco or "",
            c.bairro or "",
            c.cidade or "",
            c.telefone or "",
        ]
        for c in Clinica.objects.order_by("nome").only(
            "nome", "endereco", "bairro", "cidade", "telefone"
        )
    ]
    _write_csv(
        base_dir / "clinicas.csv",
        ["Nome", "Endereco", "Bairro", "Cidade", "Telefone"],
        clinicas_rows,
    )

    viaturas_rows = [
        [
            v.patrimonio or "",
            v.placa or "",
            v.tipo_veiculo or "ambulancia",
            v.lotacao if v.lotacao is not None else 1,
        ]
        for v in Veiculo.objects.order_by("id").only(
            "patrimonio", "placa", "tipo_veiculo", "lotacao"
        )
    ]
    _write_csv(
        base_dir / "viaturas.csv",
        ["patrimonio", "placa", "tipo_veiculo", "lotacao"],
        viaturas_rows,
    )
