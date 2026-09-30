@echo off
setlocal
if "%~1"=="" (
  echo Usage: run_live.bat path\to\episode.mp4
  exit /b 1
)
python -m src.main ^
  --episode data/episode_demo.json ^
  --audiences data/audiences_demo.json ^
  --mode live ^
  --video "%~1" ^
  --render ^
  --render-dir sample_run/live_rendered ^
  --output sample_run/live_run.json
endlocal
