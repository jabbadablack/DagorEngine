@rem impostorBaker: bakes impostor textures of the assets that use them
@pushd "%~dp0"
@call ..\_engine.cmd || (echo Run "python project.py setup" in the project dir first. & popd & exit /b 1)
@"%DAGOR_CDK_DIR%\impostorBaker-dev.exe" ..\application.blk -rootdir:./ -clean:yes %*
@set ERR=%ERRORLEVEL%
@popd
@exit /b %ERR%
