@echo off
rem Brings the "desktop" Jenkins agent online in this logged-in session, so
rem headed runs are visible. The secret lives in agent-secret.txt, gitignored.
title Jenkins desktop agent - keep this window open

set SECRET_FILE=%~dp0agent-secret.txt
if not exist "%SECRET_FILE%" (
    echo Missing %SECRET_FILE%
    echo Copy the secret from Manage Jenkins - Nodes - desktop into that file.
    pause
    exit /b 1
)
set /p SECRET=<"%SECRET_FILE%"

cd /d C:\jenkins-agent
if not exist agent.jar (
    echo Downloading agent.jar...
    curl.exe -sO http://localhost:8080/jnlpJars/agent.jar
)

java -jar agent.jar ^
    -url http://localhost:8080/ ^
    -secret %SECRET% ^
    -name desktop ^
    -webSocket ^
    -workDir "C:\jenkins-agent"

pause
