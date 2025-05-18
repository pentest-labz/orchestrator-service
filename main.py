from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
import httpx

app = FastAPI(
    title="Orchestrator Service",
    version="1.1.1",
    description="Orchestrates calls to scanner-service with selectable scan modes."
)

# Home page with inputs for target, scan mode, and optional custom ports.
@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Orchestrator Service</title>
        <style>
          label { display:block; margin:8px 0; }
          #custom_ports_label { display:none; }
          button { margin-right: 8px; }
        </style>
      </head>
      <body>
        <h1>Orchestrator Service</h1>
        <label>
          Target Host:
          <input type="text" id="target" placeholder="e.g., example.com" />
        </label>
        <label>
          Scan Mode:
          <select id="scan_type" onchange="toggleCustomPorts()">
            <option value="all">All Ports</option>
            <option value="top10">Top 10 Ports</option>
            <option value="top100">Top 100 Ports</option>
            <option value="custom">Custom Ports</option>
          </select>
        </label>
        <label id="custom_ports_label">
          Custom Ports (comma-separated):
          <input type="text" id="custom_ports" placeholder="e.g., 22,80,443" />
        </label>
        <label>
          Service/Version Detection:
          <input type="checkbox" id="version" />
        </label>
        <button id="scan_btn" onclick="triggerScan()">Trigger Scan</button>
        <button id="cancel_btn" onclick="cancelScan()" style="display:none;">Cancel Scan</button>
        <pre id="result"></pre>
        <script>
          let currentController = null;

          function toggleCustomPorts() {
            const show = document.getElementById('scan_type').value === 'custom';
            document.getElementById('custom_ports_label').style.display = show ? 'block' : 'none';
          }

          async function triggerScan() {
            const target   = document.getElementById('target').value;
            const scanType = document.getElementById('scan_type').value;
            const version  = document.getElementById('version').checked;
            const params   = new URLSearchParams();
            params.append('target', target);
            params.append('scan_type', scanType);
            params.append('version',  String(version).toLowerCase());
            if (scanType === 'custom') {
              const ports = document.getElementById('custom_ports').value;
              params.append('ports', ports);
            }

            const scanBtn   = document.getElementById('scan_btn');
            const cancelBtn = document.getElementById('cancel_btn');
            const resultEl  = document.getElementById('result');

            // Set loading state
            scanBtn.disabled = true;
            scanBtn.innerText = 'Scanning…';
            cancelBtn.style.display = 'inline-block';
            resultEl.innerText = '';

            // Prepare for cancellation
            currentController = new AbortController();
            const signal = currentController.signal;

            try {
              const resp = await fetch(`/trigger?${params.toString()}`, { signal });
              const data = await resp.json();
              resultEl.innerText = JSON.stringify(data, null, 2);
            } catch (err) {
              if (err.name === 'AbortError') {
                resultEl.innerText = 'Scan cancelled by user.';
              } else {
                resultEl.innerText = 'Error: ' + err;
              }
            } finally {
              // Reset UI
              scanBtn.disabled = false;
              scanBtn.innerText = 'Trigger Scan';
              cancelBtn.style.display = 'none';
              currentController = null;
            }
          }

          function cancelScan() {
            if (currentController) {
              currentController.abort();
            }
          }
        </script>
      </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

# Proxy /trigger to the scanner-service, forwarding the same params.
@app.get("/trigger", response_class=JSONResponse)
def trigger_scanner(
    target: str = Query(..., description="Target host to scan"),
    scan_type: str = Query("all", regex="^(all|top10|top100|custom)$", description="Scan mode"),
    version: bool = Query(False, description="Enable service/version detection"),
    ports: str | None = Query(None, description="Comma-separated ports for custom mode")
):
    print("### Called Trigger")
    scanner_url = "http://scanner:8001/scan"
    params = {
        "target": target,
        "scan_type": scan_type,
        "version":   str(version).lower()
    }
    if scan_type == "custom":
        if not ports:
            return JSONResponse(
                content={"error": "`ports` is required for custom scan_type"},
                status_code=400
            )
        params["ports"] = ports

    try:
        with httpx.Client(timeout=None) as client:
            print(f"### Calling {scanner_url} with {params}")
            r = client.get(scanner_url, params=params)
            print(f"### Scanner responded [{r.status_code}]: {r.text}")
            r.raise_for_status()
            return JSONResponse(content=r.json(), status_code=200)
    except httpx.HTTPStatusError as exc:
        return JSONResponse(
            content={"scanner_error": exc.response.json()},
            status_code=exc.response.status_code
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to call scanner service: {e}"},
            status_code=500
        )
