# API Reference

## LastMileAgent

### Core Methods

#### `__init__(config: Dict[str, Any] = None)`
Initialize a new LastMileAgent instance.

```python
agent = LastMileAgent({
    "browser_type": "playwright",
    "headless": True
})
```

#### `async execute_task(task: Dict[str, Any]) -> Dict[str, Any]`
Execute a single automation task.

```python
result = await agent.execute_task({
    "type": "form_filling",
    "url": "https://example.com/form",
    "data": {
        "name": "John Doe",
        "email": "john@example.com"
    }
})
```

#### `async execute_parallel(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]`
Execute multiple tasks in parallel.

```python
results = await agent.execute_parallel([
    {"type": "data_extraction", "url": "https://site1.com"},
    {"type": "data_extraction", "url": "https://site2.com"}
])
```

### Strategy Management

#### `add_strategy(name: str, strategy: Strategy) -> None`
Register a new strategy.

```python
agent.add_strategy("custom", CustomStrategy())
```

#### `remove_strategy(name: str) -> None`
Remove a registered strategy.

```python
agent.remove_strategy("custom")
```

## Strategy Base Class

### Methods to Implement

#### `async execute(task: Dict[str, Any]) -> Dict[str, Any]`
Main execution method for the strategy.

```python
class CustomStrategy(Strategy):
    async def execute(self, task):
        # Implementation
        return {"status": "success", "data": result}
```

#### `async validate(task: Dict[str, Any]) -> bool`
Validate if the strategy can handle the task.

```python
async def validate(self, task):
    return "required_field" in task
```

## Tool System

### Browser Tools

#### `async navigate(url: str) -> None`
Navigate to a URL.

```python
await browser_tool.navigate("https://example.com")
```

#### `async find_element(selector: str) -> Element`
Find an element using various selection strategies.

```python
element = await browser_tool.find_element({
    "type": "css",
    "value": "#login-button"
})
```

### AI Tools

#### `async analyze_page(html: str) -> Dict[str, Any]`
Analyze page content using Claude API.

```python
analysis = await ai_tool.analyze_page(html_content)
```

#### `async generate_strategy(task: Dict[str, Any]) -> str`
Generate execution strategy for a task.

```python
strategy = await ai_tool.generate_strategy({
    "type": "form_filling",
    "complexity": "high"
})
```
