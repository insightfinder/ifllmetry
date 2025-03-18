# Please don't import this package directly
Instead, import [iftracer-sdk](https://github.com/insightfinder/iftracer-sdk) directly. [iftracer-sdk](https://github.com/insightfinder/iftracer-sdk) will use the opentelemetry-* pkgs in this repository.

* Why do we need this package: This package provides general tags generation. e.g.: .input or .output is generated from this package. Spans like openai.chat is generated from [packages/opentelemetry-instrumentation-openai](packages/opentelemetry-instrumentation-openai)
* Why don't we use the repository that includes the latest opentelemetry-* packages: That will cause dependency issues when opentelemetry-* packages get updated. We should manage opentelemetry-* packages and update it when we are ready.

## description
Iftracer is a set of extensions built on top of [OpenTelemetry](https://opentelemetry.io/) that gives you complete observability over your LLM application. Because it uses OpenTelemetry under the hood, it can be connected to your existing observability solutions - Datadog, Honeycomb, and others.

It's built and maintained by Iftracer under the Apache 2.0 license.

The repo contains standard OpenTelemetry instrumentations for LLM providers and Vector DBs, as well as a Iftracer SDK that makes it easy to get started with OpenLLMetry, while still outputting standard OpenTelemetry data that can be connected to your observability stack.
If you already have OpenTelemetry instrumented, you can just add any of our instrumentations directly.

## 🚀 Getting Started

Install the SDK into your project:

```python
pip install iftracer-sdk
```

To start instrumenting your code, just add this line to your code:

```js
const iftracer = new Iftracer();

await iftracer.axiosInstance.post("http://my.awesome.website/orders/create");
await iftracer.fetchTraces();

expectTrace(iftracer.serviceByName("emails-service"))
  .toReceiveHttpRequest()
  .ofMethod("POST")
  .withBody({ emailTemplate: "orderCreated", itemId: "123" });

More info can be found in our [docs](https://iftracer.com/docs/python-sdk/getting-started).

## What do we instrument?

OpenLLMetry can instrument everything that [OpenTelemetry already instruments](https://github.com/open-telemetry/opentelemetry-python-contrib/tree/main/instrumentation) - so things like your DB, API calls, and more. On top of that, we built a set of custom extensions that instrument things like your calls to OpenAI or Anthropic, or your Vector DB like Pinecone, Chroma, or Weaviate.

### LLM Providers

- [ ] OpenAI / Azure OpenAI
- [ ] Anthropic
- [ ] Cohere
- [ ] Replicate
- [ ] Vertex AI (GCP)
- [ ] Bedrock (AWS)
- [ ] Ollama
- [ ] Hugging-Face

### Vector DBs

- [ ] Pinecone
- [ ] Chroma
- [ ] Weaviate
- [ ] Pgvector

