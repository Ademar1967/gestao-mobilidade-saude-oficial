from django.shortcuts import redirect
from django.contrib import messages
from .models import Condutor

def excluir_selecionados_condutor(request):
    if request.method == 'POST':
        ids = request.POST.getlist('condutor_ids')
        if ids:
            Condutor.objects.filter(id__in=ids).delete()
            messages.success(request, f'{len(ids)} condutor(es) selecionado(s) foram excluídos.')
        else:
            messages.warning(request, 'Nenhum condutor selecionado para exclusão.')
    return redirect('transporte_pacientes:cadastrar_condutor')
