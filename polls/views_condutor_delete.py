from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from .models import Condutor

def excluir_condutor(request, condutor_id):
    if request.method == 'POST':
        condutor = get_object_or_404(Condutor, id=condutor_id)
        condutor.delete()
        messages.success(request, 'Condutor excluído com sucesso!')
    return redirect('transporte_pacientes:cadastrar_condutor')


def excluir_selecionados_condutor(request):
    if request.method == 'POST':
        ids = request.POST.getlist('condutor_ids')
        if ids:
            Condutor.objects.filter(id__in=ids).delete()
            messages.success(request, f'{len(ids)} condutor(es) excluído(s) com sucesso!')
        else:
            messages.warning(request, 'Nenhum condutor selecionado para exclusão.')
    return redirect('transporte_pacientes:cadastrar_condutor')
