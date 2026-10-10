import json
from pathlib import Path

import httpx

from jevfetch import cli, pipeline, scoring, web
from jevfetch.blocks import Block
from jevfetch.jev import JevError
from jevfetch.pipeline import Config, choose_blocks, fetch_relevant_async, select_relevant_async


def blocks_of(n: int, words: int = 200) -> list[Block]:
    return [Block(i, ["Doc"], f"block {i} " + "word " * words, "p") for i in range(n)]


class FakeJev:
    def __init__(self):
        self.input_tokens = self.cached_input_tokens = self.requests = 0
        self.models = {"jev-test"}


def fake_scores(monkeypatch, stage1: dict[int, float], stage2: dict[int, float]):
    async def fanout(jev, blocks, query, window_tokens):
        jev.requests += 1
        return stage1

    async def rescore(jev, blocks, ids, query):
        jev.requests += len(ids)
        return {i: stage2[i] for i in ids}

    monkeypatch.setattr(scoring, "fanout", fanout)
    monkeypatch.setattr(scoring, "rescore", rescore)


def test_choose_keeps_title_and_passing_blocks_when_body_is_long_enough():
    keep = choose_blocks(blocks_of(5), {1: 0.9, 2: 0.5, 3: 0.1}, {1: 0.95, 2: 0.2}, Config(min_output_tokens=100))
    assert keep == {0, 1}


def test_choose_fills_to_min_tokens_by_stage2_then_stage1_score():
    keep = choose_blocks(
        blocks_of(6, words=50), {1: 0.9, 2: 0.5, 3: 0.2, 4: 0.25}, {1: 0.95, 2: 0.4}, Config(min_output_tokens=150)
    )
    assert keep == {0, 1, 2, 4}


async def test_short_document_passes_through_without_jev(monkeypatch):
    fake_scores(monkeypatch, {}, {})
    res = await select_relevant_async(blocks_of(3, words=10), "q", Config(), FakeJev())
    assert res.status == "passthrough" and res.jev_requests == 0 and res.blocks_kept == 3


async def test_text_input_is_parsed(monkeypatch):
    fake_scores(monkeypatch, {}, {})
    res = await select_relevant_async("# Title\n\nshort text", "q", Config(), FakeJev())
    assert res.status == "passthrough" and res.text == "## Title\nshort text"


async def test_long_document_is_filtered_and_usage_counted(monkeypatch):
    fake_scores(monkeypatch, {i: (0.9 if i == 7 else 0.0) for i in range(20)}, {7: 0.99})
    res = await select_relevant_async(blocks_of(20), "q", Config(min_output_tokens=0), FakeJev())
    assert res.status == "filtered"
    assert res.blocks_kept == 2 and "block 7 " in res.text and "block 0 " in res.text
    assert res.jev_requests == 2 and res.model == "jev-test"


async def test_no_block_passing_keep_threshold_reports_no_match(monkeypatch):
    fake_scores(monkeypatch, {i: 0.4 for i in range(20)}, {i: 0.5 for i in range(20)})
    res = await select_relevant_async(blocks_of(20), "q", Config(), FakeJev())
    assert res.status == "no_match" and res.out_tokens >= Config().min_output_tokens


async def test_empty_document():
    res = await select_relevant_async([], "q", Config(), FakeJev())
    assert res.status == "empty" and res.text == ""


async def test_fetch_error_is_reported_not_raised(monkeypatch):
    def fail(url):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(pipeline, "fetch_page", fail)
    res = await fetch_relevant_async("https://example.com", "q", Config(), FakeJev())
    assert res.status == "fetch_error" and "ConnectError" in res.error and res.saved == ""


PDF_BODY = b"%PDF-1.4\n" + b"stream x\x9c\xed\x01 endstream\n" * 2000


def serve(monkeypatch, body: bytes, content_type: str):
    def fake_get(url, **kwargs):
        headers = {"Content-Type": content_type}
        return httpx.Response(200, content=body, headers=headers, request=httpx.Request("GET", url))

    monkeypatch.setattr(web.httpx, "get", fake_get)


