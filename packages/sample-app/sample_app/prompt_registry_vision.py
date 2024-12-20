import os
from openai import OpenAI


from iftracer.sdk import Iftracer
from iftracer.sdk.decorators import task, workflow
from iftracer.sdk.prompts import get_prompt

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

Iftracer.init(app_name="prompt_registry_vision")


@task(name="describe_picture")
def describe_picture():
    prompt_args = get_prompt(key="vision", variables={"words": 2})
    completion = client.chat.completions.create(**prompt_args)

    return completion.choices[0].message.content


@workflow(name="picture_description")
def picture_description():
    print(describe_picture())


picture_description()
