from terminal import get_width


def center_text(text, char=" "):
    if isinstance(text, list):
        return "\n".join([line.center(get_width(), char) for line in text])
    if isinstance(text, str):
        return text.center(get_width(), char)
