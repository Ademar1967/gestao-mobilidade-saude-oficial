from django import forms


class PacienteImportForm(forms.Form):
    arquivo = forms.FileField(label="Arquivo CSV ou Excel (.csv, .xlsx)", required=True)
