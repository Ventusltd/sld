# Trusted main only. Schedule this controller with the existing logged-on user.
param(
    [Parameter(Mandatory=$true)][string]$Repository,
    [Parameter(Mandatory=$true)][string]$OutputRoot,
    [Parameter(Mandatory=$true)][string]$Python,
    [switch]$ForceFurnace
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
function Run([string]$Program, [string[]]$Arguments) {
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program failed ($LASTEXITCODE): $Arguments" }
}
$repoPath = (Resolve-Path -LiteralPath $Repository).Path
$outputPath = [IO.Path]::GetFullPath($OutputRoot)
New-Item -ItemType Directory -Path $outputPath -Force | Out-Null
# A file lock also prevents overlap between manual and scheduled runs.
$lock = $null
$candidate = Join-Path $outputPath 'candidate'
$created = $false
try {
    $lock = [IO.File]::Open((Join-Path $outputPath 'refresh.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
    Set-Location -LiteralPath $repoPath
    $remote = (& git remote get-url origin).Trim()
    if ($LASTEXITCODE -ne 0 -or $remote -notin @('https://github.com/Ventusltd/sld.git','git@github.com:Ventusltd/sld.git')) { throw 'Unexpected repository origin' }
    if ((& git branch --show-current).Trim() -ne 'main') { throw 'Controller requires main' }
    if (@(& git status --porcelain).Count -ne 0) { throw 'Working tree is dirty; refusing to overwrite changes' }
    Run git @('pull','--ff-only','origin','main')
    $base = (& git rev-parse HEAD).Trim()
    if (Test-Path -LiteralPath $candidate) { throw 'Candidate path already exists; inspect it before retrying' }
    Run git @('worktree','add','--detach',$candidate,$base)
    $created = $true
    Set-Location -LiteralPath $candidate
    Run $Python @('scripts/fetch_sources.py')
    Run $Python @('scripts/build_catalogue.py')
    Run $Python @('-m','unittest','discover','-s','tests','-p','test_*.py')
    & $Python scripts/verify_furnace.py
    $needsFurnace = $LASTEXITCODE -ne 0
    if ($needsFurnace -or $ForceFurnace) {
        $furnaceOut = Join-Path $outputPath 'furnace'
        Run $Python @('scripts/furnace.py','--out',$furnaceOut)
        Run $Python @('scripts/verify_furnace.py','--evidence-dir',$furnaceOut)
        New-Item -ItemType Directory -Path 'data/furnace' -Force | Out-Null
        Copy-Item -LiteralPath (Join-Path $furnaceOut 'photon-library.json') -Destination 'data/furnace/photon-library.json'
        Copy-Item -LiteralPath (Join-Path $furnaceOut 'photon-evidence.json') -Destination 'data/furnace/photon-evidence.json'
    }
    Run $Python @('scripts/verify_furnace.py')
    Run $Python @('scripts/build_site.py')
    # Only generated, reviewed-source outputs may enter the autonomous commit.
    Run git @('add','--','data/library.json','data/source-lock.json','data/upstream','data/furnace','assets/previews')
    & git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) { Write-Output 'Pinned sources and accepted furnace inputs unchanged'; return }
    if ($LASTEXITCODE -ne 1) { throw 'Cannot inspect candidate diff' }
    Run git @('-c','user.name=SLD automation','-c','user.email=sld-automation@users.noreply.github.com','commit','-m','Refresh validated SLD catalogue and furnace evidence')
    # Ordinary fast-forward push rejects a concurrently advanced main.
    Run git @('push','origin','HEAD:refs/heads/main')
    Set-Location -LiteralPath $repoPath
    Run git @('pull','--ff-only','origin','main')
} finally {
    Set-Location -LiteralPath $repoPath
    if ($created) {
        $resolvedCandidate = [IO.Path]::GetFullPath($candidate)
        if ($resolvedCandidate -ne (Join-Path $outputPath 'candidate')) { throw 'Candidate cleanup escaped output directory' }
        & git worktree remove --force -- $resolvedCandidate
    }
    if ($null -ne $lock) { $lock.Dispose() }
}
