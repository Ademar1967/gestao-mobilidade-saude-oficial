# PowerShell script para automatizar ajuste de branch principal e push para o GitHub
# Salve como ajustar_branch_git.ps1 e execute no terminal PowerShell

# Caminho do arquivo de lock do git
$lockFile = "..\.git\index.lock"

# Remove o arquivo de lock se existir
if (Test-Path $lockFile) {
    Remove-Item $lockFile -Force
    Write-Host "Arquivo de lock removido."
}

# Busca branches remotas
$remoteBranches = git branch -r

if ($remoteBranches -match "origin/main") {
    $branch = "main"
} elseif ($remoteBranches -match "origin/master") {
    $branch = "master"
} else {
    $branch = "main"
    git checkout -b main
    git push -u origin main
    Write-Host "Branch main criada e enviada para o remoto."
    exit
}

# Troca para a branch correta
Write-Host "Trocando para a branch $branch..."
git checkout $branch

# Faz merge da backup-formulario se existir
$hasBackup = git branch --list backup-formulario
if ($hasBackup) {
    Write-Host "Fazendo merge da backup-formulario..."
    git merge backup-formulario
}

# Faz pull para unir histórico local e remoto
Write-Host "Sincronizando histórico local e remoto..."
git pull origin $branch --allow-unrelated-histories

# Sobe para o GitHub
Write-Host "Enviando branch $branch para o GitHub..."
git push origin $branch

Write-Host "Processo finalizado! Branch ativa: $branch"