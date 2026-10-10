@echo off
set ARCH_DIR=windows-x86_64
if "%PROCESSOR_ARCHITECTURE%" == "ARM64" (
  set ARCH_DIR=windows-arm64
) else (
  if not "%PROCESSOR_IDENTIFIER:(64-bit)=%" == "%PROCESSOR_IDENTIFIER%" (
    if not "%PROCESSOR_IDENTIFIER:ARMv=%" == "%PROCESSOR_IDENTIFIER%" (
      set ARCH_DIR=windows-arm64
    )
  )
)
set dargbox=%~dp0%ARCH_DIR%\dargbox-dev.exe
rem x86_64 exe runs on arm64 hosts through emulation; the reverse cannot work
if not exist %dargbox% set dargbox=%~dp0windows-x86_64\dargbox-dev.exe
rem transitional layouts, until the checkout is rebuilt/updated
if not exist %dargbox% set dargbox=%~dp0win64\dargbox-dev.exe
if not exist %dargbox% set dargbox=%~dp0dargbox-64-dev.exe
if not exist %dargbox% (
  echo no dargbox executable found
  exit
)
start %dargbox% %*