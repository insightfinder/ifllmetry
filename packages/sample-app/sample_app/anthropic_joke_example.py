from anthropic import Anthropic

from iftracer.sdk import Iftracer
from iftracer.sdk.decorators import workflow

Iftracer.init()


@workflow(name="pirate_joke_generator")
def joke_workflow():
    anthropic = Anthropic()
    response = anthropic.messages.create(
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": "Tell me a joke about OpenTelemetry",
            }
        ],
        model="claude-3-opus-20240229",
    )
    print(response.content)
    return response


joke_workflow()
