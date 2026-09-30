@echo off
setlocal
if "%~1"=="" (
  echo Usage: run_local.bat path\to\episode.mp4
  exit /b 1
)
python -m src.main ^
  --episode data\episode_demo.json ^
  --audiences data\audiences_demo.json ^
  --mode live ^
  --provider local ^
  --video "%~1" ^
  --render ^
  --render-dir sample_run\local_rendered ^
  --output sample_run\local_run.json
endlocal
