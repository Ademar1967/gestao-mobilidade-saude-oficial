param([string]$arquivo)

$base = "C:\Users\elide\OneDrive\Desktop\codigos\gestao-mobilidade-saude-oficial_novo"

switch ($arquivo.ToLower()) {
    "urls"      { Get-Content "$base\polls\urls.py" }
    "views"     { Get-Content "$base\polls\views.py" }
    "template"  { Get-Content "$base\polls\templates\transporte_pacientes\cadastrar_paciente.html" }
    "simples"   { Get-Content "$base\polls\templates\transporte_pacientes\cadastrar_paciente_simples.html" }
    "models"    { Get-Content "$base\polls\models.py" }
    "settings"  { Get-Content "$base\transporte_django\settings.py" }
    "raiz"      { Get-Content "$base\transporte_django\urls.py" }
    "mapa"      { Get-Content "$PSScriptRoot\mapa.txt" }
    default {
        Write-Host ""
        Write-Host "  USO: .\referencia\ver.ps1 <nome>" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Opcoes disponiveis:" -ForegroundColor Cyan
        Write-Host "    urls      -> polls/urls.py"
        Write-Host "    views     -> polls/views.py"
        Write-Host "    template  -> cadastrar_paciente.html"
        Write-Host "    simples   -> cadastrar_paciente_simples.html"
        Write-Host "    models    -> polls/models.py"
        Write-Host "    settings  -> transporte_django/settings.py"
        Write-Host "    raiz      -> transporte_django/urls.py"
        Write-Host "    mapa      -> mostra este resumo"
        Write-Host ""
    }
}
