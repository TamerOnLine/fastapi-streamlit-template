Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/healthz | Out-Null
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/docs    | Out-Null
Write-Host "Endpoints hit."