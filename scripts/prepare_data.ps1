param()

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$destination = Join-Path $repoRoot 'data\raw\hillstrom.csv'
$expectedHash = '0E5893329D8B93CEFECC571777672028290AB69865718020C78C7284F291AECE'
$expectedBytes = 3964977
$expectedRows = 64000
$sourceUrl = 'http://www.minethatdata.com/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv'

if (Test-Path -LiteralPath $destination) {
    $existingHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash
    if ($existingHash -eq $expectedHash) {
        Write-Host 'Hillstrom data already exists and passed SHA-256 verification.'
        exit 0
    }
    throw "Existing data failed SHA-256 verification: $destination"
}

$destinationDirectory = Split-Path -Parent $destination
New-Item -ItemType Directory -Force -Path $destinationDirectory | Out-Null
$temporary = Join-Path ([System.IO.Path]::GetTempPath()) ("hillstrom-{0}.csv" -f [guid]::NewGuid())

try {
    Write-Host "Downloading the publisher file from $sourceUrl"
    Invoke-WebRequest -Uri $sourceUrl -OutFile $temporary -UseBasicParsing

    $download = Get-Item -LiteralPath $temporary
    if ($download.Length -ne $expectedBytes) {
        throw "Downloaded file size mismatch: expected $expectedBytes bytes, got $($download.Length)"
    }

    $actualHash = (Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash
    if ($actualHash -ne $expectedHash) {
        throw "Downloaded file SHA-256 mismatch: expected $expectedHash, got $actualHash"
    }

    $header = Get-Content -LiteralPath $temporary -TotalCount 1
    $expectedHeader = 'recency,history_segment,history,mens,womens,zip_code,newbie,channel,segment,visit,conversion,spend'
    if ($header -ne $expectedHeader) {
        throw 'Downloaded file schema header does not match the frozen input.'
    }

    $rowCount = (Get-Content -LiteralPath $temporary | Measure-Object -Line).Lines - 1
    if ($rowCount -ne $expectedRows) {
        throw "Downloaded file row count mismatch: expected $expectedRows, got $rowCount"
    }

    Move-Item -LiteralPath $temporary -Destination $destination
    (Get-Item -LiteralPath $destination).IsReadOnly = $true
    Write-Host "Data ready: $destination"
    Write-Host "SHA-256 verified: $expectedHash"
}
finally {
    if (Test-Path -LiteralPath $temporary) {
        Remove-Item -LiteralPath $temporary -Force
    }
}
