param(
    [string]$BindHost = "0.0.0.0",
    [int]$Port = 8000,
    [switch]$Reload
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

function Write-Step($text) {
    Write-Host ""
    Write-Host "--------------------------------------------" -ForegroundColor DarkCyan
    Write-Host "  $text" -ForegroundColor DarkCyan
    Write-Host "--------------------------------------------" -ForegroundColor DarkCyan
}

function Import-DotEnv {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        Write-Host ".env not found at $Path" -ForegroundColor Yellow
        return
    }

    Write-Host "Loading env from $Path ..." -ForegroundColor Cyan
    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) {
            return
        }

        $idx = $line.IndexOf("=")
        if ($idx -lt 1) {
            return
        }

        $key = $line.Substring(0, $idx).Trim()
        $value = $line.Substring($idx + 1)
        [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
}

function Wait-TcpPort {
    param(
        [string]$HostName,
        [int]$Port,
        [string]$ServiceName,
        [int]$TimeoutSec = 60
    )

    Write-Host "Waiting for $ServiceName at ${HostName}:${Port} ..." -ForegroundColor Cyan
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        $tcp = Test-NetConnection $HostName -Port $Port -WarningAction SilentlyContinue
        if ($tcp.TcpTestSucceeded) {
            Write-Host "$ServiceName is ready." -ForegroundColor Green
            return $true
        }
        Start-Sleep -Seconds 2
    }

    Write-Host "$ServiceName did not become ready within ${TimeoutSec}s." -ForegroundColor Red
    return $false
}

function Test-TcpPortOpen {
    param(
        [string]$HostName,
        [int]$Port
    )

    try {
        $tcp = Test-NetConnection $HostName -Port $Port -WarningAction SilentlyContinue
        return [bool]$tcp.TcpTestSucceeded
    } catch {
        return $false
    }
}

function Get-ContainerStatus {
    param([string]$ContainerName)

    $prevNativeErrPref = $PSNativeCommandUseErrorActionPreference
    $PSNativeCommandUseErrorActionPreference = $false
    try {
        $status = (& docker inspect --format '{{.State.Status}}' $ContainerName 2>$null | Out-String).Trim()
        $exitCode = $LASTEXITCODE
    } finally {
        $PSNativeCommandUseErrorActionPreference = $prevNativeErrPref
    }

    if ($exitCode -ne 0 -or -not $status) {
        return $null
    }

    return $status
}

function Ensure-ExistingContainerRunning {
    param(
        [string]$ContainerName,
        [string]$ServiceLabel
    )

    $status = Get-ContainerStatus -ContainerName $ContainerName
    if (-not $status) {
        Write-Host "$ServiceLabel container '$ContainerName' not found. Script will not create a new container." -ForegroundColor Red
        return $false
    }

    if ($status -eq "running") {
        Write-Host "$ServiceLabel container '$ContainerName' already running." -ForegroundColor Green
        return $true
    }

    Write-Host "$ServiceLabel container '$ContainerName' is '$status'. Starting ..." -ForegroundColor Yellow
    & docker start $ContainerName | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to start container '$ContainerName'." -ForegroundColor Red
        return $false
    }

    Write-Host "$ServiceLabel container '$ContainerName' started." -ForegroundColor Green
    return $true
}

function Wait-RedisReady {
    param(
        [string]$ContainerName,
        [string]$HostName,
        [int]$Port,
        [int]$TimeoutSec = 45
    )

    Write-Host "Waiting for Redis readiness ..." -ForegroundColor Cyan
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        $prevNativeErrPref = $PSNativeCommandUseErrorActionPreference
        $PSNativeCommandUseErrorActionPreference = $false
        try {
            $pong = (& docker exec $ContainerName sh -c "redis-cli ping 2>/dev/null || true" 2>$null | Out-String)
            $dockerExitCode = $LASTEXITCODE
        } finally {
            $PSNativeCommandUseErrorActionPreference = $prevNativeErrPref
        }

        if ($dockerExitCode -eq 0 -and "$pong".Trim() -eq "PONG") {
            Write-Host "Redis is ready (PONG)." -ForegroundColor Green
            return $true
        }

        Start-Sleep -Seconds 2
    }

    Write-Host "Redis ping not ready. Fallback TCP check ..." -ForegroundColor Yellow
    return (Wait-TcpPort -HostName $HostName -Port $Port -ServiceName "Redis" -TimeoutSec 15)
}

function Wait-QdrantReady {
    param(
        [string]$HostName,
        [int]$Port,
        [int]$TimeoutSec = 45
    )

    return (Wait-TcpPort -HostName $HostName -Port $Port -ServiceName "Qdrant" -TimeoutSec $TimeoutSec)
}

Write-Step "STEP 1 - Docker Desktop"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker CLI not found. Install Docker Desktop first." -ForegroundColor Red
    exit 1
}

