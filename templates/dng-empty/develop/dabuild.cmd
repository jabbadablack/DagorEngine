@rem dabuild: exports assets\ into the game packs (..\game\content), as python ..\prog\build.py assets does
@pushd "%~dp0"
@call ..\_engine.cmd || (echo Run "python project.py setup" in the project dir first. & popd & exit /b 1)
@"%DAGOR_CDK_DIR%\daBuild-dev.exe" ..\application.blk -q -jobs:%NUMBER_OF_PROCESSORS% %*
@set ERR=%ERRORLEVEL%
@popd
@exit /b %ERR%
