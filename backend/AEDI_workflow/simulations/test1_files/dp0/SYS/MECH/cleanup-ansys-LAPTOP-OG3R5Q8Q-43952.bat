@echo off
set LOCALHOST=%COMPUTERNAME%
if /i "%LOCALHOST%"=="LAPTOP-OG3R5Q8Q" (taskkill /f /pid 468)
if /i "%LOCALHOST%"=="LAPTOP-OG3R5Q8Q" (taskkill /f /pid 46196)
if /i "%LOCALHOST%"=="LAPTOP-OG3R5Q8Q" (taskkill /f /pid 31052)
if /i "%LOCALHOST%"=="LAPTOP-OG3R5Q8Q" (taskkill /f /pid 43952)

del /F cleanup-ansys-LAPTOP-OG3R5Q8Q-43952.bat