$dockerReady = $false
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
& docker info 2>$null | Out-Null
$dockerExitCode = $LASTEXITCODE
$ErrorActionPreference = $prevEap

if ($dockerExitCode -eq 0) {
    $dockerReady = $true
    Write-Host "Docker Desktop is already running." -ForegroundColor Green
}

if (-not $dockerReady) {
    Write-Host "Docker daemon is not running. Starting Docker Desktop ..." -ForegroundColor Yellow

    $dockerDesktopPaths = @(
        "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
        "$env:LOCALAPPDATA\Docker\Docker Desktop.exe"
    )
    $dockerExe = $dockerDesktopPaths | Where-Object { Test-Path $_ } | Select-Object -First 1

    if (-not $dockerExe) {
        Write-Host "Cannot find Docker Desktop executable. Start Docker manually and rerun." -ForegroundColor Red
        exit 1
    }

    Start-Process -FilePath $dockerExe

    Write-Host "Waiting for Docker daemon to be ready (up to 120s) ..." -ForegroundColor Cyan
    $deadline = (Get-Date).AddSeconds(120)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 3
        $ErrorActionPreference = "SilentlyContinue"
        & docker info 2>$null | Out-Null
        $loopExitCode = $LASTEXITCODE
        $ErrorActionPreference = $prevEap
        if ($loopExitCode -eq 0) {
            $dockerReady = $true
            break
        }
        Write-Host "  Still waiting ..." -ForegroundColor DarkGray
    }

    if (-not $dockerReady) {
        Write-Host "Docker Desktop did not become ready within 120s." -ForegroundColor Red
        exit 1
    }

    Write-Host "Docker Desktop is ready." -ForegroundColor Green
}

Write-Step "STEP 2 - Load .env"
Import-DotEnv -Path (Join-Path $repoRoot ".env")

$qdrantHost = if ($env:QDRANT_HOST) { $env:QDRANT_HOST } else { "localhost" }
$qdrantPort = if ($env:QDRANT_PORT) { [int]$env:QDRANT_PORT } else { 6333 }
$redisHost = if ($env:REDIS_HOST) { $env:REDIS_HOST } else { "localhost" }
$redisPort = if ($env:REDIS_PORT) { [int]$env:REDIS_PORT } else { 6379 }
$qdrantContainerName = "rag-chatbot-qdrant"
$redisContainerName = "rag-chatbot-redis"

Write-Step "STEP 3 - Start Docker services"

if (Test-TcpPortOpen -HostName $qdrantHost -Port $qdrantPort) {
    Write-Host "Qdrant already reachable at ${qdrantHost}:${qdrantPort}. Skip docker start." -ForegroundColor Green
} else {
    if (-not (Ensure-ExistingContainerRunning -ContainerName $qdrantContainerName -ServiceLabel "Qdrant")) {
        exit 1
    }
}

if (Test-TcpPortOpen -HostName $redisHost -Port $redisPort) {
    Write-Host "Redis already reachable at ${redisHost}:${redisPort}. Skip docker start." -ForegroundColor Green
} else {
    if (-not (Ensure-ExistingContainerRunning -ContainerName $redisContainerName -ServiceLabel "Redis")) {
        exit 1
    }
}

if (-not (Wait-QdrantReady -HostName $qdrantHost -Port $qdrantPort -TimeoutSec 45)) {
    exit 1
}

if (Test-TcpPortOpen -HostName $redisHost -Port $redisPort) {
    $redisContainerStatus = Get-ContainerStatus -ContainerName $redisContainerName
    if ($redisContainerStatus -eq "running") {
        if (-not (Wait-RedisReady -ContainerName $redisContainerName -HostName $redisHost -Port $redisPort -TimeoutSec 45)) {
            exit 1
        }
    } else {
        Write-Host "Redis reachable on host port. Skip container ping." -ForegroundColor Green
    }
} else {
    Write-Host "Redis port still not reachable after start attempt." -ForegroundColor Red
    exit 1
}

Write-Step "STEP 4 - Python env"

$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host ".venv not found at $pythonExe" -ForegroundColor Red
    Write-Host "Create venv and install dependencies first." -ForegroundColor Yellow
    exit 1
}

Write-Host "Using Python: $pythonExe" -ForegroundColor Green

Write-Step "STEP 5 - Bootstrap deps"

& $pythonExe -m app.bootstrap
if ($LASTEXITCODE -ne 0) {
    Write-Host "Bootstrap failed." -ForegroundColor Red
    exit 1
}

Write-Step "STEP 6 - Start uvicorn"

$uvicornArgs = @("-m", "uvicorn", "app.main:app", "--host", $BindHost, "--port", $Port.ToString())
if ($Reload) {
    $uvicornArgs += "--reload"
}

Write-Host "Starting server at http://localhost:$Port ..." -ForegroundColor Green
& $pythonExe @uvicornArgs
