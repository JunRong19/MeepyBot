async def log_tokens(response):
    total_input = 0
    total_output = 0

    for msg in response["messages"]:
        if hasattr(msg, "usage_metadata") and msg.usage_metadata:
            total_input += msg.usage_metadata.get("input_tokens", 0)
            total_output += msg.usage_metadata.get("output_tokens", 0)

    print("Input tokens:", total_input)
    print("Output tokens:", total_output)
    print("Total tokens:", total_input + total_output)
