"""Reduce a document to the blocks relevant to a query.

1. A document of at most `passthrough_tokens` is returned whole.
2. Blocks whose stage-1 score reaches `candidate_threshold` are rescored in stage 2, and those reaching
   `keep_threshold` are kept. A block right before or after a kept one under the same heading is kept from
   `neighbor_threshold`, since a narrowly worded query tends to underrate the condition next to the answer.
3. The first block (title and front matter) is always kept.
4. If the kept body is shorter than `min_output_tokens`, blocks are added by stage-2 score, then by
   stage-1 score, until it is long enough."""

import asyncio
from dataclasses import asdict, dataclass
from typing import Literal

import httpx

from jevfetch import scoring, tokens
from jevfetch.blocks import PLAIN_TYPES, Block, merge_fragments, parse, render
from jevfetch.jev import Jev
from jevfetch.web import UnsupportedContent, fetch_page, fetch_rendered, save_file

Status = Literal["filtered", "passthrough", "no_match", "empty", "fetch_error"]


@dataclass(frozen=True)
class Config:
    candidate_threshold: float = 0.3
    keep_threshold: float = 0.8
    neighbor_threshold: float = 0.6
    passthrough_tokens: int = 2000
    min_output_tokens: int = 300
    window_tokens: int = 3000
    concurrency: int = 16
    model: str = "jev-latest"
    render_fallback: bool = True
    render_below_tokens: int = 200


@dataclass
class Result:
    status: Status
    text: str
    url: str = ""
    doc_tokens: int = 0
    out_tokens: int = 0
    blocks_total: int = 0
    blocks_kept: int = 0
    rendered: bool = False
    jev_input_tokens: int = 0
    jev_cached_input_tokens: int = 0
    jev_requests: int = 0
    model: str = ""
    error: str = ""
    saved: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def choose_blocks(blocks: list[Block], stage1: dict[int, float], stage2: dict[int, float], cfg: Config) -> set[int]:
    keep = {i for i, v in stage2.items() if v >= cfg.keep_threshold}
    keep |= {
        j
        for i in keep
        for j in (i - 1, i + 1)
        if 0 <= j < len(blocks) and blocks[j].path == blocks[i].path and stage2.get(j, 0) >= cfg.neighbor_threshold
    }
    if blocks:
        keep.add(0)
    ranked = sorted(stage2, key=stage2.get, reverse=True) + sorted(
        (i for i in stage1 if i not in stage2), key=stage1.get, reverse=True
    )
    body = sum(tokens.count(blocks[i].text) for i in keep if i != 0)
    for i in ranked:
        if body >= cfg.min_output_tokens:
            break
        if i not in keep:
            keep.add(i)
            body += tokens.count(blocks[i].text)
    return keep


async def select_relevant_async(
    doc: str | list[Block], query: str, cfg: Config | None = None, jev: Jev | None = None
) -> Result:
    """The blocks of `doc` (text, HTML, or already parsed blocks) that are relevant to `query`."""
    cfg = cfg or Config()
    blocks = parse(doc) if isinstance(doc, str) else doc
    full = render(blocks)
    doc_tokens = tokens.count(full)
    if not blocks:
        return Result("empty", "", doc_tokens=doc_tokens)
    if doc_tokens <= cfg.passthrough_tokens:
        return Result(
            "passthrough",
            full,
            doc_tokens=doc_tokens,
            out_tokens=doc_tokens,
            blocks_total=len(blocks),
            blocks_kept=len(blocks),
        )
    blocks = merge_fragments(blocks)
    own = jev is None
    jev = jev or Jev(concurrency=cfg.concurrency, model=cfg.model)
    try:
        before = (jev.input_tokens, jev.cached_input_tokens, jev.requests)
        stage1 = await scoring.fanout(jev, blocks, query, cfg.window_tokens)
        candidates = [i for i, v in stage1.items() if v >= cfg.candidate_threshold]
        stage2 = await scoring.rescore(jev, blocks, candidates, query) if candidates else {}
        usage = (jev.input_tokens - before[0], jev.cached_input_tokens - before[1], jev.requests - before[2])
        model = ",".join(sorted(jev.models))
    finally:
        if own:
            await jev.aclose()
    keep = choose_blocks(blocks, stage1, stage2, cfg)
    text = render(blocks, keep)
    status = "filtered" if any(v >= cfg.keep_threshold for v in stage2.values()) else "no_match"
    return Result(
        status,
        text,
        doc_tokens=doc_tokens,
        out_tokens=tokens.count(text),
        blocks_total=len(blocks),
        blocks_kept=len(keep),
        jev_input_tokens=usage[0],
        jev_cached_input_tokens=usage[1],
        jev_requests=usage[2],
        model=model,
    )


async def fetch_relevant_async(url: str, query: str, cfg: Config | None = None, jev: Jev | None = None) -> Result:
    """Fetch `url` and keep the blocks relevant to `query`, re-rendering the page if its static HTML is nearly empty."""
    cfg = cfg or Config()
    try:
        html, final_url, media_type = await asyncio.to_thread(fetch_page, url)
    except UnsupportedContent as e:
        error = f"{type(e).__name__}: {e}"
        try:
            saved = await asyncio.to_thread(save_file, url, e.kind, e.content)
        except OSError as save_error:
            return Result("fetch_error", "", url=url, error=f"{error}; could not save it: {save_error}")
        return Result("fetch_error", "", url=url, error=error, saved=saved)
    except httpx.HTTPError as e:
        return Result("fetch_error", "", url=url, error=f"{type(e).__name__}: {e}")
    blocks, rendered = parse(html, final_url, media_type), False
    # A browser shows a plain-text type as source, so rendering adds nothing and turns the text into HTML.
    if cfg.render_fallback and media_type not in PLAIN_TYPES and tokens.count(render(blocks)) < cfg.render_below_tokens:
        dom = await asyncio.to_thread(fetch_rendered, url)
        if dom:
            again = parse(dom, final_url)
            if tokens.count(render(again)) > tokens.count(render(blocks)):
                blocks, rendered = again, True
    res = await select_relevant_async(blocks, query, cfg, jev)
    res.url, res.rendered = url, rendered
    return res


def select_relevant(doc: str | list[Block], query: str, cfg: Config | None = None) -> Result:
    return asyncio.run(select_relevant_async(doc, query, cfg))


def fetch_relevant(url: str, query: str, cfg: Config | None = None) -> Result:
    return asyncio.run(fetch_relevant_async(url, query, cfg))
