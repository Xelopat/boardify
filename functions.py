import re


def delete_emoji(text):
    symbol_pattern = re.compile('[^a-zA-Z0-9-.]')
    text_without_symbols = symbol_pattern.sub('', text)
    return text_without_symbols
