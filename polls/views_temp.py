def excluir_todas_clinicas(request):
    from django.http import JsonResponse
    from .models import Clinica

    if request.method == "POST":
        try:
            total = Clinica.objects.count()
            Clinica.objects.all().delete()
            return JsonResponse(
                {
                    "status": "sucesso",
                    "mensagem": f"{total} clínica(s) excluída(s) com sucesso",
                }
            )
        except Exception as e:
            return JsonResponse({"status": "erro", "mensagem": str(e)}, status=500)

    return JsonResponse(
        {"status": "erro", "mensagem": "Método não permitido. Use POST."}, status=405
    )
