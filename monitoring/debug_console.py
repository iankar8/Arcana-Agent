"""Interactive debugging console for Arcana workflows."""

from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime
import json
from pathlib import Path
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from core.agent_registry import AgentRegistry
from core.monitoring import MetricsCollector
from core.error_handling import ErrorHandler
from core.feedback_loop import FeedbackLoop, FeedbackEvent
from core.workflow.executor import WorkflowExecutor, WorkflowState
from core.ml_anomaly_detector import MLAnomalyDetector
from core.scenario_runner import ScenarioRunner

class WorkflowPlayback:
    """Manages workflow state recording and playback."""
    
    def __init__(self):
        self.workflow_states: Dict[str, List[Dict[str, Any]]] = {}
        self.current_positions: Dict[str, int] = {}
    
    def record_state(self, workflow_id: str, state: Dict[str, Any]) -> None:
        """Record a workflow state."""
        if workflow_id not in self.workflow_states:
            self.workflow_states[workflow_id] = []
            self.current_positions[workflow_id] = 0
            
        self.workflow_states[workflow_id].append({
            "timestamp": datetime.now().isoformat(),
            "state": state
        })
    
    def get_state_at_position(self, workflow_id: str, position: int) -> Optional[Dict[str, Any]]:
        """Get workflow state at a specific position."""
        if workflow_id not in self.workflow_states:
            return None
            
        states = self.workflow_states[workflow_id]
        if 0 <= position < len(states):
            return states[position]
        return None
    
    def get_current_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current workflow state."""
        return self.get_state_at_position(
            workflow_id,
            self.current_positions.get(workflow_id, 0)
        )
    
    def move_position(self, workflow_id: str, steps: int) -> bool:
        """Move playback position forward or backward."""
        if workflow_id not in self.current_positions:
            return False
            
        new_pos = self.current_positions[workflow_id] + steps
        if 0 <= new_pos < len(self.workflow_states[workflow_id]):
            self.current_positions[workflow_id] = new_pos
            return True
        return False

class AgentDependencyGraph:
    """Tracks and visualizes agent dependencies."""
    
    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        
    def add_agent(self, agent_id: str, metadata: Dict[str, Any]) -> None:
        """Add an agent node to the graph."""
        self.nodes[agent_id] = {
            "id": agent_id,
            "type": metadata.get("type", "unknown"),
            "status": metadata.get("status", "unknown"),
            "metadata": metadata
        }
        
    def add_interaction(
        self,
        from_agent: str,
        to_agent: str,
        interaction_type: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Record an interaction between agents."""
        self.edges.append({
            "source": from_agent,
            "target": to_agent,
            "type": interaction_type,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata
        })
        
    def get_graph_data(self) -> Dict[str, Any]:
        """Get graph data in D3.js compatible format."""
        return {
            "nodes": list(self.nodes.values()),
            "edges": self.edges
        }

