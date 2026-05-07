param(
    [string]$RenderUrl = 'https://transporte-de-enfermos.onrender.com',
    [string]$CheckPath = '/login/',
    [int]$MaxMinutes = 12,
    [int]$PollSeconds = 8
)

$start = Get-Date
$maxSeconds = [Math]::Max(60, $MaxMinutes * 60)
$firstFailureSeen = $false
$stableOkCount = 0

$host.UI.RawUI.WindowTitle = 'Monitor de Deploy Render'
Write-Host ''
Write-Host 'Monitorando deploy do Render...' -ForegroundColor Cyan
Write-Host "URL: $RenderUrl$CheckPath" -ForegroundColor DarkGray
Write-Host ''

while ($true) {
    $elapsed = [int]((Get-Date) - $start).TotalSeconds
    $pct = [int]([Math]::Min(99, ($elapsed / [double]$maxSeconds) * 100))

    try {
        $resp = Invoke-WebRequest -Uri ($RenderUrl.TrimEnd('/') + $CheckPath) -Method Get -TimeoutSec 12 -ErrorAction Stop
        if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
            $stableOkCount += 1
            $statusText = "ONLINE (HTTP $($resp.StatusCode))"
        } else {
            $stableOkCount = 0
            $statusText = "Instavel (HTTP $($resp.StatusCode))"
        }
    } catch {
        $firstFailureSeen = $true
        $stableOkCount = 0
        $statusText = 'Aguardando subir...'
    }

    Write-Progress -Activity 'Deploy Render em andamento' -Status $statusText -PercentComplete $pct

    # Condicao de conclusao:
    # 1) vimos queda e depois voltou estavel; ou
    # 2) site estavel por alguns ciclos apos tempo minimo.
    if (($firstFailureSeen -and $stableOkCount -ge 3) -or ($elapsed -ge 90 -and $stableOkCount -ge 5)) {
        break
    }

    if ($elapsed -ge $maxSeconds) {
        break
    }

    Start-Sleep -Seconds $PollSeconds
}

Write-Progress -Activity 'Deploy Render em andamento' -Completed
$finalElapsed = [int]((Get-Date) - $start).TotalSeconds
Write-Host ''
if ($stableOkCount -ge 3) {
    Write-Host "Deploy aparentemente concluido em $finalElapsed segundos." -ForegroundColor Green
} else {
    Write-Host "Monitor finalizado apos $finalElapsed segundos. Confira o Render se ainda estiver publicando." -ForegroundColor Yellow
}
Write-Host ''
