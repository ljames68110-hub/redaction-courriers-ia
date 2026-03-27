# ============================================================
#  CourrierIA - Preparation cle USB
#  Lance ce script pour copier tout le necessaire sur une cle USB
#  Le PC destinataire n'aura PAS besoin d'internet
# ============================================================

$ErrorActionPreference = "Continue"

function Write-Step($msg) { Write-Host "" ; Write-Host "  > $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "  OK : $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  !! $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "  ERREUR : $msg" -ForegroundColor Red }

Clear-Host
Write-Host ""
Write-Host "  CourrierIA - Preparation cle USB" -ForegroundColor DarkYellow
Write-Host "  ==================================" -ForegroundColor DarkYellow
Write-Host ""

# ── Detecter les cles USB disponibles ────────────────────────
Write-Step "Detection des cles USB..."
$drives = Get-WmiObject Win32_LogicalDisk | Where-Object { $_.DriveType -eq 2 }

if ($drives.Count -eq 0) {
    Write-Err "Aucune cle USB detectee. Branchez votre cle et relancez."
    Read-Host "Appuyez sur Entree pour quitter"
    exit
}

Write-Host ""
Write-Host "  Cles USB trouvees :" -ForegroundColor White
$i = 0
foreach ($d in $drives) {
    $libre = [math]::Round($d.FreeSpace / 1GB, 1)
    $total = [math]::Round($d.Size / 1GB, 1)
    Write-Host "  [$i] $($d.DeviceID)  $($d.VolumeName)  ($libre Go libres / $total Go)" -ForegroundColor Gray
    $i++
}

Write-Host ""
$choix = Read-Host "  Entrez le numero de la cle USB a utiliser"
$usb = ($drives | Select-Object -Index ([int]$choix)).DeviceID

if (-not $usb) {
    Write-Err "Choix invalide."
    Read-Host "Appuyez sur Entree pour quitter"
    exit
}

$USB_DIR = "$usb\CourrierIA_USB"
Write-Host ""
Write-Host "  Destination : $USB_DIR" -ForegroundColor White

# Verifier espace (besoin ~8 Go)
$drive = Get-WmiObject Win32_LogicalDisk | Where-Object { $_.DeviceID -eq $usb }
$libreGo = [math]::Round($drive.FreeSpace / 1GB, 1)
if ($libreGo -lt 8) {
    Write-Warn "Espace insuffisant sur la cle ($libreGo Go libres, 8 Go recommandes)"
    $continuer = Read-Host "  Continuer quand meme ? (o/n)"
    if ($continuer -ne "o") { exit }
}

# Creer structure sur la cle
New-Item -ItemType Directory -Force -Path "$USB_DIR\server"     | Out-Null
New-Item -ItemType Directory -Force -Path "$USB_DIR\ollama"     | Out-Null
New-Item -ItemType Directory -Force -Path "$USB_DIR\python"     | Out-Null
New-Item -ItemType Directory -Force -Path "$USB_DIR\pip_cache"  | Out-Null

# ── 1. Copier les fichiers serveur ────────────────────────────
Write-Step "Copie des fichiers serveur..."
$SERVER_SRC = "C:\Users\Yoann\Documents\Rédaction de courriers IA\server"
foreach ($item in @("api","core","ia","models","static","main.py","launcher.py","requirements.txt")) {
    $src = Join-Path $SERVER_SRC $item
    if (Test-Path $src) {
        Copy-Item $src "$USB_DIR\server\" -Recurse -Force
        Write-Host "    + $item" -ForegroundColor Gray
    }
}
# Copier le script d'installation
if (Test-Path "$SERVER_SRC\install.ps1") {
    Copy-Item "$SERVER_SRC\install.ps1" "$USB_DIR\" -Force
}
Write-OK "Fichiers serveur copies"

# ── 2. Copier le modele Mistral (Ollama) ──────────────────────
Write-Step "Copie du modele Mistral (peut prendre 2-3 min)..."
$ollamaModels = "$env:USERPROFILE\.ollama\models"
if (Test-Path $ollamaModels) {
    Write-Host "    Copie de $ollamaModels..." -ForegroundColor Gray
    Copy-Item "$ollamaModels\*" "$USB_DIR\ollama\" -Recurse -Force
    Write-OK "Modele Mistral copie"
} else {
    Write-Warn "Modele Ollama non trouve dans $ollamaModels"
    Write-Warn "Lancez 'ollama pull mistral' puis revenez"
}

