@echo off
setlocal
set "PYTHONHOME="
set "PYTHONPATH="
set "PYTHONUTF8=1"
set "PYTHONNOUSERSITE=1"
"%~dp0runtime\python.exe" -I -X utf8 "%~dp0app\review_launcher.py" %*
if errorlevel 1 (
  echo Application stopped with an error. Keep the message above for review.
  pause
)
endlocal