async def test_pdf_is_a_fetch_error_naming_its_type_without_jev(monkeypatch, tmp_path):
    fake_scores(monkeypatch, {}, {})
    serve(monkeypatch, PDF_BODY, "application/pdf")
    monkeypatch.setattr(pipeline, "fetch_rendered", lambda url: None)
    monkeypatch.setenv("JEVFETCH_FILES_DIR", str(tmp_path))
    jev = FakeJev()
    res = await fetch_relevant_async("https://example.com/a.pdf", "q", Config(), jev)
    assert res.status == "fetch_error" and "application/pdf" in res.error
    assert jev.requests == 0 and res.text == ""


async def test_a_refused_file_is_saved_for_another_reader(monkeypatch, tmp_path):
    serve(monkeypatch, PDF_BODY, "application/pdf")
    monkeypatch.setenv("JEVFETCH_FILES_DIR", str(tmp_path))
    res = await fetch_relevant_async("https://example.com/a.pdf", "q", Config(), FakeJev())
    saved = Path(res.saved)
    assert saved.parent == tmp_path and saved.suffix == ".pdf" and saved.read_bytes() == PDF_BODY
    assert [p.name for p in tmp_path.iterdir()] == [saved.name]


async def test_a_pdf_served_as_octet_stream_is_saved_as_pdf(monkeypatch, tmp_path):
    serve(monkeypatch, PDF_BODY, "application/octet-stream")
    monkeypatch.setenv("JEVFETCH_FILES_DIR", str(tmp_path))
    res = await fetch_relevant_async("https://example.com/download?id=7", "q", Config(), FakeJev())
    assert Path(res.saved).suffix == ".pdf"


async def test_unknown_binary_is_saved_as_bin(monkeypatch, tmp_path):
    serve(monkeypatch, bytes(range(256)) * 8, "application/octet-stream")
    monkeypatch.setenv("JEVFETCH_FILES_DIR", str(tmp_path))
    res = await fetch_relevant_async("https://example.com/blob", "q", Config(), FakeJev())
    assert Path(res.saved).suffix == ".bin"


async def test_a_file_that_cannot_be_saved_is_still_a_fetch_error(monkeypatch, tmp_path):
    serve(monkeypatch, PDF_BODY, "application/pdf")
    blocker = tmp_path / "not-a-dir"
    blocker.write_text("")
    monkeypatch.setenv("JEVFETCH_FILES_DIR", str(blocker))
    res = await fetch_relevant_async("https://example.com/a.pdf", "q", Config(), FakeJev())
    assert res.status == "fetch_error" and "application/pdf" in res.error and res.saved == ""


async def test_nearly_empty_page_is_rendered_with_a_browser(monkeypatch):
    fake_scores(monkeypatch, {}, {})
    monkeypatch.setattr(
        pipeline, "fetch_page", lambda url: ("<html><body><div id='app'></div></body></html>", url, "text/html")
    )
    monkeypatch.setattr(
        pipeline, "fetch_rendered", lambda url: "<html><body><p>" + "rendered text " * 40 + "</p></body></html>"
    )
    res = await fetch_relevant_async("https://example.com", "q", Config(), FakeJev())
    assert res.rendered and "rendered text" in res.text


async def test_markdown_served_as_plain_text_keeps_its_headings_and_is_not_rendered(monkeypatch):
    doc = "# Client\n\n```pycon\n>>> r.text\n'<!doctype html>\\n<html>'\n```\n\n## Install\n\nRun pip install.\n"
    monkeypatch.setattr(pipeline, "fetch_page", lambda url: (doc, url, "text/plain"))
    rendered = []
    monkeypatch.setattr(pipeline, "fetch_rendered", rendered.append)
    res = await fetch_relevant_async("https://example.com/README.md", "q", Config(), FakeJev())
    assert "## Client > Install" in res.text and not rendered


def run_cli(monkeypatch, capsys, res=None, error=None, args=("https://example.com", "what?")):
    def fake(url, q, cfg):
        if error:
            raise error
        return res

    monkeypatch.setattr(cli, "fetch_relevant", fake)
    code = cli.main(list(args))
    return code, capsys.readouterr()


def test_cli_prints_status_and_text(monkeypatch, capsys):
    res = pipeline.Result(
        "filtered",
        "## Doc\nanswer",
        url="https://example.com",
        doc_tokens=5000,
        out_tokens=10,
        blocks_total=40,
        blocks_kept=2,
    )
    code, out = run_cli(monkeypatch, capsys, res)
    assert code == 0
    assert "# status: filtered" in out.out and "2/40 blocks, 10 of 5000 tokens" in out.out
    assert out.out.endswith("answer\n")


