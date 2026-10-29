param(
    [string]$ExtensionRoot = (Join-Path $PSScriptRoot '..\..\..\..\DagorVisualStudioTools'),
    [ValidateSet('dev', 'dbg', 'rel')][string[]]$Configurations = @('dev', 'dbg', 'rel'),
    [switch]$SkipIntelliSense
)
$ErrorActionPreference = 'Stop'
$engineRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
$msbuild = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -find 'MSBuild\**\Bin\MSBuild.exe' | Select-Object -First 1
if (!$msbuild) { throw 'Install Visual Studio with Desktop development with C++.' }
$taskProject = Join-Path $ExtensionRoot 'MSBuildUtilities\Gaijin.MSBuild.Utilities.csproj'
if (!(Test-Path -LiteralPath $taskProject)) { throw "Extension sources not found at $ExtensionRoot. Clone https://github.com/GaijinEntertainment/DagorVisualStudioTools and apply the VS18 build fixes, or pass -ExtensionRoot." }
Push-Location (Split-Path -Parent $taskProject)
try { & $msbuild $taskProject /restore /p:Configuration=Release /nologo /v:minimal /nr:false }
finally { Pop-Location }
if ($LASTEXITCODE) { throw 'Building the Dagor MSBuild tasks failed.' }
$destination = Join-Path $PSScriptRoot 'bin'
New-Item -ItemType Directory -Path $destination -Force | Out-Null
foreach ($dll in Get-ChildItem (Join-Path $ExtensionRoot 'MSBuildUtilities\bin\Release\net472\*.dll')) {
    $target = Join-Path $destination $dll.Name
    if ((Test-Path -LiteralPath $target) -and ((Get-FileHash $dll.FullName).Hash -eq (Get-FileHash $target).Hash)) { continue }
    Copy-Item -LiteralPath $dll.FullName -Destination $target -Force
}
$devtools = if ($env:GDEVTOOL) { $env:GDEVTOOL } else { Join-Path $engineRoot '..\devtools' }
$python = Join-Path $devtools 'python3\python.exe'
if (!(Test-Path -LiteralPath $python)) { $python = 'python' }
& $python (Join-Path $PSScriptRoot 'generate_projects.py')
if ($LASTEXITCODE) { throw 'Generating the Visual Studio solution failed.' }
if (!$SkipIntelliSense) {
    $projects = @('samples\testGI\prog\testGI.vcxproj', 'samples\skiesSample\prog\skiesSample.vcxproj', 'samples\dngSceneViewer\prog\dng_scene_viewer.vcxproj', 'outerSpace\prog\outer_space.vcxproj', 'prog\tools\ShaderCompiler2\ShaderCompiler2.vcxproj', 'prog\tools\AssetViewer\AssetViewer.vcxproj', 'prog\tools\sceneTools\daEditorX\daEditorX.vcxproj', 'prog\tools\converters\dag2blk\dag2blk.vcxproj', 'prog\tools\dargbox\dargbox.vcxproj')
    $registry = Join-Path $engineRoot '_output\ide\project-registry.json'
    if (Test-Path -LiteralPath $registry) {
        $projects += @(Get-Content $registry -Raw | ConvertFrom-Json | ForEach-Object { $_.project } | Where-Object { Test-Path -LiteralPath $_ })
    }
    foreach ($project in $projects) {
      foreach ($config in $Configurations) {
        $projectPath = if ([IO.Path]::IsPathRooted($project)) { $project } else { Join-Path $engineRoot $project }
        & $msbuild $projectPath /t:GenerateDagorIntelliSense /p:Configuration=$config /p:Platform=x64 /nologo /v:minimal /nr:false
        if ($LASTEXITCODE) { throw "Generating IntelliSense failed for $project" }
      }
    }
}
Write-Host "Ready: $engineRoot\DagorEngine.sln"
