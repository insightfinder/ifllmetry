# OpenTelemetry Together AI Instrumentation

<a href="https://pypi.org/project/opentelemetry-if-instrumentation-together/">
    <img src="https://badge.fury.io/py/opentelemetry-instrumentation-together.svg">
</a>

This library allows tracing calls to any of Together AI's endpoints sent with the official [Together AI Library](https://github.com/togethercomputer/together-python).

## Installation

```bash
pip install opentelemetry-if-instrumentation-together
```

## Example usage

```python
from opentelemetry.instrumentation.together import TogetherAiInstrumentor

TogetherAiInstrumentor().instrument()
```

## Privacy

**By default, this instrumentation logs prompts, completions, and embeddings to span attributes**. This gives you a clear visibility into how your LLM application is working, and can make it easy to debug and evaluate the quality of the outputs.

However, you may want to disable this logging for privacy reasons, as they may contain highly sensitive data from your users. You may also simply want to reduce the size of your traces.

To disable logging, set the `IFTRACER_TRACE_CONTENT` environment variable to `false`.

```bash
IFTRACER_TRACE_CONTENT=false
```
