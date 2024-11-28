"""Real-time monitoring dashboard for Arcana agents."""

from typing import Dict, Any, List
import asyncio
from datetime import datetime
import json
from pathlib import Path
import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from core.agent_registry import AgentRegistry
from core.monitoring import MetricsCollector
from core.error_handling import ErrorHandler

app = FastAPI(title="Arcana Monitoring Dashboard")

# Mount static files
static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Store WebSocket connections
active_connections: List[WebSocket] = []

class Dashboard:
    """Dashboard manager for real-time monitoring."""

    def __init__(
        self,
        agent_registry: AgentRegistry,
        metrics_collector: MetricsCollector,
        error_handler: ErrorHandler
    ):
        self.registry = agent_registry
        self.metrics = metrics_collector
        self.error_handler = error_handler
        self._start_time = datetime.now()

    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        uptime = (datetime.now() - self._start_time).total_seconds()
        
        return {
            "status": "healthy",
            "uptime": uptime,
            "active_agents": len(self.registry.list_agents()),
            "total_errors": len(self.error_handler.get_recent_errors()),
            "metrics": self.metrics.get_summary()
        }

    async def get_agent_metrics(self) -> Dict[str, Any]:
        """Get metrics for all agents."""
        metrics = {}
        
        for agent in self.registry.list_agents():
            agent_metrics = self.metrics.get_metrics_by_component(agent)
            metrics[agent] = {
                "status": self.registry.get_agent_status(agent),
                "metrics": agent_metrics
            }
            
        return metrics

    async def get_error_log(self) -> List[Dict[str, Any]]:
        """Get recent error log."""
        return self.error_handler.get_recent_errors()

# Initialize dashboard
dashboard = None

@app.on_event("startup")
async def startup_event():
    """Initialize dashboard on startup."""
    global dashboard
    
    # Initialize core components
    metrics = MetricsCollector()
    error_handler = ErrorHandler()
    registry = AgentRegistry(metrics, error_handler)
    
    dashboard = Dashboard(registry, metrics, error_handler)

@app.get("/")
async def get_dashboard():
    """Serve dashboard HTML."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Arcana Monitoring Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body class="bg-gray-100">
        <div class="container mx-auto px-4 py-8">
            <h1 class="text-3xl font-bold mb-8">Arcana Monitoring Dashboard</h1>
            
            <!-- System Status -->
            <div class="bg-white rounded-lg shadow-md p-6 mb-8">
                <h2 class="text-xl font-semibold mb-4">System Status</h2>
                <div id="system-status"></div>
            </div>
            
            <!-- Agent Metrics -->
            <div class="bg-white rounded-lg shadow-md p-6 mb-8">
                <h2 class="text-xl font-semibold mb-4">Agent Metrics</h2>
                <div id="agent-metrics"></div>
            </div>
            
            <!-- Error Log -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-semibold mb-4">Error Log</h2>
                <div id="error-log"></div>
            </div>
        </div>
        
        <script>
            const ws = new WebSocket(`ws://${window.location.host}/ws`);
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
            
            function updateDashboard(data) {
                // Update system status
                document.getElementById('system-status').innerHTML = `
                    <div class="grid grid-cols-4 gap-4">
                        <div class="p-4 bg-blue-100 rounded-lg">
                            <p class="text-sm text-blue-600">Status</p>
                            <p class="text-2xl font-bold">${data.system.status}</p>
                        </div>
                        <div class="p-4 bg-green-100 rounded-lg">
                            <p class="text-sm text-green-600">Uptime</p>
                            <p class="text-2xl font-bold">${Math.floor(data.system.uptime)}s</p>
                        </div>
                        <div class="p-4 bg-yellow-100 rounded-lg">
                            <p class="text-sm text-yellow-600">Active Agents</p>
                            <p class="text-2xl font-bold">${data.system.active_agents}</p>
                        </div>
                        <div class="p-4 bg-red-100 rounded-lg">
                            <p class="text-sm text-red-600">Total Errors</p>
                            <p class="text-2xl font-bold">${data.system.total_errors}</p>
                        </div>
                    </div>
                `;
                
                // Update agent metrics
                const agentMetrics = document.getElementById('agent-metrics');
                agentMetrics.innerHTML = '';
                
                for (const [agent, metrics] of Object.entries(data.agents)) {
                    agentMetrics.innerHTML += `
                        <div class="mb-4 p-4 border rounded-lg">
                            <h3 class="font-semibold mb-2">${agent}</h3>
                            <p>Status: ${metrics.status.active ? 'Active' : 'Inactive'}</p>
                            <p>Type: ${metrics.status.type}</p>
                            <div class="mt-2">
                                <h4 class="font-semibold">Metrics:</h4>
                                <pre class="bg-gray-100 p-2 rounded mt-1">
                                    ${JSON.stringify(metrics.metrics, null, 2)}
                                </pre>
                            </div>
                        </div>
                    `;
                }
                
                // Update error log
                const errorLog = document.getElementById('error-log');
                errorLog.innerHTML = `
                    <div class="overflow-x-auto">
                        <table class="min-w-full">
                            <thead>
                                <tr class="bg-gray-100">
                                    <th class="px-4 py-2">Time</th>
                                    <th class="px-4 py-2">Component</th>
                                    <th class="px-4 py-2">Error</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.errors.map(error => `
                                    <tr class="border-t">
                                        <td class="px-4 py-2">${new Date(error.timestamp).toLocaleString()}</td>
                                        <td class="px-4 py-2">${error.component}</td>
                                        <td class="px-4 py-2">${error.message}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                `;
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for real-time updates."""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Get latest data
            system_status = await dashboard.get_system_status()
            agent_metrics = await dashboard.get_agent_metrics()
            error_log = await dashboard.get_error_log()
            
            # Send update
            await websocket.send_json({
                "system": system_status,
                "agents": agent_metrics,
                "errors": error_log
            })
            
            # Wait before next update
            await asyncio.sleep(1)
            
    except Exception:
        active_connections.remove(websocket)
        
    finally:
        active_connections.remove(websocket)

def start_dashboard(host: str = "0.0.0.0", port: int = 8000):
    """Start the monitoring dashboard."""
    uvicorn.run(app, host=host, port=port)
