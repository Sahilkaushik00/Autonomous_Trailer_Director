@echo off
setlocal
echo Checking for Ollama...
ollama --version
if errorlevel 1 (
  echo Ollama is not installed or not on PATH. Install Ollama first.
  exit /b 1
)
echo Pulling Qwen3-VL 8B...
ollama pull qwen3-vl:8b
if errorlevel 1 (
  echo Failed to pull qwen3-vl:8b.
  exit /b 1
)
echo Local model setup complete.
endlocal
