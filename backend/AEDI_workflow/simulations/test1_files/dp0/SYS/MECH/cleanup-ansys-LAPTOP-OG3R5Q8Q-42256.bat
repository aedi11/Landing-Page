@echo off
set LOCALHOST=%COMPUTERNAME%
if /i "%LOCALHOST%"=="LAPTOP-OG3R5Q8Q" (taskkill /f /pid 3492)
if /i "%LOCALHOST%"=="LAPTOP-OG3R5Q8Q" (taskkill /f /pid 37068)
if /i "%LOCALHOST%"=="LAPTOP-OG3R5Q8Q" (taskkill /f /pid 46736)
if /i "%LOCALHOST%"=="LAPTOP-OG3R5Q8Q" (taskkill /f /pid 42256)

del /F cleanup-ansys-LAPTOP-OG3R5Q8Q-42256.bat
