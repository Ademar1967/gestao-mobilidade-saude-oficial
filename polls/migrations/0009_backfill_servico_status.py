from django.db import migrations


def backfill_servico_status(apps, schema_editor):
    table_name = 'polls_paciente'

    with schema_editor.connection.cursor() as cursor:
        columns = {
            row[1]
            for row in cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
        }

        # Em algumas bases legadas a coluna existe fisicamente; em outras não.
        if 'servico_ativo' not in columns:
            cursor.execute(
                f"ALTER TABLE {table_name} ADD COLUMN servico_ativo bool NOT NULL DEFAULT 1"
            )

        columns = {
            row[1]
            for row in cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
        }

        if 'servico_ativo' in columns:
            cursor.execute(
                f"UPDATE {table_name} SET servico_status='ativo' WHERE servico_ativo=1"
            )
            cursor.execute(
                f"UPDATE {table_name} SET servico_status='encerrado' WHERE servico_ativo=0"
            )

        cursor.execute(
            f"UPDATE {table_name} SET servico_ativo=0 WHERE servico_status IN ('suspenso', 'encerrado')"
        )
        cursor.execute(
            f"UPDATE {table_name} SET servico_ativo=1 WHERE servico_status='ativo'"
        )


def noop_reverse(apps, schema_editor):
    # Mantém sem reversão para não perder o histórico operacional atual.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0008_paciente_data_inativacao_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_servico_status, noop_reverse),
    ]
