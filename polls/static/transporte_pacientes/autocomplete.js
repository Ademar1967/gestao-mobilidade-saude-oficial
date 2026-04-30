// Autocomplete AJAX para cadastro de clinica por nome de hospital/unidade.
$(document).ready(function() {
  var nomeInput = $('#id_nome');
  var enderecoInput = $('#id_endereco_completo');

  if (!nomeInput.length || !enderecoInput.length || typeof nomeInput.autocomplete !== 'function') {
    return;
  }

  nomeInput.autocomplete({
    source: function(request, response) {
      $.getJSON('/autocomplete_endereco_unidade/', { term: request.term }, function(data) {
        response($.map(data || [], function(item) {
          return {
            label: item.label || '',
            value: item.label || '',  // Nome do hospital (exibido na autocomplete)
            nomeHospital: item.label || '',
            enderecoCompleto: item.value || '',  // Endereço completo
            logradouro: item.logradouro || '',
            numero: item.numero || '',
            cep: item.cep || ''
          };
        }));
      });
    },
    minLength: 2,
    select: function(event, ui) {
      // Preenche nome com label (nome do hospital)
      nomeInput.val(ui.item.label || '');
      // Preenche endereço completo com item.value (que vem do backend como endereço)
      enderecoInput.val(ui.item.enderecoCompleto || '');
      $('#id_logradouro').val(ui.item.logradouro || '');
      $('#id_numero').val(ui.item.numero || '');
      $('#id_cep').val(ui.item.cep || '');
      return false;
    },
    // Hook para forçar renderização correta
    open: function(event, ui) {
      // Ajusta a altura mínima de cada item
      var menu = $(this).autocomplete("widget");
      menu.css({
        "max-height": "350px",
        "overflow-y": "auto",
        "width": (nomeInput.width() + 30) + "px"
      });
      
      // Força altura mínima para cada item
      menu.find(".ui-menu-item").each(function() {
        $(this).css({
          "min-height": "32px",
          "height": "auto",
          "margin": "0",
          "padding": "0"
        });
        $(this).find(".ui-menu-item-wrapper").css({
          "padding": "8px 12px",
          "display": "block",
          "white-space": "normal",
          "word-wrap": "break-word"
        });
      });
    }
  });
});
