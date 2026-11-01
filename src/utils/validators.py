def sanitize_text(input_text: str) -> str:
    """Cleans raw user input string."""
    if not input_text:
        return ""
    return input_text.strip()

def validate_file_extension(filename: str, allowed_extensions: list[str]) -> bool:
    """Validates uploaded file extensions."""
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in allowed_extensions
