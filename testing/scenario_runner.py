"""Scenario-based testing framework for Arcana workflows."""

from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
import asyncio
import yaml
from pathlib import Path
import json
from datetime import datetime
import pytest
from contextlib import asynccontextmanager

from core.workflow.simulator import WorkflowSimulator, SimulationConfig
from core.monitoring.anomaly_detector import AnomalyDetector
from core.monitoring.ml_detector import MLAnomalyDetector, MLModelConfig
from core.monitoring import MetricsCollector
from core.error_handling import ErrorHandler
from core.feedback_loop import FeedbackLoop

@dataclass
class TestScenario:
    """Definition of a workflow test scenario."""
    
    name: str
    description: str
    workflow_id: str
    mock_data: Dict[str, Any]
    expected_outcomes: Dict[str, Any]
    validation_rules: Dict[str, Callable[[Any], bool]]
    failure_scenarios: Optional[Dict[str, List[Dict[str, Any]]]] = None
    performance_thresholds: Optional[Dict[str, float]] = None
    cleanup_steps: Optional[List[Dict[str, Any]]] = None

@dataclass
class ScenarioResult:
    """Results from running a test scenario."""
    
    scenario: TestScenario
    success: bool
    start_time: datetime
    end_time: Optional[datetime] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)
    validation_failures: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    anomalies: List[Dict[str, Any]] = field(default_factory=list)

class ScenarioRunner:
    """Executes and validates workflow test scenarios."""
    
    def __init__(
        self,
        simulator: WorkflowSimulator,
        anomaly_detector: AnomalyDetector,
        ml_detector: MLAnomalyDetector,
        metrics_collector: MetricsCollector,
        error_handler: ErrorHandler,
        feedback_loop: FeedbackLoop
    ):
        self.simulator = simulator
        self.anomaly_detector = anomaly_detector
        self.ml_detector = ml_detector
        self.metrics = metrics_collector
        self.error_handler = error_handler
        self.feedback_loop = feedback_loop
        
    @staticmethod
    def load_scenario(path: Path) -> TestScenario:
        """Load a test scenario from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
            
        return TestScenario(
            name=data["name"],
            description=data["description"],
            workflow_id=data["workflow_id"],
            mock_data=data["mock_data"],
            expected_outcomes=data["expected_outcomes"],
            validation_rules={},  # Rules need to be defined in code
            failure_scenarios=data.get("failure_scenarios"),
            performance_thresholds=data.get("performance_thresholds"),
            cleanup_steps=data.get("cleanup_steps")
        )
        
    async def run_scenario(self, scenario: TestScenario) -> ScenarioResult:
        """Execute a test scenario."""
        result = ScenarioResult(
            scenario=scenario,
            success=False,
            start_time=datetime.now()
        )
        
        try:
            # Configure simulation
            config = SimulationConfig(
                mock_data=scenario.mock_data,
                failure_scenarios=scenario.failure_scenarios,
                validation_rules=scenario.validation_rules
            )
            
            # Run simulation
            sim_result = await self.simulator.simulate_workflow(
                scenario.workflow_id,
                config
            )
            
            # Validate outcomes
            await self._validate_outcomes(scenario, sim_result, result)
            
            # Check performance
            if scenario.performance_thresholds:
                await self._check_performance(scenario, sim_result, result)
                
            # Run cleanup if needed
            if scenario.cleanup_steps:
                await self._run_cleanup(scenario)
                
            result.success = (
                not result.errors
                and not result.validation_failures
                and not result.anomalies
            )
            
        except Exception as e:
            result.errors.append({
                "type": "execution_error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
        finally:
            result.end_time = datetime.now()
            
        return result
        
    async def _validate_outcomes(
        self,
        scenario: TestScenario,
        sim_result: Any,
        result: ScenarioResult
    ) -> None:
        """Validate scenario outcomes."""
        for step_id, expected in scenario.expected_outcomes.items():
            actual = self._get_step_output(sim_result, step_id)
            
            if not self._compare_outcomes(expected, actual):
                result.validation_failures.append({
                    "step_id": step_id,
                    "expected": expected,
                    "actual": actual,
                    "timestamp": datetime.now().isoformat()
                })
                
    async def _check_performance(
        self,
        scenario: TestScenario,
        sim_result: Any,
        result: ScenarioResult
    ) -> None:
        """Check performance against thresholds."""
        for metric, threshold in scenario.performance_thresholds.items():
            value = self._get_performance_metric(sim_result, metric)
            result.performance_metrics[metric] = value
            
            if value > threshold:
                result.errors.append({
                    "type": "performance_threshold",
                    "metric": metric,
                    "threshold": threshold,
                    "actual": value,
                    "timestamp": datetime.now().isoformat()
                })
                
    async def _run_cleanup(self, scenario: TestScenario) -> None:
        """Execute cleanup steps."""
        for step in scenario.cleanup_steps:
            try:
                if step["type"] == "delete":
                    # Implement cleanup logic
                    pass
            except Exception as e:
                if self.error_handler:
                    await self.error_handler.handle_error(
                        e,
                        {
                            "component": "ScenarioRunner",
                            "operation": "cleanup",
                            "scenario": scenario.name
                        }
                    )
                    
    def _get_step_output(self, sim_result: Any, step_id: str) -> Any:
        """Extract step output from simulation result."""
        for step in sim_result.steps:
            if step["step_id"] == step_id:
                return step["result"].get("output")
        return None
        
    def _get_performance_metric(self, sim_result: Any, metric: str) -> float:
        """Extract performance metric from simulation result."""
        if metric == "total_duration":
            return (sim_result.end_time - sim_result.start_time).total_seconds()
        # Add more metric extractors as needed
        return 0.0
        
    def _compare_outcomes(self, expected: Any, actual: Any) -> bool:
        """Compare expected and actual outcomes."""
        if isinstance(expected, dict):
            return all(
                k in actual and self._compare_outcomes(v, actual[k])
                for k, v in expected.items()
            )
        return expected == actual

@pytest.fixture
async def scenario_runner():
    """Pytest fixture for scenario runner."""
    # Initialize components
    metrics = MetricsCollector()
    error_handler = ErrorHandler()
    feedback_loop = FeedbackLoop(metrics, error_handler)
    
    # Initialize ML detector
    ml_config = MLModelConfig(
        feature_columns=["duration", "memory_mb", "cpu_percent"],
        model_path=Path("models/anomaly_detector.joblib")
    )
    ml_detector = MLAnomalyDetector(ml_config, metrics, error_handler, feedback_loop)
    
    # Initialize other components
    anomaly_detector = AnomalyDetector(metrics, error_handler, feedback_loop)
    simulator = WorkflowSimulator(metrics, error_handler, feedback_loop)
    
    # Create runner
    runner = ScenarioRunner(
        simulator,
        anomaly_detector,
        ml_detector,
        metrics,
        error_handler,
        feedback_loop
    )
    
    yield runner
    
    # Cleanup
    await feedback_loop.shutdown()

async def test_workflow_scenario(scenario_runner: ScenarioRunner, scenario_path: Path):
    """Test a workflow scenario."""
    scenario = ScenarioRunner.load_scenario(scenario_path)
    result = await scenario_runner.run_scenario(scenario)
    
    assert result.success, f"Scenario '{scenario.name}' failed:\n" + \
        "\n".join(f"- {e['message']}" for e in result.errors)
