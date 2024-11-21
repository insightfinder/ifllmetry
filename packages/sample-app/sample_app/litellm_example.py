import litellm


def test_traceloop_logging():
    try:
        litellm.success_callback = ["iftracer"]
        from iftracer.sdk import Iftracer
        from iftracer.sdk.instruments import Instruments

        Iftracer.init(app_name="...", instruments=set([Instruments.OPENAI]))
        litellm.set_verbose = False
        response = litellm.completion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "This is a test"}],
            max_tokens=10,
            temperature=0.7,
            timeout=5,
        )
        print(f"response: {response}")
    except Exception:
        pass


test_traceloop_logging()
