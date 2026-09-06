import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transporte_django.settings')
import django
django.setup()
from django.test import Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from polls.models import Paciente, Veiculo, Condutor, Transporte
from datetime import date

User = get_user_model()
User.objects.filter(username='tmp_lote_probe7').delete()
Paciente.objects.all().delete(); Veiculo.objects.all().delete(); Condutor.objects.all().delete(); Transporte.objects.all().delete()
user = User.objects.create_user(username='tmp_lote_probe7', password='123')
with override_settings(ALLOWED_HOSTS=['testserver']):
    client = Client(HTTP_HOST='testserver')
    client.force_login(user)
    p = Paciente.objects.create(nome='Paciente Lote Fluxo', rua='Rua Teste', numero='99', bairro='Centro', cidade='Sao Paulo', servico_status='ativo')
    v = Veiculo.objects.create(tipo_veiculo='van', placa='ABC-1234', lotacao=10)
    c = Condutor.objects.create(nome='Condutor Fluxo')
    resp = client.post(reverse('transporte_pacientes:cadastrar_transporte_lote'), {
        'pacientes': [str(p.id)],
        'modo_lote': 'misto',
        'veiculo': str(v.id),
        'condutor': str(c.id),
        'tipo_transporte': 'CONSULTA',
        'data_transporte': date.today().isoformat(),
        'clinica_manual_' + str(p.id): 'Hospital Teste',
        'forcar_excesso_lotacao': '0',
    }, follow=True)
    print('status', resp.status_code)
    print('redirect_chain', resp.redirect_chain)
    print('transportes', Transporte.objects.count())
    if resp.context:
        print('context keys', list(resp.context.keys())[:20])
        print('messages', [str(m) for m in get_messages(resp.wsgi_request)])
        if 'form' in resp.context:
            print('form errors', resp.context['form'].errors)
            print('is_bound', resp.context['form'].is_bound)
    text = resp.content.decode('utf-8', 'ignore').lower()
    print('contains_success', 'salvo com sucesso' in text or 'salvos com sucesso' in text)
    print('contains_continue', 'continue alocando' in text or 'continuar alocando' in text)
    print(text[text.lower().find('preencha'):text.lower().find('preencha')+2000] if 'preencha' in text else text[:2000])
