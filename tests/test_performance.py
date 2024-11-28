import pytest
import pytest_asyncio
from agents.last_mile_agent import LastMileAgent
from tools.browser_tool import BrowserTool
from tools.claude_tool import ClaudeTool
import asyncio
import time
import statistics
from typing import List, Dict

class TestPerformance:
    @pytest.fixture
    async def agent(self):
        agent = LastMileAgent()
        agent.register_tool('browser', BrowserTool())
        agent.register_tool('claude', ClaudeTool())
        await agent.initialize()
        yield agent
        await agent.cleanup()

    async def measure_execution_time(self, coro):
        start_time = time.perf_counter()
        result = await coro
        end_time = time.perf_counter()
        return end_time - start_time, result

    @pytest.mark.asyncio
    async def test_parallel_performance(self, agent, monkeypatch, performance_config):
        """Test performance of parallel task execution"""
        execution_times: List[float] = []
        
        async def mock_browser_execute(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate consistent work
            return {'status': 'success'}
        monkeypatch.setattr(BrowserTool, 'execute', mock_browser_execute)
        
        for _ in range(3):  # Run multiple batches for consistent results
            tasks = [
                {
                    'type': 'data_extraction',
                    'url': f'https://example.com/page{i}'
                }
                for i in range(performance_config['concurrent_tasks'])
            ]
            
            execution_time, results = await self.measure_execution_time(
                agent.execute_parallel(tasks)
            )
            execution_times.append(execution_time)
        
        avg_time = statistics.mean(execution_times)
        assert avg_time < 0.2  # Should complete in less than 200ms
        assert len(results) == performance_config['concurrent_tasks']

    @pytest.mark.asyncio
    async def test_memory_usage(self, agent, monkeypatch):
        """Test memory usage during large data processing"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Generate large test data
        large_data = {'data': ['x' * 1000 for _ in range(1000)]}
        
        async def mock_browser_execute(*args, **kwargs):
            return {'status': 'success', 'data': large_data}
        monkeypatch.setattr(BrowserTool, 'execute', mock_browser_execute)
        
        tasks = [
            {
                'type': 'data_extraction',
                'url': f'https://example.com/page{i}'
            }
            for i in range(10)
        ]
        
        await agent.execute_parallel(tasks)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024

    @pytest.mark.asyncio
    async def test_response_time_distribution(self, agent, monkeypatch):
        """Test distribution of response times"""
        response_times: List[float] = []
        
        async def mock_browser_execute(*args, **kwargs):
            # Simulate variable response times
            delay = 0.1 + (0.1 * random.random())
            await asyncio.sleep(delay)
            return {'status': 'success'}
        monkeypatch.setattr(BrowserTool, 'execute', mock_browser_execute)
        
        task = {
            'type': 'data_extraction',
            'url': 'https://example.com'
        }
        
        for _ in range(50):  # Collect 50 samples
            execution_time, _ = await self.measure_execution_time(
                agent.execute_task(task)
            )
            response_times.append(execution_time)
        
        mean_time = statistics.mean(response_times)
        std_dev = statistics.stdev(response_times)
        p95 = sorted(response_times)[int(len(response_times) * 0.95)]
        
        assert mean_time < 0.3  # Average response time under 300ms
        assert std_dev < 0.1   # Standard deviation under 100ms
        assert p95 < 0.4      # 95th percentile under 400ms

    @pytest.mark.asyncio
    async def test_concurrent_resource_usage(self, agent, monkeypatch):
        """Test resource usage under concurrent load"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        cpu_percent = []
        memory_usage = []
        
        async def mock_browser_execute(*args, **kwargs):
            # Simulate CPU-intensive work
            for _ in range(1000000):
                pass
            return {'status': 'success'}
        monkeypatch.setattr(BrowserTool, 'execute', mock_browser_execute)
        
        async def monitor_resources():
            while True:
                cpu_percent.append(process.cpu_percent())
                memory_usage.append(process.memory_info().rss)
                await asyncio.sleep(0.1)
        
        # Start resource monitoring
        monitor_task = asyncio.create_task(monitor_resources())
        
        # Run concurrent tasks
        tasks = [
            {
                'type': 'data_extraction',
                'url': f'https://example.com/page{i}'
            }
            for i in range(performance_config['concurrent_tasks'])
        ]
        
        await agent.execute_parallel(tasks)
        
        # Stop monitoring
        monitor_task.cancel()
        
        avg_cpu = statistics.mean(cpu_percent)
        max_memory = max(memory_usage)
        
        # CPU usage should be reasonable
        assert avg_cpu < 90  # Average CPU usage under 90%
        # Memory should be reasonable
        assert max_memory < 500 * 1024 * 1024  # Max memory under 500MB
