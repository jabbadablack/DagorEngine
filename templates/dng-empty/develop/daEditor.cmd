@rem daEditor for this project: its workspace is made from ..\application.blk on the first start
@pushd "%~dp0"
@call ..\_engine.cmd || (echo Run "python project.py setup" in the project dir first. & popd & exit /b 1)
@start "" "%DAGOR_CDK_DIR%\daEditor3x-dev.exe" ..\application.blk %*
@popd
