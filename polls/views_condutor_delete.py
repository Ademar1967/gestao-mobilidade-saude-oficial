from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from .models import Condutor

def excluir_condutor(request, condutor_id):
    if request.method == 'POST':
        condutor = get_object_or_404(Condutor, id=condutor_id)
        condutor.delete()
        messages.success(request, 'Condutor excluído com sucesso!')
    return redirect('transporte_pacientes:cadastrar_condutor')
