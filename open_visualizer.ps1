# PowerShell script to open the visualizer studio
$htmlPath = Join-Path $PSScriptRoot "visualizer\index.html"
Write-Host "[Visualizer] Opening ITT 036 Interactive Studio: $htmlPath" -ForegroundColor Cyan
Start-Process $htmlPath
