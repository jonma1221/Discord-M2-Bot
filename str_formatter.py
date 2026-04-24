
def sanitize_text(text: str) -> str:
    # Remove NULL bytes and other control characters (except newline/tab)
    return ''.join(
        ch for ch in text
        if ch == '\n' or ch == '\t' or ord(ch) >= 32
    )

def split_message(text: str, limit: int = 1900):
    chunks = []
    while text:
        chunk = text[:limit]

        # Try to split on a newline for cleaner formatting
        if len(text) > limit:
            last_newline = chunk.rfind('\n')
            if last_newline != -1:
                chunk = chunk[:last_newline]

        chunks.append(chunk)
        text = text[len(chunk):]

    return chunks