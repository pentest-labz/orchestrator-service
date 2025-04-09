from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import httpx

app = FastAPI(
    title="Orchestrator Service",
    version="1.0.0",
    description="A microservice that orchestrates calls to scanner-service."
)

# Home route that serves an HTML page with a button.
@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Orchestrator Service</title>
      </head>
      <body>
        <h1>Welcome to the Orchestrator Service</h1>
        <button onclick="triggerScan()">Trigger Scanner Service</button>
        <p id="result"></p>
        <script>
          async function triggerScan() {
            const response = await fetch('/trigger');
            const data = await response.json();
            document.getElementById('result').innerText = JSON.stringify(data);
          }
        </script>
      </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

# Endpoint that when called makes a request to the scanner-service.
@app.get("/trigger", response_class=JSONResponse)
def trigger_scanner():
    try:
        # In Docker Compose, we can use the service name to call the scanner-service.
        scanner_url = "http://scanner:8001/scan"
        with httpx.Client(timeout=10) as client:
            response = client.get(scanner_url)
            return response.json()
    except Exception as e:
        return {"error": f"Failed to call scanner service: {e}"}
