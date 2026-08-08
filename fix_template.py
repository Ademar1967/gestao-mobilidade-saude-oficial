# -*- coding: utf-8 -*-
"""Reconstrói o início corrompido do template cadastrar_paciente_simples.html."""

path = "polls/templates/transporte_pacientes/cadastrar_paciente_simples.html"
lines = open(path, encoding="utf-8").readlines()

# Mantém da linha 94 em diante (o conteúdo válido)
resto = "".join(lines[93:])

novo_inicio = """\
{% extends 'base.html' %}
{% load static %}

{% block content %}
<div class="container mt-3 mb-5">
  <div class="card border-0 mb-3">
    <div class="card-body p-3 p-md-4">

      <form method="post" id="form-cadastro-rapido">
        {% csrf_token %}

        <div class="d-flex flex-wrap gap-2 justify-content-between align-items-start mb-3" id="cabecalho-ficha-operacional">
          <div>
            <h5 class="mb-0 fw-bold">F.A. Remocoes Eletivas</h5>
            <small class="text-muted">Prefeitura de Mogi das Cruzes &mdash; Secretaria Municipal de Saude</small>
          </div>
          <div class="d-flex gap-2 align-items-center">
            <button type="button" class="btn btn-outline-secondary btn-sm no-print" onclick="window.print()">
              <i class="bi bi-printer me-1"></i> Imprimir
            </button>
          </div>
        </div>

        <div class="row g-2 mb-2">
          <div class="col-md-3 campo-item">
            <div class="campo-inline">
              <label for="{{ form.status.id_for_label }}" class="campo-inline-label">{{ form.status.label }}</label>
              <div class="campo-inline-control-wrap">
                {{ form.status }}
              </div>
            </div>
            {% if form.status.errors %}<div class="text-danger small">{{ form.status.errors }}</div>{% endif %}
          </div>
          <div class="col-md-3 campo-item">
            <div class="campo-inline">
              <label for="{{ form.horario_consulta.id_for_label }}" class="campo-inline-label">{{ form.horario_consulta.label }}</label>
              <div class="campo-inline-control-wrap">
                {{ form.horario_consulta }}
              </div>
            </div>
            {% if form.horario_consulta.errors %}<div class="text-danger small">{{ form.horario_consulta.errors }}</div>{% endif %}
          </div>
        </div>

        <fieldset class="ficha-box p-3 mb-3">
          <legend class="ficha-legend">Dados Pessoais</legend>
          <table class="ficha-tabela-dados">
            <tbody>
              <tr>
                <td class="ficha-celula ficha-celula-nome">
                  <div class="ficha-campo">
                    <label for="{{ form.nome.id_for_label }}">{{ form.nome.label }}</label>
                    {{ form.nome }}
                  </div>
"""

conteudo_final = novo_inicio + resto
open(path, "w", encoding="utf-8").write(conteudo_final)
print(f"Arquivo reconstruido: {conteudo_final.count(chr(10))} linhas")
