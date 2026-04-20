from .models import Clinica

def unidades_salvas(request):
    return {'unidades_salvas': Clinica.objects.all()}
