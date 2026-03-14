@echo off
set LOCALHOST=%COMPUTERNAME%
if /i "%LOCALHOST%"=="LAPTOP-OG3R5Q8Q" (taskkill /f /pid 21212)
if /i "%LOCALHOST%"=="LAPTOP-OG3R5Q8Q" (taskkill /f /pid 2632)
if /i "%LOCALHOST%"=="LAPTOP-OG3R5Q8Q" (taskkill /f /pid 9296)
if /i "%LOCALHOST%"=="LAPTOP-OG3R5Q8Q" (taskkill /f /pid 30892)

del /F cleanup-ansys-LAPTOP-OG3R5Q8Q-30892.bat
