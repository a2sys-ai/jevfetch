"""Split an HTML or plain-text document into blocks, the unit that jevfetch scores and returns.

A block is a paragraph, list item, table row, or code block, labelled with its heading path. A list
lead-in ending in a colon is merged with the list items that follow it, because the lead-in often
carries the condition that the items depend on."""

import re
from dataclasses import dataclass
from typing import Literal

from bs4 import BeautifulSoup, CData, NavigableString, Tag

DROP = {"script", "style", "noscript", "nav", "footer", "aside", "form", "svg", "button", "iframe"}
HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
LEAF_BLOCKS = {"p", "li", "pre", "blockquote", "dt", "dd", "tr", "figcaption", "caption"}
CONTAINERS = {"table", "ul", "ol", "dl"}
# Wikipedia furniture, the permalink symbols (¶, #) that documentation generators append to headings, and
# elements a browser does not show (such as the hidden sort keys in Wikipedia tables).
NOISE = (
    "sup.reference, .mw-editsection, .navbox, .reflist, .references, .toc, #toc, .sidebar, "
    "a.headerlink, a.hash-link, a.anchor-link, "
    '[style*="display:none"], [style*="display: none"], [hidden], .sortkey'
)
BLOCK_LEVEL = set(
    "address article aside blockquote caption dd div dl dt figcaption figure footer form h1 h2 h3 h4 "
    "h5 h6 header hr li main nav ol p pre section table tbody td tfoot th thead tr ul".split()
)
MAX_BLOCK_CHARS = 4000  # keeps a single Jev request within the model's input limit
# A content-like element holding less of the page's text than this is one section, not the content: the HTML
# of an RFC gives its section titled "Content" the id "content".
MIN_ROOT_SHARE = 0.1

Kind = Literal["p", "li", "pre", "row", "group", "frag"]


@dataclass
class Block:
    id: int
    path: list[str]
    text: str
    kind: Kind

    @property
    def heading(self) -> str:
        return " > ".join(self.path)


def parse(doc: str) -> list[Block]:
    """Blocks of an HTML page, or of plain text and markdown when the document is not HTML."""
    return _parse_html(doc) if _is_html(doc) else _parse_plain(doc)


def merge_fragments(blocks: list[Block], short: int = 100, cap: int = 800) -> list[Block]:
    """Merge consecutive short paragraphs or list items under the same heading (e.g. steps of a flow chart).

    Such fragments rarely say on their own what they are about. Table rows and code are never merged."""
    out: list[Block] = []
    for b in blocks:
        prev = out[-1] if out else None
        if (
            prev
            and b.kind in ("p", "li")
            and len(b.text) < short
            and prev.path == b.path
            and (prev.kind == "frag" or (prev.kind in ("p", "li") and len(prev.text) < short))
            and len(prev.text) + len(b.text) < cap
        ):
            out[-1] = Block(0, prev.path, prev.text + "\n" + b.text, "frag")
        else:
            out.append(Block(0, b.path, b.text, b.kind))
    return _number(_split_long(out))


def render(blocks: list[Block], keep: set[int] | None = None) -> str:
    """Blocks in document order, with a "## heading path" line wherever the path changes.

    With `keep`, only blocks whose id is in it are rendered."""
    lines, last_path = [], None
    for b in blocks:
        if keep is not None and b.id not in keep:
            continue
        if b.path != last_path:
            if b.path:
                lines.append("## " + b.heading)
            last_path = b.path
        lines.append(b.text)
    return "\n".join(lines)


def _text(el: Tag) -> str:
    """The element's text with inline elements joined as written, so that <span>f</span><span>(x)</span> reads
    "f(x)" (BeautifulSoup's get_text(" ") gives "f (x)"). Block boundaries, <br>, and super- and subscripts
    separate words."""
    out: list[str] = []

    def walk(node: Tag) -> None:
        for c in node.children:
            if type(c) in (NavigableString, CData):
                out.append(str(c))
            elif isinstance(c, Tag):
                if c.name == "br":
                    out.append("\n")
                elif c.name in BLOCK_LEVEL or c.name in ("sup", "sub"):  # 6<sup>4</sup> must not read as 64
                    out.append(" ")
                    walk(c)
                    out.append(" ")
                else:
                    walk(c)

    walk(el)
    return "".join(out)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _is_html(doc: str) -> bool:
    head = doc[:3000].lower()
    return any(t in head for t in ("<html", "<body", "<div", "<p>", "<!doctype"))


def _root(soup: BeautifulSoup) -> Tag:
    body = soup.body or soup
    total = len(body.get_text(" ", strip=True))
    for sel in ("main", "article", "[role=main]", "#content", "#main-content", ".body"):
        el = soup.select_one(sel)
        n = len(el.get_text(" ", strip=True)) if el else 0
        if n > 500 and n >= MIN_ROOT_SHARE * total:
            return el
    return body


def _parse_plain(doc: str) -> list[Block]:
    path: list[tuple[int, str]] = []
    out: list[Block] = []
    for para in re.split(r"\n\s*\n", doc):
        para = para.strip()
        if not para:
            continue
        m = re.match(r"^(#{1,6})\s+(.*)", para)
        if m and "\n" not in para:
            level = len(m.group(1))
            while path and path[-1][0] >= level:
                path.pop()
            path.append((level, m.group(2).strip()))
            continue
        out.append(Block(0, [h for _, h in path], para, "p"))
    return _number(_split_long(out))


