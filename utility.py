def text_to_utf8(text):
    """
    Utility function to "translate" the text taken from an html page with all the utf-8 chars
    encoded into a decoded text
    """
    return text.encode('ascii').decode('unicode-escape').encode('latin-1').decode('utf-8')