# ── 3. Telecharger Python portable ───────────────────────────
Write-Step "Telechargement de Python 3.11 (installeur)..."
$pyUrl  = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
$pyDest = "$USB_DIR\python\python-3.11.9-amd64.exe"
if (-not (Test-Path $pyDest)) {
    try {
        Invoke-WebRequest -Uri $pyUrl -OutFile $pyDest -UseBasicParsing
        Write-OK "Python 3.11 telecharge"
    } catch {
        Write-Warn "Echec telechargement Python - verifiez votre connexion"
    }
} else {
    Write-OK "Python 3.11 deja present sur la cle"
}

# ── 4. Telecharger Ollama ─────────────────────────────────────
Write-Step "Telechargement d'Ollama..."
$ollamaDest = "$USB_DIR\ollama\OllamaSetup.exe"
if (-not (Test-Path $ollamaDest)) {
    try {
        Invoke-WebRequest -Uri "https://ollama.com/download/OllamaSetup.exe" -OutFile $ollamaDest -UseBasicParsing
        Write-OK "Ollama telecharge"
    } catch {
        Write-Warn "Echec telechargement Ollama"
    }
} else {
    Write-OK "Ollama deja present sur la cle"
}

# ── 5. Pre-telecharger les packages pip ───────────────────────
Write-Step "Pre-telechargement des packages Python (pip cache)..."
$packages = @(
    "fastapi==0.100.0",
    "uvicorn[standard]==0.22.0",
    "SQLAlchemy==2.0.20",
    "pydantic==2.12.5",
    "pydantic-settings",
    "python-jose==3.3.0",
    "passlib==1.7.4",
    "bcrypt==4.0.1",
    "python-multipart==0.0.6",
    "cryptography",
    "faiss-cpu",
    "sentence-transformers",
    "numpy",
    "joblib",
    "python-docx",
    "ollama"
)
try {
    pip download @packages --dest "$USB_DIR\pip_cache" --quiet
    Write-OK "Packages pip pre-telecharges"
} catch {
    Write-Warn "Pip download echoue - les packages seront telecharges a l'installation"
}

# ── 6. Copier le modele d'embeddings ─────────────────────────
Write-Step "Copie du modele d'embeddings..."
$embSrc = "$env:USERPROFILE\.cache\torch\sentence_transformers"
if (Test-Path $embSrc) {
    New-Item -ItemType Directory -Force -Path "$USB_DIR\embeddings" | Out-Null
    Copy-Item "$embSrc\*" "$USB_DIR\embeddings\" -Recurse -Force
    Write-OK "Modele embeddings copie"
} else {
    Write-Warn "Modele embeddings non trouve - sera telecharge a la 1ere utilisation"
}

# ── 7. Creer le script d'installation USB ────────────────────
Write-Step "Creation du script d'installation depuis USB..."
$installUSB = @'
# ============================================================
#  CourrierIA - Installation depuis cle USB (HORS LIGNE)
#  Clic droit > Executer avec PowerShell (Admin)
# ============================================================

$ErrorActionPreference = "Continue"
$USB_DIR     = Split-Path -Parent $MyInvocation.MyCommand.Definition
$INSTALL_DIR = "C:\CourrierIA"

