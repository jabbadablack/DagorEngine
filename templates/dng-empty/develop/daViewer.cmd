@rem daViewer (assetViewer) for the assets in assets\
@pushd "%~dp0"
@call ..\_engine.cmd || (echo Run "python project.py setup" in the project dir first. & popd & exit /b 1)
@start "" "%DAGOR_CDK_DIR%\assetViewer2-dev.exe" ..\application.blk %*
@popd
