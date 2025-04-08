def chunk_generated_code(data, token_limit: int = 5500) -> list:
    """
    Splits a dictionary or string into chunks based on token limits.
    - For `dict`, splits by key-value.
    - For `str`, splits by lines.
    """
    estimated_tokens = lambda text: len(str(text)) // 4
    batches = []

    if isinstance(data, dict):
        current_batch = {}
        current_tokens = 0

        for key, value in data.items():
            tokens = estimated_tokens(value)
            if current_tokens + tokens > token_limit:
                if current_batch:
                    batches.append(current_batch)
                    current_batch = {}
                    current_tokens = 0
            current_batch[key] = value
            current_tokens += tokens

        if current_batch:
            batches.append(current_batch)

    elif isinstance(data, str):
        lines = data.splitlines()
        current_batch = []
        current_tokens = 0

        for line in lines:
            tokens = estimated_tokens(line)
            if current_tokens + tokens > token_limit:
                batches.append("\n".join(current_batch))
                current_batch = []
                current_tokens = 0
            current_batch.append(line)
            current_tokens += tokens

        if current_batch:
            batches.append("\n".join(current_batch))

    return batches