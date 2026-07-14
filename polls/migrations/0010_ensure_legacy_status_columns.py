from django.db import migrations


def ensure_legacy_status_columns(apps, schema_editor):
    table_name = "polls_paciente"
    connection = schema_editor.connection
    introspection = connection.introspection

    def _get_columns(cursor):
        return {
            col.name for col in introspection.get_table_description(cursor, table_name)
        }

    with connection.cursor() as cursor:
        columns = _get_columns(cursor)

        if "data_inativacao" not in columns:
            cursor.execute(
                f"ALTER TABLE {table_name} ADD COLUMN data_inativacao timestamp NULL"
            )

        if "motivo_inativacao" not in columns:
            cursor.execute(
                f"ALTER TABLE {table_name} ADD COLUMN motivo_inativacao varchar(30) NOT NULL DEFAULT ''"
            )

        if "observacao_inativacao" not in columns:
            cursor.execute(
                f"ALTER TABLE {table_name} ADD COLUMN observacao_inativacao TEXT NOT NULL DEFAULT ''"
            )

        if "servico_ativo" not in columns:
            cursor.execute(
                f"ALTER TABLE {table_name} ADD COLUMN servico_ativo bool NOT NULL DEFAULT TRUE"
            )

        cursor.execute(
            f"UPDATE {table_name} SET servico_ativo=FALSE WHERE servico_status IN ('suspenso', 'encerrado')"
        )
        cursor.execute(
            f"UPDATE {table_name} SET servico_ativo=TRUE WHERE servico_status='ativo'"
        )
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS polls_paciente_servico_ativo_idx ON {table_name}(servico_ativo)"
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("polls", "0009_backfill_servico_status"),
    ]

    operations = [
        migrations.RunPython(ensure_legacy_status_columns, noop_reverse),
    ]