class DebugConsole:
    """Enhanced debug console with ML-powered insights and scenario testing."""
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        error_handler: ErrorHandler,
        feedback_loop: FeedbackLoop,
        ml_detector: MLAnomalyDetector,
        scenario_runner: ScenarioRunner
    ):
        self.metrics = metrics_collector
        self.error_handler = error_handler
        self.feedback_loop = feedback_loop
        self.ml_detector = ml_detector
        self.scenario_runner = scenario_runner
        
        # WebSocket connections
        self._clients = set()
        self._lock = asyncio.Lock()
        
        # State tracking
        self._workflow_states = {}
        self._anomalies = []
        self._active_scenarios = {}
        
    async def start(self):
        """Start the debug console server."""
        app = FastAPI()
        
        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self._handle_client_connection(websocket)
            
        @app.get("/workflows")
        async def get_workflows():
            return {"workflows": list(self._workflow_states.values())}
            
        @app.get("/anomalies")
        async def get_anomalies():
            return {"anomalies": self._anomalies}
            
        @app.get("/scenarios")
        async def get_scenarios():
            return {"scenarios": list(self._active_scenarios.values())}
            
        @app.post("/run-scenario")
        async def run_scenario(scenario_path: str):
            return await self._run_scenario(Path(scenario_path))
            
        # Start server
        uvicorn.run(app, host="0.0.0.0", port=8000)
        
    async def _handle_client_connection(self, websocket: WebSocket):
        """Handle new WebSocket client connection."""
        await websocket.accept()
        async with self._lock:
            self._clients.add(websocket)
            
        try:
            while True:
                data = await websocket.receive_json()
                await self._handle_client_message(websocket, data)
        finally:
            async with self._lock:
                self._clients.remove(websocket)
                
    async def _handle_client_message(self, websocket: WebSocket, data: Dict[str, Any]):
        """Handle incoming client message."""
        msg_type = data.get("type")
        if not msg_type:
            return
            
        if msg_type == "subscribe":
            # Handle subscription to specific workflow/component
            pass
        elif msg_type == "command":
            # Handle debug command
            await self._handle_debug_command(websocket, data)
            
    async def _handle_debug_command(self, websocket: WebSocket, data: Dict[str, Any]):
        """Handle debug command from client."""
        command = data.get("command")
        if not command:
            return
            
        if command == "pause":
            # Implement workflow pause
            pass
        elif command == "resume":
            # Implement workflow resume
            pass
        elif command == "step":
            # Implement step-by-step execution
            pass
        elif command == "inspect":
            # Implement state inspection
            pass
            
    async def _run_scenario(self, scenario_path: Path) -> Dict[str, Any]:
        """Run a test scenario."""
        try:
            scenario = ScenarioRunner.load_scenario(scenario_path)
            result = await self.scenario_runner.run_scenario(scenario)
            
            self._active_scenarios[scenario.workflow_id] = {
                "scenario": scenario,
                "result": result,
                "status": "completed" if result.success else "failed"
            }
            
            return {
                "success": result.success,
                "errors": result.errors,
                "validation_failures": result.validation_failures,
                "performance_metrics": result.performance_metrics,
                "anomalies": result.anomalies
            }
            
        except Exception as e:
            if self.error_handler:
                await self.error_handler.handle_error(
                    e,
                    {
                        "component": "DebugConsole",
                        "operation": "run_scenario",
                        "scenario_path": str(scenario_path)
                    }
                )
            return {
                "success": False,
                "error": str(e)
            }
            
    async def broadcast_update(self, data: Dict[str, Any]):
        """Broadcast update to all connected clients."""
        async with self._lock:
            for client in self._clients:
                try:
                    await client.send_json(data)
                except Exception as e:
                    if self.error_handler:
                        await self.error_handler.handle_error(
                            e,
                            {
                                "component": "DebugConsole",
                                "operation": "broadcast_update"
                            }
                        )
                        
    async def update_workflow_state(
        self,
        workflow_id: str,
        state: Dict[str, Any]
    ):
        """Update workflow state and notify clients."""
        self._workflow_states[workflow_id] = state
        await self.broadcast_update({
            "type": "workflow_update",
            "workflow_id": workflow_id,
            "state": state
        })
        
    async def record_anomaly(self, anomaly: Dict[str, Any]):
        """Record detected anomaly and notify clients."""
        self._anomalies.append(anomaly)
        await self.broadcast_update({
            "type": "anomaly_detected",
            "anomaly": anomaly
        })

# Initialize console
debug_console = None

app = FastAPI(title="Arcana Debug Console")

# Mount static files
static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

@app.on_event("startup")
async def startup_event():
    """Initialize debug console on startup."""
    global debug_console
    
    # Initialize core components
    metrics = MetricsCollector()
    error_handler = ErrorHandler()
    registry = AgentRegistry(metrics, error_handler)
    feedback_loop = FeedbackLoop(metrics, error_handler)
    ml_detector = MLAnomalyDetector()
    scenario_runner = ScenarioRunner()
    
    debug_console = DebugConsole(metrics, error_handler, feedback_loop, ml_detector, scenario_runner)
    
    # Subscribe to feedback events
    feedback_loop.subscribe(debug_console.handle_feedback)

