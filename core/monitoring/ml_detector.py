"""Machine learning based anomaly detection for Arcana workflows."""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import joblib
from pathlib import Path
import json
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass, field

from core.monitoring.anomaly_detector import AnomalyDetector, Anomaly, AnomalyType
from core.monitoring import MetricsCollector
from core.error_handling import ErrorHandler
from core.feedback_loop import FeedbackLoop, FeedbackLevel

@dataclass
class MLModelConfig:
    """Configuration for ML-based anomaly detection."""
    
    # Feature extraction
    feature_columns: List[str]
    time_window: timedelta = timedelta(hours=1)
    min_samples: int = 100
    
    # Isolation Forest params
    contamination: float = 0.1
    n_estimators: int = 100
    
    # Dimensionality reduction
    use_pca: bool = True
    pca_components: int = 3
    
    # Model persistence
    model_path: Optional[Path] = None
    
    # Online learning
    enable_online_learning: bool = True
    retraining_interval: timedelta = timedelta(hours=24)
    
    # Prediction thresholds
    anomaly_probability_threshold: float = 0.8
    novelty_threshold: float = 0.9

class MLAnomalyDetector:
    """ML-powered anomaly detection system."""
    
    def __init__(
        self,
        config: MLModelConfig,
        metrics_collector: MetricsCollector,
        error_handler: Optional[ErrorHandler] = None,
        feedback_loop: Optional[FeedbackLoop] = None
    ):
        self.config = config
        self.metrics = metrics_collector
        self.error_handler = error_handler
        self.feedback_loop = feedback_loop
        
        # Initialize components
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=config.pca_components) if config.use_pca else None
        self.model = IsolationForest(
            contamination=config.contamination,
            n_estimators=config.n_estimators,
            random_state=42
        )
        
        # Data storage
        self._feature_history: List[Dict[str, float]] = []
        self._last_training: Optional[datetime] = None
        self._training_lock = asyncio.Lock()
        
        # Load existing model if available
        if config.model_path and config.model_path.exists():
            self._load_model()
            
    async def process_metrics(
        self,
        workflow_id: str,
        step_id: str,
        metrics: Dict[str, Any]
    ) -> List[Anomaly]:
        """Process new metrics and detect anomalies."""
        try:
            # Extract features
            features = self._extract_features(metrics)
            if not features:
                return []
                
            # Store for training
            self._feature_history.append(features)
            
            # Check if we need to retrain
            await self._check_retrain()
            
            # Detect anomalies
            anomalies = await self._detect_anomalies(
                workflow_id,
                step_id,
                features
            )
            
            # Report anomalies
            if anomalies and self.feedback_loop:
                await self._report_anomalies(workflow_id, anomalies)
                
            return anomalies
            
        except Exception as e:
            if self.error_handler:
                await self.error_handler.handle_error(
                    e,
                    {
                        "component": "MLAnomalyDetector",
                        "operation": "process_metrics",
                        "workflow_id": workflow_id,
                        "step_id": step_id
                    }
                )
            raise
            
    def _extract_features(self, metrics: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """Extract relevant features from metrics."""
        features = {}
        for col in self.config.feature_columns:
            if col not in metrics:
                return None
            features[col] = float(metrics[col])
        return features
        
    async def _check_retrain(self) -> None:
        """Check if model needs retraining."""
        if not self.config.enable_online_learning:
            return
            
        now = datetime.now()
        if (
            len(self._feature_history) >= self.config.min_samples
            and (
                not self._last_training
                or now - self._last_training >= self.config.retraining_interval
            )
        ):
            async with self._training_lock:
                await self._train_model()
                
    async def _train_model(self) -> None:
        """Train the anomaly detection model."""
        if len(self._feature_history) < self.config.min_samples:
            return
            
        # Prepare training data
        X = np.array([
            list(features.values())
            for features in self._feature_history
        ])
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Apply PCA if enabled
        if self.config.use_pca:
            X_scaled = self.pca.fit_transform(X_scaled)
            
        # Train model
        self.model.fit(X_scaled)
        self._last_training = datetime.now()
        
        # Save model if path configured
        if self.config.model_path:
            self._save_model()
            
    async def _detect_anomalies(
        self,
        workflow_id: str,
        step_id: str,
        features: Dict[str, float]
    ) -> List[Anomaly]:
        """Detect anomalies in new data point."""
        if not self._last_training:
            return []
            
        # Prepare input
        X = np.array([list(features.values())])
        X_scaled = self.scaler.transform(X)
        
        if self.config.use_pca:
            X_scaled = self.pca.transform(X_scaled)
            
        # Get predictions
        scores = self.model.score_samples(X_scaled)
        predictions = self.model.predict(X_scaled)
        
        anomalies = []
        
        # Check for anomalies
        if predictions[0] == -1:  # Isolation Forest anomaly
            prob = np.exp(scores[0])  # Convert score to probability
            if prob < self.config.anomaly_probability_threshold:
                anomalies.append(
                    Anomaly(
                        type=AnomalyType.PATTERN,
                        workflow_id=workflow_id,
                        step_id=step_id,
                        timestamp=datetime.now(),
                        description="ML model detected unusual pattern in metrics",
                        severity=1.0 - prob,
                        data={
                            "features": features,
                            "anomaly_score": float(scores[0]),
                            "probability": float(prob)
                        }
                    )
                )
                
        return anomalies
        
    async def _report_anomalies(
        self,
        workflow_id: str,
        anomalies: List[Anomaly]
    ) -> None:
        """Report detected anomalies."""
        for anomaly in anomalies:
            await self.feedback_loop.emit(
                task_id=workflow_id,
                level=FeedbackLevel.WARNING,
                message=f"ML-detected anomaly: {anomaly.description}",
                details={
                    "anomaly_type": "ml_pattern",
                    "severity": anomaly.severity,
                    "data": anomaly.data
                }
            )
            
    def _save_model(self) -> None:
        """Save model and preprocessing components."""
        if not self.config.model_path:
            return
            
        model_dir = self.config.model_path.parent
        model_dir.mkdir(parents=True, exist_ok=True)
        
        joblib.dump(
            {
                "model": self.model,
                "scaler": self.scaler,
                "pca": self.pca,
                "config": self.config,
                "last_training": self._last_training
            },
            self.config.model_path
        )
        
    def _load_model(self) -> None:
        """Load saved model and preprocessing components."""
        if not self.config.model_path.exists():
            return
            
        saved = joblib.load(self.config.model_path)
        self.model = saved["model"]
        self.scaler = saved["scaler"]
        self.pca = saved["pca"]
        self._last_training = saved["last_training"]
