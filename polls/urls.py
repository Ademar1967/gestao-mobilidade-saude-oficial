from . import views_condutor_delete_lote

from django.urls import path
from . import views
from . import views_condutor_delete
from .views import editar_paciente, login_view


app_name = 'transporte_pacientes'
urlpatterns = [
    # Webhook do WhatsApp via Twilio
    path('whatsapp/webhook/', views.whatsapp_webhook, name='whatsapp_webhook'),
    # Página aberta para visualizar mensagens recebidas do WhatsApp (teste)
    path('whatsapp/mensagens/', views.mensagens_whatsapp, name='mensagens_whatsapp'),
    # --- ROTAS DE TRANSPORTE ---
    # Cadastro e listagem de transportes integrando todas as entidades principais
    path('enfermagem/editar/<int:enfermagem_id>/', views.editar_enfermagem, name='editar_enfermagem'),
    path('veiculos/editar/<int:veiculo_id>/', views.editar_veiculo, name='editar_veiculo'),
    path('transportes/cadastrar/', views.cadastrar_transporte, name='cadastrar_transporte'),
    path('transportes/cadastrar-lote/', views.cadastrar_transporte_lote, name='cadastrar_transporte_lote'),
    path('transportes/', views.listar_transportes, name='listar_transportes'),
    path('transportes/excluir/<int:transporte_id>/', views.excluir_transporte, name='excluir_transporte'),
    path('api/pacientes/sugestoes/', views.buscar_pacientes_sugestoes, name='buscar_pacientes_sugestoes'),
    path('api/clinicas/sugestoes/', views.buscar_clinicas_sugestoes, name='buscar_clinicas_sugestoes'),
    path('api/condutores/sugestoes/', views.buscar_condutores_sugestoes, name='buscar_condutores_sugestoes'),
    path('api/enfermagem/sugestoes/', views.buscar_enfermagem_sugestoes, name='buscar_enfermagem_sugestoes'),
    path('api/clinica/<int:clinica_id>/', views.obter_dados_clinica, name='obter_dados_clinica'),
    path('api/veiculos/sugestoes/', views.buscar_veiculos_sugestoes, name='buscar_veiculos_sugestoes'),
    path('condutores/excluir_selecionados/', views_condutor_delete_lote.excluir_selecionados_condutor, name='excluir_selecionados_condutor'),
        path('enfermagem/excluir_selecionadas/', views.excluir_selecionadas_enfermagem, name='excluir_selecionadas_enfermagem'),
    path('enfermagem/cadastrar/', views.cadastrar_enfermagem, name='cadastrar_enfermagem'),
    path('enfermagem/excluir/<int:enfermagem_id>/', views.excluir_enfermagem, name='excluir_enfermagem'),
    path('clinicas/excluir_selecionadas/', views.excluir_selecionadas_clinicas, name='excluir_selecionadas_clinicas'),
    path('clinicas/excluir_todas/', views.excluir_todas_clinicas, name='excluir_todas_clinicas'),
    path('login/', login_view, name='login'),
    path('', views.home, name='home'),
    # Adicionado para garantir funcionamento do autocomplete de endereço no cadastro de clínica
    # Se quiser desfazer, basta remover esta linha
    path('autocomplete_endereco_unidade/', views.autocomplete_endereco_unidade, name='autocomplete_endereco_unidade'),
    path('pacientes/cadastrar/', views.cadastrar_paciente, name='cadastrar_paciente'),
    path('pacientes/arquivos-recebidos/', views.arquivos_recebidos_pacientes, name='arquivos_recebidos_pacientes'),
    path('veiculos/cadastrar/', views.cadastrar_veiculo, name='cadastrar_veiculo'),
    path('condutores/cadastrar/', views.cadastrar_condutor, name='cadastrar_condutor'),
    path('condutores/editar/<int:condutor_id>/', views.editar_condutor, name='editar_condutor'),
    path('condutores/excluir/<int:condutor_id>/', views_condutor_delete.excluir_condutor, name='excluir_condutor'),
    path('clinicas/cadastrar/', views.cadastrar_clinica, name='cadastrar_clinica'),
    path('clinicas/excluir/<int:clinica_id>/', views.excluir_clinica, name='excluir_clinica'),
    path('clinicas/corrigir/', views.corrigir_dados_clinica, name='corrigir_dados_clinica'),
    path('pacientes/exportar_excel/', views.exportar_pacientes_excel, name='exportar_pacientes_excel'),
    path('pacientes/exportar_csv/', views.exportar_pacientes_csv, name='exportar_pacientes_csv'),
    path('veiculos/exportar_excel/', views.exportar_veiculos_excel, name='exportar_veiculos_excel'),
    path('condutores/exportar_excel/', views.exportar_condutores_excel, name='exportar_condutores_excel'),
    path('clinicas/exportar_excel/', views.exportar_clinicas_excel, name='exportar_clinicas_excel'),
    path('pacientes/preview/', views.preview_pacientes, name='preview_pacientes'),
    path('clinicas/preview/', views.preview_clinicas, name='preview_clinicas'),
    path('condutores/preview/', views.preview_condutores, name='preview_condutores'),
    path('veiculos/preview/', views.preview_veiculos, name='preview_veiculos'),
    path('autocomplete/<str:field>/', views.autocomplete_field, name='autocomplete_field'),
    path('paciente/<int:pk>/editar/', editar_paciente, name='editar_paciente'),
    path('pacientes/buscar_editar/', views.buscar_editar_paciente, name='buscar_editar_paciente'),
    path('pacientes/excluir_ajax/', views.excluir_paciente_ajax, name='excluir_paciente_ajax'),
    path('pacientes/excluir_todos/', views.excluir_todos_pacientes, name='excluir_todos_pacientes'),
    path('pacientes/corrigir_dados/', views.corrigir_dados_pacientes, name='corrigir_dados_pacientes'),
    path('pacientes-json/', views.pacientes_json, name='pacientes_json'),
    path('mapa-pacientes/', views.mapa_pacientes, name='mapa_pacientes'),

]
