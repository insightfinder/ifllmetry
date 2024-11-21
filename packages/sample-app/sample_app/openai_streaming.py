import os
from openai import OpenAI


from iftracer.sdk import Iftracer
from iftracer.sdk.decorators import workflow

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

Iftracer.init(app_name="story_service")


@workflow(name="streaming_story")
def joke_workflow():
    stream = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Tell me a story about opentelemetry"}],
        stream=True,
    )

    for part in stream:
        print(part.choices[0].delta.content or "", end="")
    print()


joke_workflow()
