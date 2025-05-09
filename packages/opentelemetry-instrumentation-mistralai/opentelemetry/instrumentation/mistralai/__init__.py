"""OpenTelemetry Mistral AI instrumentation"""

import logging
import os
import json
from typing import Collection
from opentelemetry.instrumentation.mistralai.config import Config
from opentelemetry.instrumentation.mistralai.utils import dont_throw
from wrapt import wrap_function_wrapper

from opentelemetry import context as context_api
from opentelemetry.trace import get_tracer, SpanKind
from opentelemetry.trace.status import Status, StatusCode

from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.instrumentation.utils import (
    _SUPPRESS_INSTRUMENTATION_KEY,
    unwrap,
)

from opentelemetry.semconv.ai import (
    SUPPRESS_LANGUAGE_MODEL_INSTRUMENTATION_KEY,
    SpanAttributes,
    LLMRequestTypeValues,
)
from opentelemetry.instrumentation.mistralai.version import __version__


from mistralai import Mistral, UserMessage, AssistantMessage
from mistralai.models.chatcompletionresponse import ChatCompletionResponse
from mistralai.models.chatcompletionchoice import ChatCompletionChoice
from mistralai.models.usageinfo import UsageInfo

logger = logging.getLogger(__name__)

_instruments = ("mistralai >= 1.0.0, < 2",)

WRAPPED_METHODS = [
    {
        "method": "complete",
        "span_name": "mistralai.chat",
        "streaming": False,
    },
    {
        "method": "stream",
        "span_name": "mistralai.chat",
        "streaming": True,
    }
]

WRAPPED_METHODS_ASYNC = [
    {
        "method": "complete_async",
        "span_name": "mistralai.chat",
        "streaming": False,
    },
    {
        "method": "stream_async",
        "span_name": "mistralai.chat",
        "streaming": True,
    }
]

WRAPPED_METHODS_EMBED = [
    {
        "method": "create",
        "span_name": "mistralai.embeddings",
        "streaming": False,
    },
    {
        "method": "create_async",
        "span_name": "mistralai.embeddings",
        "streaming": False,
    }
]



def should_send_prompts():
    return (
        os.getenv("IFTRACER_TRACE_CONTENT") or "true"
    ).lower() == "true" or context_api.get_value("override_enable_content_tracing")


def _set_span_attribute(span, name, value):
    if value is not None:
        if value != "":
            span.set_attribute(name, value)
    return


@dont_throw
def _set_input_attributes(span, llm_request_type, to_wrap, kwargs):
    _set_span_attribute(span, SpanAttributes.LLM_REQUEST_MODEL, kwargs.get("model"))
    _set_span_attribute(
        span,
        SpanAttributes.LLM_IS_STREAMING,
        to_wrap.get("streaming"),
    )

    if should_send_prompts():
        if llm_request_type == LLMRequestTypeValues.CHAT:
            _set_span_attribute(span, f"{SpanAttributes.LLM_PROMPTS}.0.role", "user")
            for index, message in enumerate(kwargs.get("messages")):
                _set_span_attribute(
                    span,
                    f"{SpanAttributes.LLM_PROMPTS}.{index}.content",
                    message.content,
                )
                _set_span_attribute(
                    span,
                    f"{SpanAttributes.LLM_PROMPTS}.{index}.role",
                    message.role,
                )
        else:
            inputs = kwargs.get("inputs")

            if isinstance(inputs, str):
                _set_span_attribute(
                    span, f"{SpanAttributes.LLM_PROMPTS}.0.role", "user"
                )
                _set_span_attribute(
                    span, f"{SpanAttributes.LLM_PROMPTS}.0.content", inputs
                )
            else:
                for index, prompt in enumerate(inputs):
                    _set_span_attribute(
                        span,
                        f"{SpanAttributes.LLM_PROMPTS}.{index}.role",
                        "user",
                    )
                    _set_span_attribute(
                        span,
                        f"{SpanAttributes.LLM_PROMPTS}.{index}.content",
                        prompt,
                    )


