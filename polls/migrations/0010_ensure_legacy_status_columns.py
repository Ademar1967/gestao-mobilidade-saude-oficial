from django.db import migrations


def ensure_legacy_status_columns(apps, schema_editor):
    table_name = 'polls_paciente'

    with schema_editor.connection.cursor() as cursor:
        columns = {
            row[1]: row
            for row in cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
        }

        if 'data_inativacao' not in columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN data_inativacao datetime NULL")

        if 'motivo_inativacao' not in columns:
            cursor.execute(
                f"ALTER TABLE {table_name} ADD COLUMN motivo_inativacao varchar(30) NOT NULL DEFAULT ''"
            )

        if 'observacao_inativacao' not in columns:
            cursor.execute(
                f"ALTER TABLE {table_name} ADD COLUMN observacao_inativacao TEXT NOT NULL DEFAULT ''"
            )

        if 'servico_ativo' not in columns:
            cursor.execute(
                f"ALTER TABLE {table_name} ADD COLUMN servico_ativo bool NOT NULL DEFAULT 1"
            )

        cursor.execute(
            f"UPDATE {table_name} SET servico_ativo=0 WHERE servico_status IN ('suspenso', 'encerrado')"
        )
        cursor.execute(
            f"UPDATE {table_name} SET servico_ativo=1 WHERE servico_status='ativo'"
        )
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS polls_paciente_servico_ativo_idx ON {table_name}(servico_ativo)"
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0009_backfill_servico_status'),
    ]

    operations = [
        migrations.RunPython(ensure_legacy_status_columns, noop_reverse),
    ]
