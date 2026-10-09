@rem Runs the dedicated server (clients connect with client.cmd -connect:localhost); scripts are read from ..\prog
@pushd "%~dp0"
@set ARCH=x86_64
@if "%PROCESSOR_ARCHITECTURE%" == "ARM64" set ARCH=arm64
@windows-%ARCH%\dng_empty-ded-dev.exe -config:debug/useAddonVromSrc:b=yes %*
@set ERR=%ERRORLEVEL%
@popd
@exit /b %ERR%
