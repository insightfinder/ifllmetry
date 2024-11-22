from anthropic import Anthropic
from iftracer.sdk import Iftracer
from iftracer.sdk.decorators import workflow


Iftracer.init()


@workflow(name="pirate_joke_streaming_generator")
def joke_workflow():
    anthropic = Anthropic()
    stream = anthropic.messages.create(
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": "Tell me a joke about OpenTelemetry",
            }
        ],
        model="claude-3-haiku-20240307",
        stream=True,
    )
    response_content = ""
    for event in stream:
        if event.type == 'content_block_delta' and event.delta.type == 'text_delta':
            response_content += event.delta.text
    print(response_content)
    return stream


joke_workflow()
