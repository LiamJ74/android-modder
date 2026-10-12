@echo off
rem Run the `am` CLI from a clone on Windows, via uv if present.
setlocal
set "REPO=%~dp0.."
where uv >nul 2>nul
if %ERRORLEVEL%==0 (
  uv run --project "%REPO%" am %*
) else (
  set "PYTHONPATH=%REPO%"
  python -m am %*
)
