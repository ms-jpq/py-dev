from typing import Iterator
from xml.etree.ElementTree import Element

from markdown import Markdown, markdown


def _unmark_element(element: Element) -> str:
    def cont() -> Iterator[str]:
        if element.text:
            yield element.text
        for child in element:
            yield _unmark_element(child)
        if element.tail:
            yield element.tail

    return "".join(cont())


Markdown.output_formats["plain"] = _unmark_element # type: ignore


def md_2_txt(md: str) -> str:
    _md = Markdown(output_format="plain") # type: ignore
    _md.stripTopLevelTags = False # type: ignore
    txt = _md.convert(md)
    return txt


def txt_2_md(txt: str) -> str:
    md = markdown(txt, output_format="xhtml")
    return md
