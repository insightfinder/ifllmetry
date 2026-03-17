# OpenTelemetry Milvus Instrumentation

<a href="https://pypi.org/project/opentelemetry-if-instrumentation-milvus/">
    <img src="https://badge.fury.io/py/opentelemetry-instrumentation-milvus.svg">
</a>

This library allows tracing client-side calls to Milvus vector DB sent with the official [Milvus library](https://github.com/milvus-io/milvus).

## Installation

```bash
pip install opentelemetry-if-instrumentation-milvus
```

## Example usage

```python
from opentelemetry.instrumentation.milvus import MilvusInstrumentor

MilvusInstrumentor().instrument()
```