def _clean(soup: BeautifulSoup) -> None:
    # Keep the page title but drop the rest of the header: Wikipedia puts the h1 and its language menu
    # in the same <header>.
    for t in soup.find_all("header"):
        h1 = t.find("h1")
        if h1:
            t.replace_with(h1.extract())
        else:
            t.decompose()
    for t in soup.find_all(DROP):
        t.decompose()
    for t in soup.select(NOISE):
        t.decompose()


def _own_text(li: Tag) -> str:
    """Text of a list item without its nested lists, including text inside inline tags."""
    parts = []
    for c in li.children:
        if isinstance(c, NavigableString):
            parts.append(str(c))
        elif isinstance(c, Tag) and c.name not in CONTAINERS:
            parts.append(_text(c))
    return " ".join(parts)


def _definition_items(dl: Tag) -> list[Tag]:
    items = []
    for c in dl.children:
        if isinstance(c, Tag) and c.name in ("dt", "dd"):
            items.append(c)
        elif isinstance(c, Tag) and c.name == "div":  # HTML5 allows <div> around each dt/dd group
            items += [x for x in c.children if isinstance(x, Tag) and x.name in ("dt", "dd")]
    return items


def _parse_html(html: str) -> list[Block]:
    soup = BeautifulSoup(html, "lxml")
    _clean(soup)
    path: list[tuple[int, str]] = []
    out: list[Block] = []

    def emit(text: str, kind: Kind) -> None:
        text = text.strip("\n") if kind == "pre" else _norm(text)
        if len(text.strip()) >= 3:
            out.append(Block(0, [h for _, h in path], text, kind))

    def walk(node: Tag) -> None:
        for ch in node.children:
            if not isinstance(ch, Tag):
                continue
            if ch.name == "dl":
                # A definition term (a function signature, an option name) becomes the heading of its
                # descriptions; without it "the child process will be killed" loses which function it is about.
                depth = len(path)
                for item in _definition_items(ch):
                    if item.name == "dt":
                        del path[depth:]
                        path.append((99, _norm(_text(item))[:160]))
                    elif item.find(list(LEAF_BLOCKS | CONTAINERS | {"div"})):
                        walk(item)
                    else:
                        emit(_text(item), "p")
                del path[depth:]
            elif ch.name in HEADINGS:
                level = int(ch.name[1])
                while path and path[-1][0] >= level:
                    path.pop()
                path.append((level, _norm(_text(ch))))
            elif ch.name == "tr":
                cells = [_norm(_text(c)) for c in ch.find_all(["td", "th"], recursive=False)]
                emit(" | ".join(cells), "row")
            elif ch.name == "pre":
                emit(ch.get_text(), "pre")
            elif ch.name == "li":
                if ch.find(list(CONTAINERS)):
                    emit(_own_text(ch), "li")  # becomes the lead-in of the nested list
                    walk(ch)
                else:
                    emit(_text(ch), "li")
            elif ch.name in LEAF_BLOCKS and not ch.find(list((LEAF_BLOCKS - {"tr"}) | CONTAINERS)):
                emit(_text(ch), "p")
            else:
                walk(ch)

    walk(_root(soup))
    return _number(_split_long(_merge_leadins(out)))


def _merge_leadins(blocks: list[Block]) -> list[Block]:
    """Join a lead-in ending in a colon with the list items after it under the same heading (up to 1,500 chars)."""
    merged: list[Block] = []
    i = 0
    while i < len(blocks):
        b = blocks[i]
        j = i + 1
        if b.text.rstrip().endswith(":") and b.kind != "pre":
            parts = [b.text]
            while (
                j < len(blocks)
                and blocks[j].kind == "li"
                and blocks[j].path == b.path
                and len("\n".join(parts)) < 1500
                and not blocks[j].text.rstrip().endswith(":")
            ):
                parts.append("- " + blocks[j].text)
                j += 1
        if j > i + 1:
            merged.append(Block(0, b.path, "\n".join(parts), "group"))
        else:
            merged.append(b)
            j = i + 1
        i = j
    return merged


def _split_long(blocks: list[Block]) -> list[Block]:
    """Split blocks longer than MAX_BLOCK_CHARS at sentence (or, for code, line) boundaries."""
    out: list[Block] = []
    for b in blocks:
        if len(b.text) <= MAX_BLOCK_CHARS:
            out.append(b)
            continue
        sep = "\n" if b.kind == "pre" else " "
        parts = b.text.split("\n") if b.kind == "pre" else re.split(r"(?<=[.!?。])\s+|\n", b.text)
        cur = ""
        for s in parts:
            if cur and len(cur) + len(s) > MAX_BLOCK_CHARS:
                out.append(Block(0, b.path, cur.rstrip(), b.kind))
                cur = ""
            while len(s) > MAX_BLOCK_CHARS:  # a single sentence or line over the limit is cut by length
                out.append(Block(0, b.path, s[:MAX_BLOCK_CHARS], b.kind))
                s = s[MAX_BLOCK_CHARS:]
            cur += s + sep
        if cur.strip():
            out.append(Block(0, b.path, cur.rstrip(), b.kind))
    return out


def _number(blocks: list[Block]) -> list[Block]:
    for k, b in enumerate(blocks):
        b.id = k
    return blocks
