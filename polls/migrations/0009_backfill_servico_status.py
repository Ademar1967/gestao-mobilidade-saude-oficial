from django.db import migrations


def backfill_servico_status(apps, schema_editor):
    table_name = "polls_paciente"
    connection = schema_editor.connection
    introspection = connection.introspection

    def _get_columns(cursor):
        return {
            col.name for col in introspection.get_table_description(cursor, table_name)
        }

    with connection.cursor() as cursor:
        columns = _get_columns(cursor)

        # Em algumas bases legadas a coluna existe fisicamente; em outras não.
        if "servico_ativo" not in columns:
            cursor.execute(
                f"ALTER TABLE {table_name} ADD COLUMN servico_ativo bool NOT NULL DEFAULT TRUE"
            )

        columns = _get_columns(cursor)

        if "servico_ativo" in columns:
            cursor.execute(
                f"UPDATE {table_name} SET servico_status='ativo' WHERE servico_ativo IS TRUE"
            )
            cursor.execute(
                f"UPDATE {table_name} SET servico_status='encerrado' WHERE servico_ativo IS FALSE"
            )

        cursor.execute(
            f"UPDATE {table_name} SET servico_ativo=FALSE WHERE servico_status IN ('suspenso', 'encerrado')"
        )
        cursor.execute(
            f"UPDATE {table_name} SET servico_ativo=TRUE WHERE servico_status='ativo'"
        )


def noop_reverse(apps, schema_editor):
    # Mantém sem reversão para não perder o histórico operacional atual.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("polls", "0008_paciente_data_inativacao_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_servico_status, noop_reverse),
    ]
