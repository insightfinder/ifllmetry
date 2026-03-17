# OpenTelemetry Weaviate Instrumentation

<a href="https://pypi.org/project/opentelemetry-if-instrumentation-weaviate/">
    <img src="https://badge.fury.io/py/opentelemetry-instrumentation-weaviate.svg">
</a>

This library allows tracing client-side calls to Weaviate vector DB sent with the official [Weaviate library](https://github.com/weaviate/weaviate-python-client).

## Installation

```bash
pip install opentelemetry-if-instrumentation-weaviate
```

## Example usage

```python
from opentelemetry.instrumentation.weaviate import WeaviateInstrumentor

WeaviateInstrumentor().instrument()
```