def test_cli_json_output(monkeypatch, capsys):
    res = pipeline.Result("passthrough", "text", url="https://example.com")
    code, out = run_cli(monkeypatch, capsys, res, args=("https://example.com", "q", "--json"))
    assert code == 0 and json.loads(out.out)["status"] == "passthrough"


def test_cli_reports_a_pdf_as_fetch_error_naming_its_type(monkeypatch, capsys, tmp_path):
    serve(monkeypatch, PDF_BODY, "application/pdf")
    monkeypatch.setenv("JEVFETCH_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("JEVFETCH_FILES_DIR", str(tmp_path / "files"))
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)  # a Jev call would exit 2 instead of reaching the network
    code = cli.main(["https://example.com/a.pdf", "what?", "--no-render"])
    out = capsys.readouterr().out
    assert code == 1
    assert "# status: fetch_error" in out and "# error: UnsupportedContent: application/pdf" in out
    saved = [line.removeprefix("# saved: ") for line in out.splitlines() if line.startswith("# saved: ")]
    assert len(saved) == 1 and Path(saved[0]).read_bytes() == PDF_BODY


def test_cli_exit_codes(monkeypatch, capsys):
    code, out = run_cli(monkeypatch, capsys, error=JevError("402: billing"))
    assert code == 2 and "402" in out.err
    code, _ = run_cli(monkeypatch, capsys, pipeline.Result("fetch_error", "", error="ConnectError: down"))
    assert code == 1


class CapturingJev(FakeJev):
    def __init__(self):
        super().__init__()
        self.states = []

    async def ask(self, state, questions):
        self.states.append(state)
        return {k: {"noul": 0.0} for k in questions}


async def test_stage1_sends_passages_without_link_targets():
    jev = CapturingJev()
    await scoring.fanout(jev, [Block(0, ["Doc"], "See the [guide](https://example.com/g) now.", "p")], "q")
    assert jev.states[0]["passages"][0]["text"] == "See the guide now."


async def test_stage2_sends_passage_and_context_without_link_targets():
    jev = CapturingJev()
    blocks = [Block(0, ["Doc"], "Before [a](x).", "p"), Block(1, ["Doc"], "The [guide](y) says so.", "p")]
    await scoring.rescore(jev, blocks, [1], "q")
    assert jev.states[0]["passage"] == "The guide says so." and jev.states[0]["context_before"] == "Before a."


async def test_fetched_pages_resolve_relative_links_against_their_url(monkeypatch):
    fake_scores(monkeypatch, {}, {})
    html = '<html><body><p>Read the <a href="/docs/">docs</a>.</p></body></html>'
    monkeypatch.setattr(pipeline, "fetch_page", lambda url: (html, url, "text/html"))
    monkeypatch.setattr(pipeline, "fetch_rendered", lambda url: None)
    res = await fetch_relevant_async("https://example.com/start", "q", Config(), FakeJev())
    assert "[docs](https://example.com/docs/)" in res.text


async def test_stage1_sends_code_blocks_as_written():
    jev = CapturingJev()
    await scoring.fanout(jev, [Block(0, ["Doc"], "handlers[key](event)", "pre")], "q")
    assert jev.states[0]["passages"][0]["text"] == "handlers[key](event)"


async def test_links_resolve_against_the_final_url_after_redirects(monkeypatch):
    fake_scores(monkeypatch, {}, {})
    html = '<html><body><p>Read the <a href="docs/">docs</a>.</p></body></html>'
    monkeypatch.setattr(pipeline, "fetch_page", lambda url: (html, "https://example.com/v2/start", "text/html"))
    monkeypatch.setattr(pipeline, "fetch_rendered", lambda url: None)
    res = await fetch_relevant_async("https://example.com/start", "q", Config(), FakeJev())
    assert "[docs](https://example.com/v2/docs/)" in res.text


def test_windows_measure_blocks_without_link_targets():
    href = "https://example.com/" + "x" * 3000
    linked = [Block(i, ["Doc"], f"[item {i}]({href})", "p") for i in range(6)]
    visible = [Block(i, ["Doc"], f"item {i}", "p") for i in range(6)]

    def ids(ws):
        return [[b.id for b in w] for w in ws]

    assert ids(scoring.windows(linked, 200)) == ids(scoring.windows(visible, 200))
