param(
    [Parameter(Mandatory = $true)]
    [string]$CommitMessage,

    [switch]$Push,

    [switch]$SkipTests,

    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

function Assert-LastExitCode {
    param([string]$StepName)
    if ($LASTEXITCODE -ne 0) {
        throw "Falha na etapa: $StepName"
    }
}

function Get-NormalizedPath {
    param([string]$PathText)
    $p = $PathText.Trim()
    if ($p -match " -> ") {
        $p = ($p -split " -> ")[-1]
    }
    return ($p -replace "\\", "/")
}

# Garante que estamos em um repositorio git
& git rev-parse --is-inside-work-tree | Out-Null
Assert-LastExitCode "git rev-parse --is-inside-work-tree"
$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$allowDirtyPaths = @(
    ".vscode/settings.json",
    "transporte_django/settings.py",
    "transporte_django/management/commands/create_admin.py"
)

Write-Host "[1/6] Lendo alteracoes locais..." -ForegroundColor Cyan
$statusLines = git status --porcelain
if ($LASTEXITCODE -ne 0) {
    throw "Nao foi possivel ler git status --porcelain"
}

if (-not $statusLines -or $statusLines.Count -eq 0) {
    Write-Host "Nenhuma alteracao encontrada para release." -ForegroundColor Yellow
    exit 0
}

$releaseCandidates = @()
foreach ($line in $statusLines) {
    if ([string]::IsNullOrWhiteSpace($line) -or $line.Length -lt 4) {
        continue
    }

    $statusCode = $line.Substring(0, 2).Trim()
    $rawPath = $line.Substring(3)
    $path = Get-NormalizedPath -PathText $rawPath

    if ($allowDirtyPaths -contains $path) {
        continue
    }

    $releaseCandidates += [PSCustomObject]@{
        Status = $statusCode
        Path   = $path
    }
}

$uniqueCandidates = $releaseCandidates | Sort-Object Path -Unique

if (-not $uniqueCandidates -or $uniqueCandidates.Count -eq 0) {
    Write-Host "So existem alteracoes locais permitidas (settings/.vscode/create_admin). Nada para release." -ForegroundColor Yellow
    exit 0
}

Write-Host "[2/6] Arquivos que entrarao no release:" -ForegroundColor Cyan
$uniqueCandidates | Format-Table -AutoSize

Write-Host "[3/6] Executando validacao Django (manage.py check)..." -ForegroundColor Cyan
$pythonExe = ".venv/Scripts/python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

& $pythonExe manage.py check
if ($LASTEXITCODE -ne 0) {
    throw "Falha no manage.py check. Release cancelado."
}

if (-not $SkipTests.IsPresent) {
    Write-Host "[4/7] Executando testes automatizados (manage.py test)..." -ForegroundColor Cyan
    & $pythonExe manage.py test
    if ($LASTEXITCODE -ne 0) {
        throw "Falha no manage.py test. Release cancelado."
    }
} else {
    Write-Host "[4/7] Testes pulados via -SkipTests." -ForegroundColor Yellow
}

Write-Host "[5/7] Preparando stage apenas dos arquivos do release..." -ForegroundColor Cyan
$pathsToAdd = $uniqueCandidates.Path

# Limpa somente o indice (nao altera arquivos locais)
& git reset
Assert-LastExitCode "git reset"

& git add -- @pathsToAdd
Assert-LastExitCode "git add -- <arquivos>"

$stagedFiles = git diff --cached --name-only
if (-not $stagedFiles) {
    throw "Nenhum arquivo ficou staged. Release cancelado."
}

Write-Host "[6/7] Arquivos staged para commit:" -ForegroundColor Cyan
$stagedFiles | ForEach-Object { Write-Host " - $_" }

$confirmCommit = Read-Host "Digite SIM para confirmar o commit"
if ($confirmCommit -ne "SIM") {
    Write-Host "Commit cancelado pelo usuario." -ForegroundColor Yellow
    exit 1
}

& git commit -m $CommitMessage
Assert-LastExitCode "git commit"

Write-Host "[7/7] Commit concluido com sucesso." -ForegroundColor Green

if ($Push.IsPresent) {
    Write-Host "Arquivos do ultimo commit:" -ForegroundColor Cyan
    & git show --name-only --pretty=format:"" HEAD

    $confirmPush = Read-Host "Digite PUSH para enviar para origin/$Branch"
    if ($confirmPush -ne "PUSH") {
        Write-Host "Push cancelado pelo usuario." -ForegroundColor Yellow
        exit 1
    }

    & git push origin $Branch
    Assert-LastExitCode "git push origin $Branch"
    Write-Host "Push concluido para origin/$Branch." -ForegroundColor Green
} else {
    Write-Host "Push nao executado. Use: .\\scripts\\release_seguro.ps1 -CommitMessage \"...\" -Push" -ForegroundColor Yellow
}