@dont_throw
def _set_response_attributes(span, llm_request_type, response):
    if llm_request_type == LLMRequestTypeValues.EMBEDDING:
        return

    if should_send_prompts():
        for index, choice in enumerate(response.choices):
            prefix = f"{SpanAttributes.LLM_COMPLETIONS}.{index}"
            _set_span_attribute(
                span,
                f"{prefix}.finish_reason",
                choice.finish_reason,
            )
            _set_span_attribute(
                span,
                f"{prefix}.content",
                (
                    choice.message.content
                    if isinstance(choice.message.content, str)
                    else json.dumps(choice.message.content)
                ),
            )
            _set_span_attribute(
                span,
                f"{prefix}.role",
                choice.message.role,
            )

    _set_span_attribute(span, SpanAttributes.LLM_RESPONSE_MODEL, response.model)

    if not response.usage:
        return

    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens or 0
    total_tokens = response.usage.total_tokens

    _set_span_attribute(
        span,
        SpanAttributes.LLM_USAGE_TOTAL_TOKENS,
        total_tokens,
    )
    _set_span_attribute(
        span,
        SpanAttributes.LLM_USAGE_COMPLETION_TOKENS,
        output_tokens,
    )
    _set_span_attribute(
        span,
        SpanAttributes.LLM_USAGE_PROMPT_TOKENS,
        input_tokens,
    )


def _accumulate_streaming_response(span, llm_request_type, response):
    accumulated_response = ChatCompletionResponse(
        id="",
        object="",
        created=0,
        model="",
        choices=[],
        usage=UsageInfo(prompt_tokens=0, total_tokens=0, completion_tokens=0),
    )

    for res in response:
        yield res

        if res.data.model:
            accumulated_response.model = res.data.model
        if res.data.usage:
            accumulated_response.usage = res.data.usage

        for idx, choice in enumerate(res.data.choices):
            if len(accumulated_response.choices) <= idx:
                accumulated_response.choices.append(
                    ChatCompletionChoice(
                        index=idx,
                        message=AssistantMessage(role="assistant", content=""),
                        finish_reason=None,
                    )
                )

            accumulated_response.choices[idx].finish_reason = choice.finish_reason
            accumulated_response.choices[idx].message.content += choice.delta.content
            accumulated_response.choices[idx].message.role = choice.delta.role

    _set_response_attributes(span, llm_request_type, accumulated_response)
    span.end()


async def _aaccumulate_streaming_response(span, llm_request_type, response):
    accumulated_response = ChatCompletionResponse(
        id="",
        object="",
        created=0,
        model="",
        choices=[],
        usage=UsageInfo(prompt_tokens=0, total_tokens=0, completion_tokens=0),
    )

    async_response = await response

    async for res in async_response:
        yield res

        if res.data.model:
            accumulated_response.model = res.data.model
        if res.data.usage:
            accumulated_response.usage = res.data.usage

        for idx, choice in enumerate(res.data.choices):
            if len(accumulated_response.choices) <= idx:
                accumulated_response.choices.append(
                    ChatCompletionChoice(
                        index=idx,
                        message=AssistantMessage(role="assistant", content=""),
                        finish_reason=None,
                    )
                )

            accumulated_response.choices[idx].finish_reason = choice.finish_reason
            accumulated_response.choices[idx].message.content += choice.delta.content
            accumulated_response.choices[idx].message.role = choice.delta.role

    _set_response_attributes(span, llm_request_type, accumulated_response)
    span.end()


def _with_tracer_wrapper(func):
    """Helper for providing tracer for wrapper functions."""

    def _with_tracer(tracer, to_wrap):
        def wrapper(wrapped, instance, args, kwargs):
            return func(tracer, to_wrap, wrapped, instance, args, kwargs)

        return wrapper

    return _with_tracer


def _llm_request_type_by_method(method_name):
    if method_name == "complete" or method_name == "stream" or method_name == "complete_async" or method_name == "stream_async":
        return LLMRequestTypeValues.CHAT
    elif method_name == "create" or method_name == "create_async":
        return LLMRequestTypeValues.EMBEDDING
    else:
        return LLMRequestTypeValues.UNKNOWN


