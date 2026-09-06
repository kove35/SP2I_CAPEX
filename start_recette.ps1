# start_recette.ps1
# Lancement reproductible de la recette locale SP2I CAPEX (V6 active).
# - Verifie PostgreSQL de test (conteneur + base + donnees synthetiques) SANS reconstruire.
# - Demarre backend FastAPI (:8000) et frontend Vite (:5173) s'ils ne sont pas deja actifs.
# - Affiche l'URL, les identifiants de recette et les chemins de logs.
# Refuse toute cible de production : seules les bases du conteneur isole sont utilisees.
#
# Usage :  powershell -ExecutionPolicy Bypass -File .\start_recette.ps1
param(
  [switch]$Stop  # arret des services backend/frontend de recette
)

$ErrorActionPreference = "Stop"
$Root = "C:\Users\Geoffrey\Documents\DEVELOPPEMENT\SP2I_CAPEX_RECIPE_FIXES"
$BackDir = Join-Path $Root "07_API_BACKEND"
$FrontDir = Join-Path $Root "08_FRONTEND"
$VenvPython = "C:\Users\Geoffrey\Documents\DEVELOPPEMENT\SP2I_CAPEX\.venv\Scripts\python.exe"
$BackLog = Join-Path $BackDir "recette_backend.log"
$BackErr = Join-Path $BackDir "recette_backend.err.log"
$FrontLog = Join-Path $FrontDir "recette_frontend.log"
$FrontErr = Join-Path $FrontDir "recette_frontend.err.log"
$Container = "sp2i_capex_test_pg"
$Db = "sp2i_capex_recipe"

function Test-Port([int]$Port) {
  try {
    (Invoke-WebRequest -Uri "http://127.0.0.1:$Port" -UseBasicParsing -TimeoutSec 2) | Out-Null
    return $true
  } catch { return $false }
}

function Start-Backend {
  $p = Start-Process -FilePath $VenvPython `
    -ArgumentList "tests\recette\_run_backend.py" `
    -WorkingDirectory $BackDir `
    -RedirectStandardOutput $BackLog -RedirectStandardError $BackErr -WindowStyle Hidden -PassThru
  Write-Output ("[recette] backend demarre (PID " + $p.Id + "), log: " + $BackLog)
}

function Start-Frontend {
  $env:VITE_SP2I_USE_V6_FINANCIALS = "true"
  $p = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c", "npm run dev -- --host 127.0.0.1 --port 5173" `
    -WorkingDirectory $FrontDir `
    -RedirectStandardOutput $FrontLog -RedirectStandardError $FrontErr -WindowStyle Hidden -PassThru
  Write-Output ("[recette] frontend demarre (PID " + $p.Id + "), log: " + $FrontLog)
}

if ($Stop) {
  Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "_run_backend.py|uvicorn app.main:app" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
  Get-CimInstance Win32_Process -Filter "Name='node.exe'" | Where-Object { $_.CommandLine -match "vite" -and $_.CommandLine -match "5173" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
  Write-Output "[recette] arret demande : backend/frontend stoppes."
  exit 0
}

# 1. PostgreSQL de test isole (aucune reconstruction)
$containerState = docker ps --filter "name=$Container" --format "{{.Status}}"
if (-not $containerState) { throw "Conteneur PostgreSQL $Container absent ou arrete. Demarrage impossible (aucune reconstruction automatique)." }
Write-Output ("[recette] PostgreSQL OK : " + $containerState)

$dbCount = (docker exec $Container psql -U user -d postgres -t -A -c "SELECT count(*) FROM pg_database WHERE datname='$Db';" | Out-String).Trim()
if ([int]$dbCount -lt 1) { throw "Base $Db absente. Donnees de recette non reconstruites par ce script." }
$userCount = (docker exec $Container psql -U user -d $Db -t -A -c "SELECT count(*) FROM users;" | Out-String).Trim()
if ([int]$userCount -lt 1) { throw "Base $Db sans compte de recette. Arret (aucune reconstruction)." }
Write-Output "[recette] donnees synthetiques presentes : $userCount compte(s). Aucune donnee de production utilisee."

# 2. Backend FastAPI
if (Test-Port 8000) { Write-Output "[recette] backend deja actif sur :8000 (reutilise)." }
else { Start-Backend; Start-Sleep -Seconds 8 }

# 3. Frontend Vite (V6 active)
if (Test-Port 5173) { Write-Output "[recette] frontend deja actif sur :5173 (reutilise)." }
else { Start-Frontend; Start-Sleep -Seconds 10 }

# 4. Recapitulatif
Write-Output ""
Write-Output "================ SP2I CAPEX - RECETTE LOCALE ================"
Write-Output "URL        : http://localhost:5173/"
Write-Output "API        : http://127.0.0.1:8000 (health OK attendu)"
Write-Output "Compte     : admin@recette.local / Admin123!  (synthetique, projets A/B/C/D)"
Write-Output "Logs       : backend  -> $BackLog (+ .err)"
Write-Output "             frontend -> $FrontLog (+ .err)"
Write-Output "Arret      : powershell -ExecutionPolicy Bypass -File .\start_recette.ps1 -Stop"
Write-Output "=============================================================="