@app.get("/")
async def get_console():
    """Serve debug console HTML."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Arcana Debug Console</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/prismjs@1.24.1/themes/prism.css" rel="stylesheet" />
        <script src="https://cdn.jsdelivr.net/npm/prismjs@1.24.1/prism.js"></script>
        <style>
            .task-tree {
                font-family: monospace;
                padding: 1rem;
            }
            .task-node {
                margin-left: 2rem;
                position: relative;
            }
            .task-node::before {
                content: "├─";
                position: absolute;
                left: -1.5rem;
            }
        </style>
    </head>
    <body class="bg-gray-100">
        <div class="container mx-auto px-4 py-8">
            <div class="flex justify-between items-center mb-8">
                <h1 class="text-3xl font-bold">Arcana Debug Console</h1>
                <div class="space-x-4">
                    <button id="clear-btn" class="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600">
                        Clear Console
                    </button>
                    <button id="export-btn" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                        Export Logs
                    </button>
                </div>
            </div>
            
            <!-- Task Tree View -->
            <div class="bg-white rounded-lg shadow-md p-6 mb-8">
                <h2 class="text-xl font-semibold mb-4">Active Tasks</h2>
                <div id="task-tree" class="task-tree"></div>
            </div>
            
            <!-- Real-time Feedback -->
            <div class="bg-white rounded-lg shadow-md p-6 mb-8">
                <h2 class="text-xl font-semibold mb-4">Real-time Feedback</h2>
                <div id="feedback-log" class="space-y-2"></div>
            </div>
            
            <!-- Task Details -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-semibold mb-4">Task Details</h2>
                <div id="task-details">
                    <p class="text-gray-500">Select a task to view details</p>
                </div>
            </div>
            
            <!-- Workflow Playback -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-semibold mb-4">Workflow Playback</h2>
                <div id="workflow-playback">
                    <button id="playback-prev-btn" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                        Previous
                    </button>
                    <button id="playback-next-btn" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                        Next
                    </button>
                    <div id="playback-state"></div>
                </div>
            </div>
            
            <!-- Dependency Graph -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-semibold mb-4">Dependency Graph</h2>
                <div id="dependency-graph"></div>
            </div>
        </div>
        
        <script>
            const ws = new WebSocket(`ws://${window.location.host}/ws`);
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleMessage(data);
            };
            
            function handleMessage(data) {
                if (data.type === 'feedback') {
                    addFeedbackEntry(data.data);
                } else if (data.type === 'task_update') {
                    updateTaskTree(data.data);
                } else if (data.type === 'workflow_update') {
                    updateWorkflowPlayback(data.data);
                    updateDependencyGraph(data.data);
                }
            }
            
            function addFeedbackEntry(feedback) {
                const feedbackLog = document.getElementById('feedback-log');
                
                const entry = document.createElement('div');
                entry.className = `p-4 rounded ${getFeedbackClass(feedback.level)}`;
                
                entry.innerHTML = `
                    <div class="flex justify-between items-start">
                        <div>
                            <span class="font-semibold">[${feedback.level}]</span>
                            <span>${feedback.message}</span>
                        </div>
                        <span class="text-sm text-gray-500">
                            ${new Date(feedback.timestamp).toLocaleTimeString()}
                        </span>
                    </div>
                    ${feedback.requires_response ? createResponseUI(feedback) : ''}
                `;
                
                feedbackLog.insertBefore(entry, feedbackLog.firstChild);
            }
            
            function getFeedbackClass(level) {
                switch (level) {
                    case 'error': return 'bg-red-100';
                    case 'warning': return 'bg-yellow-100';
                    case 'suggestion': return 'bg-purple-100';
                    case 'info': return 'bg-blue-100';
                    default: return 'bg-gray-100';
                }
            }
            
            function createResponseUI(feedback) {
                if (!feedback.response_options) {
                    return `
                        <div class="mt-2">
                            <input type="text" class="border rounded px-2 py-1 mr-2" placeholder="Enter response...">
                            <button onclick="submitResponse('${feedback.id}')" class="px-3 py-1 bg-blue-500 text-white rounded">
                                Submit
                            </button>
                        </div>
                    `;
                }
                
                return `
                    <div class="mt-2 space-x-2">
                        ${feedback.response_options.map(option => `
                            <button onclick="submitResponse('${feedback.id}', '${option}')"
                                    class="px-3 py-1 bg-blue-500 text-white rounded">
                                ${option}
                            </button>
                        `).join('')}
                    </div>
                `;
            }
            
            function submitResponse(eventId, response) {
                ws.send(JSON.stringify({
                    type: 'response',
                    event_id: eventId,
                    response: response
                }));
            }
            
            document.getElementById('clear-btn').onclick = function() {
                document.getElementById('feedback-log').innerHTML = '';
            };
            
            document.getElementById('export-btn').onclick = function() {
                // TODO: Implement log export
            };
            
            document.getElementById('playback-prev-btn').onclick = function() {
                ws.send(JSON.stringify({
                    type: 'playback_prev'
                }));
            };
            
            document.getElementById('playback-next-btn').onclick = function() {
                ws.send(JSON.stringify({
                    type: 'playback_next'
                }));
            };
            
            function updateWorkflowPlayback(data) {
                const playbackState = document.getElementById('playback-state');
                playbackState.innerHTML = `
                    <p>Workflow ID: ${data.workflow_id}</p>
                    <p>Current State: ${data.state.status}</p>
                `;
            }
            
            function updateDependencyGraph(data) {
                const graph = document.getElementById('dependency-graph');
                graph.innerHTML = `
                    <svg width="100%" height="100%"></svg>
                `;
                
                const svg = graph.querySelector('svg');
                const nodes = data.graph.nodes;
                const edges = data.graph.edges;
                
                // Draw nodes
                nodes.forEach(node => {
                    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                    circle.setAttribute('cx', Math.random() * 100);
                    circle.setAttribute('cy', Math.random() * 100);
                    circle.setAttribute('r', 10);
                    circle.setAttribute('fill', 'blue');
                    svg.appendChild(circle);
                    
                    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                    text.setAttribute('x', Math.random() * 100);
                    text.setAttribute('y', Math.random() * 100);
                    text.textContent = node.id;
                    svg.appendChild(text);
                });
                
                // Draw edges
                edges.forEach(edge => {
                    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                    line.setAttribute('x1', Math.random() * 100);
                    line.setAttribute('y1', Math.random() * 100);
                    line.setAttribute('x2', Math.random() * 100);
                    line.setAttribute('y2', Math.random() * 100);
                    line.setAttribute('stroke', 'black');
                    svg.appendChild(line);
                });
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections."""
    await websocket.accept()
    debug_console._clients.add(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "response":
                debug_console.feedback_loop.submit_response(
                    data["event_id"],
                    data["response"]
                )
            elif data["type"] == "playback_prev":
                debug_console.playback.move_position(data["workflow_id"], -1)
            elif data["type"] == "playback_next":
                debug_console.playback.move_position(data["workflow_id"], 1)
                
    except WebSocketDisconnect:
        debug_console._clients.remove(websocket)

@app.get("/api/tasks/{task_id}")
async def get_task_details(task_id: str):
    """Get detailed information about a task."""
    details = await debug_console.get_task_details(task_id)
    if not details:
        return {"error": "Task not found"}
    return details

def start_console(host: str = "0.0.0.0", port: int = 8001):
    """Start the debug console."""
    uvicorn.run(app, host=host, port=port)