@_with_tracer_wrapper
def _wrap(tracer, to_wrap, wrapped, instance, args, kwargs):
    """Instruments and calls every function defined in TO_WRAP."""
    if context_api.get_value(_SUPPRESS_INSTRUMENTATION_KEY) or context_api.get_value(
        SUPPRESS_LANGUAGE_MODEL_INSTRUMENTATION_KEY
    ):
        return wrapped(*args, **kwargs)

    name = to_wrap.get("span_name")
    llm_request_type = _llm_request_type_by_method(to_wrap.get("method"))
    span = tracer.start_span(
        name,
        kind=SpanKind.CLIENT,
        attributes={
            SpanAttributes.LLM_SYSTEM: "MistralAI",
            SpanAttributes.LLM_REQUEST_TYPE: llm_request_type.value,
        },
    )
    if span.is_recording():
        _set_input_attributes(span, llm_request_type, to_wrap, kwargs)

    response = wrapped(*args, **kwargs)

    if response:
        if span.is_recording():
            if to_wrap.get("streaming"):
                return _accumulate_streaming_response(span, llm_request_type, response)

            _set_response_attributes(span, llm_request_type, response)
            span.set_status(Status(StatusCode.OK))

    span.end()
    return response


@_with_tracer_wrapper
async def _awrap(tracer, to_wrap, wrapped, instance, args, kwargs):
    """Instruments and calls every function defined in TO_WRAP."""
    if context_api.get_value(_SUPPRESS_INSTRUMENTATION_KEY) or context_api.get_value(
        SUPPRESS_LANGUAGE_MODEL_INSTRUMENTATION_KEY
    ):
        return await wrapped(*args, **kwargs)

    name = to_wrap.get("span_name")
    llm_request_type = _llm_request_type_by_method(to_wrap.get("method"))
    span = tracer.start_span(
        name,
        kind=SpanKind.CLIENT,
        attributes={
            SpanAttributes.LLM_SYSTEM: "MistralAI",
            SpanAttributes.LLM_REQUEST_TYPE: llm_request_type.value,
        },
    )

    if span.is_recording():
        _set_input_attributes(span, llm_request_type, to_wrap, kwargs)

    if to_wrap.get("streaming"):
        response = wrapped(*args, **kwargs)
    else:
        response = await wrapped(*args, **kwargs)

    if response:
        if span.is_recording():
            if to_wrap.get("streaming"):
                return _aaccumulate_streaming_response(span, llm_request_type, response)

            _set_response_attributes(span, llm_request_type, response)
            span.set_status(Status(StatusCode.OK))

    span.end()
    return response


class MistralAiInstrumentor(BaseInstrumentor):
    """An instrumentor for Mistral AI's client library."""

    def __init__(self, exception_logger=None):
        super().__init__()
        Config.exception_logger = exception_logger

    def instrumentation_dependencies(self) -> Collection[str]:
        return _instruments

    def _instrument(self, **kwargs):
        tracer_provider = kwargs.get("tracer_provider")
        tracer = get_tracer(__name__, __version__, tracer_provider)
        for wrapped_method in WRAPPED_METHODS:
            wrap_method = wrapped_method.get("method")
            wrap_function_wrapper(
                "mistralai",
                f"chat.Chat.{wrap_method}",
                _wrap(tracer, wrapped_method),
            )

        for wrapped_method in WRAPPED_METHODS_ASYNC:
            wrap_method = wrapped_method.get("method")
            wrap_function_wrapper(
                "mistralai",
                f"chat.Chat.{wrap_method}",
                _awrap(tracer, wrapped_method),
            )
        

        for wrapped_method in WRAPPED_METHODS_EMBED:
            wrap_method = wrapped_method.get("method")
            wrap_function_wrapper(
                "mistralai",
                f"embeddings.Embeddings.{wrap_method}",
                _wrap(tracer, wrapped_method),
            )

    def _uninstrument(self, **kwargs):
        for wrapped_method in WRAPPED_METHODS:
            wrap_object = wrapped_method.get("object")
            unwrap(
                f"mistralai.chat.Chat.{wrap_object}",
                wrapped_method.get("method"),
            )

        
        for wrapped_method in WRAPPED_METHODS_ASYNC:
            wrap_object = wrapped_method.get("object")
            unwrap(
                f"mistralai.chat.Chat.{wrap_object}",
                wrapped_method.get("method"),
            )

        for wrapped_method in WRAPPED_METHODS_EMBED:
            wrap_object = wrapped_method.get("object")
            unwrap(
                f"mistralai.embeddings.Embeddings.{wrap_object}",
                wrapped_method.get("method"),
            )
