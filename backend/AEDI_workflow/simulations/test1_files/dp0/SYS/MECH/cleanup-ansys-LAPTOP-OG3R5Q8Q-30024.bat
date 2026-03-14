@echo off
set LOCALHOST=%COMPUTERNAME%
if /i "%LOCALHOST%"=="LAPTOP-OG3R5Q8Q" (taskkill /f /pid 30512)
if /i "%LOCALHOST%"=="LAPTOP-OG3R5Q8Q" (taskkill /f /pid 46452)
if /i "%LOCALHOST%"=="LAPTOP-OG3R5Q8Q" (taskkill /f /pid 38620)
if /i "%LOCALHOST%"=="LAPTOP-OG3R5Q8Q" (taskkill /f /pid 30024)

del /F cleanup-ansys-LAPTOP-OG3R5Q8Q-30024.bat
