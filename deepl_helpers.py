# deepl_helpers.py
import re

LEADING_SYMBOLS_RE = re.compile(r"^([\W_]+)(.*)$", flags=re.UNICODE)
MUSTACHE_RE = re.compile(r"{{\s*([^{}]+?)\s*}}")
FORMAT_RE = re.compile(r"{\s*([a-zA-Z0-9_]+)\s*}")  # {name}


def split_leading_symbols(s: str) -> tuple[str, str]:
    m = LEADING_SYMBOLS_RE.match(s)
    if not m:
        return "", s
    return m.group(1), m.group(2)


def protect_placeholders_to_xml(text: str):
    """
    Replace placeholders with XML tags for DeepL XML tag-handling.
    - {{name}} -> <m id="0"/>
    - {name}   -> <ph id="1"/>
    Returns (xml_text, restore_map) where restore_map maps '<m id="0"/>' to '{{name}}' etc.
    """
    restore = {}
    idx = 0

    def repl_mustache(m):
        nonlocal idx
        orig = m.group(0)
        tag = f'<m id="{idx}"/>'
        restore[tag] = orig
        idx += 1
        return tag

    def repl_format(m):
        nonlocal idx
        orig = m.group(0)
        tag = f'<ph id="{idx}"/>'
        restore[tag] = orig
        idx += 1
        return tag

    text = MUSTACHE_RE.sub(repl_mustache, text)
    text = FORMAT_RE.sub(repl_format, text)
    return text, restore


def restore_placeholders_from_xml(
    text: str, restore_map: dict[str, str]
) -> str:
    # Replace longer tags first just in case
    for tag, orig in sorted(
        restore_map.items(), key=lambda kv: -len(kv[0])
    ):
        text = text.replace(tag, orig)
    return text
