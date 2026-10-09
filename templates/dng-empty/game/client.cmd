@rem Runs the game. The scripts and data are read from ..\prog (no vromfs rebuild needed); pass more arguments as usual,
@rem e.g. client.cmd -scene:gamedata/scenes/main.blk -config:video/driver:t=vulkan
@pushd "%~dp0"
@set ARCH=x86_64
@if "%PROCESSOR_ARCHITECTURE%" == "ARM64" set ARCH=arm64
@start "" windows-%ARCH%\dng_empty-dev.exe -config:debug/useAddonVromSrc:b=yes %*
@popd
