import csv
from datetime import date


def exportar_csv_com_data(queryset, campos, nome_arquivo):
    """
    Exporta um queryset Django para CSV, adicionando a data atual no rodapé.
    queryset: QuerySet do Django
    campos: lista de campos a exportar
    nome_arquivo: nome do arquivo CSV a ser salvo
    """
    with open(nome_arquivo, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(campos)
        for obj in queryset:
            writer.writerow([getattr(obj, campo, "") for campo in campos])
        writer.writerow([])
        writer.writerow([f"Planilha gerada em: {date.today().strftime('%d/%m/%Y')}"])