function Write-Step($msg) { Write-Host "" ; Write-Host "  > $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "  OK : $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  !! $msg" -ForegroundColor Yellow }

Clear-Host
Write-Host ""
Write-Host "  CourrierIA - Installation HORS LIGNE" -ForegroundColor DarkYellow
Write-Host "  ======================================" -ForegroundColor DarkYellow
Write-Host ""

# 1. Installer Python depuis la cle
Write-Step "Installation de Python 3.11..."
$pyExe = "$USB_DIR\python\python-3.11.9-amd64.exe"
$pythonOk = $false
try {
    $v = python --version 2>&1
    if ($v -match "3\.") { Write-OK "Python deja installe : $v" ; $pythonOk = $true }
} catch {}

if (-not $pythonOk) {
    if (Test-Path $pyExe) {
        Start-Process $pyExe -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")
        Write-OK "Python 3.11 installe"
    } else {
        Write-Warn "Installeur Python non trouve sur la cle"
    }
}

# 2. Creer dossiers
Write-Step "Creation des dossiers..."
foreach ($d in @(
    "$INSTALL_DIR\server",
    "$INSTALL_DIR\storage\faiss_index",
    "$INSTALL_DIR\storage\model_weights\embeddings"
)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
Write-OK "Dossiers crees"

# 3. Copier serveur
Write-Step "Copie des fichiers..."
foreach ($item in @("api","core","ia","models","static","main.py","launcher.py")) {
    $src = "$USB_DIR\server\$item"
    if (Test-Path $src) {
        Copy-Item $src "$INSTALL_DIR\server\" -Recurse -Force
    }
}
Write-OK "Fichiers copies"

# 4. Environnement virtuel
Write-Step "Creation de l'environnement Python..."
$venvPath = "$INSTALL_DIR\server\.venv"
if (-not (Test-Path "$venvPath\Scripts\python.exe")) {
    python -m venv $venvPath
}
$pip = "$venvPath\Scripts\pip.exe"
$py  = "$venvPath\Scripts\python.exe"
Write-OK "Environnement pret"

# 5. Installer packages depuis cache USB
Write-Step "Installation des packages Python (depuis cle USB - hors ligne)..."
$pipCache = "$USB_DIR\pip_cache"
if (Test-Path $pipCache) {
    & $pip install --quiet --no-index --find-links="$pipCache" `
        fastapi uvicorn SQLAlchemy pydantic pydantic-settings `
        python-jose passlib bcrypt python-multipart cryptography `
        faiss-cpu sentence-transformers numpy joblib python-docx ollama
    Write-OK "Packages installes depuis la cle"
} else {
    Write-Warn "Cache pip absent - installation depuis internet..."
    & $pip install --quiet fastapi "uvicorn[standard]" SQLAlchemy "pydantic==2.12.5" pydantic-settings python-jose passlib "bcrypt==4.0.1" python-multipart cryptography faiss-cpu sentence-transformers numpy joblib python-docx ollama
}

# 6. Copier modele embeddings
Write-Step "Copie du modele d'embeddings..."
$embSrc = "$USB_DIR\embeddings"
$embDst = "$INSTALL_DIR\storage\model_weights\embeddings\all-MiniLM-L6-v2"
if (Test-Path $embSrc) {
    New-Item -ItemType Directory -Force -Path $embDst | Out-Null
    Copy-Item "$embSrc\*" "$embDst\" -Recurse -Force
    Write-OK "Modele embeddings copie"
}

# 7. Installer Ollama depuis cle
Write-Step "Installation d'Ollama..."
$ollamaExe = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
if (-not (Test-Path $ollamaExe)) {
    $ollamaInst = "$USB_DIR\ollama\OllamaSetup.exe"
    if (Test-Path $ollamaInst) {
        Start-Process $ollamaInst -ArgumentList "/S" -Wait
        Start-Sleep -Seconds 3
        Write-OK "Ollama installe"
    } else {
        Write-Warn "Installeur Ollama absent de la cle"
    }
} else {
    Write-OK "Ollama deja installe"
}

# 8. Copier modele Mistral
Write-Step "Copie du modele Mistral..."
$mistralSrc = "$USB_DIR\ollama\manifests"
$mistralDst = "$env:USERPROFILE\.ollama\models"
if (Test-Path $mistralSrc) {
    New-Item -ItemType Directory -Force -Path $mistralDst | Out-Null
    Copy-Item "$USB_DIR\ollama\*" "$mistralDst\" -Recurse -Force -Exclude "OllamaSetup.exe"
    Write-OK "Modele Mistral copie"
} else {
    Write-Warn "Modele Mistral absent - lancez 'ollama pull mistral' apres"
}

# 9. Configuration
Write-Step "Configuration..."
$config = @"
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SERVER_PORT: int = 8000
    JWT_SECRET: str = "courrierIA_secret_prod_2024"
    JWT_ALGORITHM: str = "HS256"
    SQLCIPHER_DB_PATH: str = "C:/CourrierIA/storage/sqlcipher.db"
    SQLCIPHER_KEY: str = "courrierIA_db_key_prod_2024"
    MODEL_DIR: str = "C:/CourrierIA/storage/model_weights"
    FAISS_INDEX_DIR: str = "C:/CourrierIA/storage/faiss_index"

settings = Settings()
"@
$config | Out-File "$INSTALL_DIR\server\core\config.py" -Encoding UTF8
Write-OK "Configuration mise a jour"

# 10. Lanceur
$bat = @"
@echo off
title CourrierIA
cd /d C:\CourrierIA\server
echo.
echo  CourrierIA - Demarrage...
echo  L'application s'ouvrira dans votre navigateur.
echo  Ne fermez pas cette fenetre.
echo.
start "" "http://127.0.0.1:8000/static/index.html"
.venv\Scripts\python.exe launcher.py
pause
"@
$bat | Out-File "$INSTALL_DIR\CourrierIA.bat" -Encoding ASCII

# 11. Raccourci Bureau
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $lnk = $WshShell.CreateShortcut("$env:PUBLIC\Desktop\CourrierIA.lnk")
    $lnk.TargetPath = "$INSTALL_DIR\CourrierIA.bat"
    $lnk.WorkingDirectory = "$INSTALL_DIR\server"
    $lnk.Description = "CourrierIA"
    $lnk.Save()
    Write-OK "Raccourci Bureau cree"
} catch {}

# 12. Init DB
try {
    Set-Location "$INSTALL_DIR\server"
    & $py -c "import sys; sys.path.insert(0, r'$INSTALL_DIR\server'); from core.db import init_db; init_db()" 2>&1 | Out-Null
    Write-OK "Base de donnees initialisee"
} catch {}

Write-Host ""
Write-Host "  =====================================" -ForegroundColor Green
Write-Host "   Installation terminee ! " -ForegroundColor Green
Write-Host "  =====================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Double-cliquez sur CourrierIA sur le Bureau." -ForegroundColor White
Write-Host ""
Read-Host "  Appuyez sur Entree pour fermer"
'@

$installUSB | Out-File "$USB_DIR\INSTALLER_ICI.ps1" -Encoding UTF8

# ── README ───────────────────────────────────────────────────
$readme = @"
=====================================================
  CourrierIA - Cle USB d'installation
=====================================================

POUR INSTALLER SUR UN NOUVEAU PC (sans internet) :

  1. Branchez cette cle USB sur le nouveau PC
  2. Ouvrez la cle dans l'Explorateur Windows
  3. Faites clic droit sur "INSTALLER_ICI.ps1"
  4. Choisissez "Executer avec PowerShell"
  5. Cliquez "Oui" si Windows demande confirmation
  6. Attendez la fin de l'installation (5-10 min)
  7. Double-cliquez sur "CourrierIA" sur le Bureau

Aucune connexion internet requise.

CONTENU DE CETTE CLE :
  server/         - Application CourrierIA
  python/         - Installeur Python 3.11
  ollama/         - Ollama + modele Mistral 7B
  pip_cache/      - Packages Python
  embeddings/     - Modele d'analyse de texte

=====================================================
"@
$readme | Out-File "$USB_DIR\LIRE_MOI.txt" -Encoding UTF8

# ── Bilan ────────────────────────────────────────────────────
Write-Host ""
Write-Host "  =====================================" -ForegroundColor Green
Write-Host "   Cle USB preparee avec succes !" -ForegroundColor Green
Write-Host "  =====================================" -ForegroundColor Green
Write-Host ""

# Calculer taille totale
$taille = (Get-ChildItem $USB_DIR -Recurse | Measure-Object -Property Length -Sum).Sum
$tailleGo = [math]::Round($taille / 1GB, 2)
Write-Host "  Contenu copie : $tailleGo Go sur la cle $usb" -ForegroundColor White
Write-Host ""
Write-Host "  Sur le PC destinataire :" -ForegroundColor Gray
Write-Host "  Clic droit sur INSTALLER_ICI.ps1 > Executer avec PowerShell" -ForegroundColor Gray
Write-Host ""

explorer $USB_DIR
Read-Host "  Appuyez sur Entree pour fermer"