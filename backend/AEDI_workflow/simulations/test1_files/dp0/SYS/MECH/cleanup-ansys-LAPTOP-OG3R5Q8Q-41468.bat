@echo off
set LOCALHOST=%COMPUTERNAME%
if /i "%LOCALHOST%"=="LAPTOP-OG3R5Q8Q" (taskkill /f /pid 15376)
if /i "%LOCALHOST%"=="LAPTOP-OG3R5Q8Q" (taskkill /f /pid 5372)
if /i "%LOCALHOST%"=="LAPTOP-OG3R5Q8Q" (taskkill /f /pid 3088)
if /i "%LOCALHOST%"=="LAPTOP-OG3R5Q8Q" (taskkill /f /pid 41468)

del /F cleanup-ansys-LAPTOP-OG3R5Q8Q-41468.bat
