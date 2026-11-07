# Run from any directory. Keep this file beside TseExcel.slnx.
$ErrorActionPreference = 'Stop'
$env:MSBuildEnableWorkloadResolver = 'false'

Push-Location $PSScriptRoot
try {
    dotnet restore TseExcel.slnx --disable-parallel --verbosity minimal
    if ($LASTEXITCODE -ne 0) { throw "Restore failed (exit code $LASTEXITCODE)." }

    dotnet build TseExcel.slnx --configuration Release --no-restore --maxcpucount:1 --nodeReuse:false -p:UseSharedCompilation=false --verbosity minimal
    if ($LASTEXITCODE -ne 0) { throw "Release build failed (exit code $LASTEXITCODE)." }

    dotnet test TseExcel.slnx --configuration Release --no-build --no-restore --maxcpucount:1 --logger 'console;verbosity=minimal' --blame-hang-timeout 60s --blame-hang-dump-type none
    if ($LASTEXITCODE -ne 0) { throw "Release tests failed (exit code $LASTEXITCODE)." }

    Write-Host 'Restore, Release build, and tests completed successfully.'
}
finally {
    Pop-Location
}
