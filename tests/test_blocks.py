import json

from jevfetch.blocks import merge_fragments, parse, render

PAD = "<p>" + "filler text " * 60 + "</p>"  # long enough for <main> to be chosen as the content root


def page(body: str) -> str:
    return f"<html><body><header><nav>site menu</nav></header><main>{PAD}{body}</main></body></html>"


def texts(html: str) -> list[str]:
    return [b.text for b in parse(html)]


def test_a_small_section_with_a_content_id_is_not_taken_as_the_page():
    sections = "".join(f"<section><h2>{i}. Part {i}</h2>{PAD}</section>" for i in range(1, 21))
    html = f'<html><body>{sections}<section id="content"><h2>6.4. Content</h2>{PAD}</section></body></html>'
    paths = {b.path[0] for b in parse(html)}
    assert "1. Part 1" in paths and "6.4. Content" in paths


def test_leadin_merges_only_following_list_items():
    blocks = parse(
        page(
            "<p>The API has these limits:</p><ul><li>10 per second</li><li>100 per minute</li></ul>"
            "<p>An unrelated paragraph.</p>"
        )
    )
    group = [b for b in blocks if b.kind == "group"]
    assert [b.text for b in group] == ["The API has these limits:\n- 10 per second\n- 100 per minute"]
    assert "An unrelated paragraph." in [b.text for b in blocks]


def test_leadin_does_not_absorb_paragraphs_or_table_rows():
    t = texts(
        page(
            "<p>The API has these limits:</p><p>A long unrelated paragraph.</p>"
            "<table><tr><td>a</td><td>b</td></tr></table>"
        )
    )
    assert "The API has these limits:" in t
    assert "A long unrelated paragraph." in t
    assert "a | b" in t


def test_nested_li_keeps_leadin_inside_inline_tag():
    t = texts(page("<ul><li><strong>Only when enabled</strong>:<ul><li>alpha item one</li></ul></li></ul>"))
    assert any("Only when enabled" in x for x in t)
    assert any("alpha item one" in x for x in t)


def test_header_with_h1_keeps_title_as_heading_path():
    html = (
        "<html><body><main><header><h1>Hôtel Matignon</h1></header>"
        f"{PAD}<p>It is the residence of the Prime Minister.</p></main></body></html>"
    )
    blocks = parse(html)
    assert blocks[0].path == ["Hôtel Matignon"]


def test_header_keeps_only_h1_not_language_list():
    html = (
        "<html><body><main><header><h1>Harriet Lane</h1><ul><li>Deutsch</li><li>Français</li></ul></header>"
        f"{PAD}<p>She was the niece of James Buchanan.</p></main></body></html>"
    )
    blocks = parse(html)
    assert blocks[0].path == ["Harriet Lane"]
    assert not any(b.text in ("Deutsch", "Français") for b in blocks)


def test_site_header_without_h1_is_dropped():
    assert not any("site menu" in x for x in texts(page("<p>body text here.</p>")))


def test_definition_list_wrapped_in_div():
    blocks = parse(page("<dl><div><dt>timeout</dt><dd>Seconds to wait before giving up.</dd></div></dl>"))
    dd = [b for b in blocks if b.text == "Seconds to wait before giving up."]
    assert dd and dd[0].path[-1] == "timeout"


def test_code_block_keeps_whitespace():
    code = "def f():\n    return 1\n\nprint(f())"
    blocks = parse(page(f"<pre>{code}</pre>"))
    assert any(b.kind == "pre" and b.text == code for b in blocks)


def test_plain_text_uses_markdown_headings():
    blocks = parse("# Title\n\nFirst paragraph.\n\n## Section\n\nSecond paragraph.")
    assert [(b.path, b.text) for b in blocks] == [
        (["Title"], "First paragraph."),
        (["Title", "Section"], "Second paragraph."),
    ]


def test_merge_fragments_joins_short_steps_but_not_rows():
    blocks = merge_fragments(parse("1. request (by March 31)\n\n2. review\n\nA longer paragraph " + "x " * 80))
    assert blocks[0].text == "1. request (by March 31)\n2. review"


def test_render_prints_heading_only_when_path_changes():
    blocks = parse("# A\n\none\n\ntwo\n\n# B\n\nthree")
    assert render(blocks) == "## A\none\ntwo\n## B\nthree"
    assert render(blocks, {0, 2}) == "## A\none\n## B\nthree"


def test_inline_elements_are_joined_as_written():
    t = texts(page("<p>If <em>maxsize</em> is set to <code>None</code>, the cache can grow.</p>"))
    assert "If maxsize is set to None, the cache can grow." in t


def test_sphinx_signature_and_permalink_symbol():
    html = page(
        '<dl><dt><em class="property">@</em><span class="sig-prename">functools.</span>'
        '<span class="sig-name">lru_cache</span><span class="sig-paren">(</span><em>maxsize</em>'
        '<span class="sig-paren">)</span><a class="headerlink" href="#x">¶</a></dt>'
        "<dd><p>Decorator to wrap a function.</p></dd></dl>"
    )
    dd = [b for b in parse(html) if b.text == "Decorator to wrap a function."]
    assert dd and dd[0].path[-1] == "@functools.lru_cache(maxsize)"


def test_superscripts_stay_separate_and_hidden_text_is_dropped():
    t = texts(
        page(
            "<p>He won the set 7–6<sup>4</sup> in a tiebreak.</p>"
            '<table><tr><td><span style="display:none">Jacobs, Daniel</span>Daniel Jacobs</td><td>DE</td></tr></table>'
        )
    )
    assert "He won the set 7–6 4 in a tiebreak." in t
    assert "Daniel Jacobs | DE" in t


def test_block_boundaries_still_separate_words():
    t = texts(page("<ul><li><div>first</div><div>second</div></li></ul><p>one<br>two</p>"))
    assert "first second" in t and "one two" in t


def test_small_json_is_one_block():
    blocks = parse('{"name": "httpx", "version": "0.28.1"}')
    assert [(b.path, b.text) for b in blocks] == [([], '{"name": "httpx", "version": "0.28.1"}')]


def test_large_json_splits_into_records_with_key_paths():
    url = "https://files.example/" + "x" * 300
    files = [{"filename": f"httpx-0.1.{i}.whl", "sha256": "f" * 64, "url": url} for i in range(3)]
    doc = json.dumps({"info": {"name": "httpx", "version": "0.28.1"}, "releases": {"0.1": files, "0.2": files}})
    assert len(doc) > 1500
    blocks = parse(doc)
    assert any(b.path == [] and b.text == '{"info": {"name": "httpx", "version": "0.28.1"}}' for b in blocks)
    versions = [b for b in blocks if "httpx-0.1.0.whl" in b.text]
    assert [(b.path, b.text[:8]) for b in versions] == [(["releases"], '{"0.1": '), (["releases"], '{"0.2": ')]
    assert all(len(b.text) <= 1500 for b in blocks)


def test_long_json_string_value_is_its_own_block():
    doc = json.dumps({"info": {"description": "# httpx\n\nA client. " * 150, "version": "1.0"}})
    blocks = parse(doc)
    description = [b for b in blocks if b.path == ["info", "description"]]
    assert description and description[0].text.startswith("# httpx")
    assert any('"version": "1.0"' in b.text and b.path == ["info"] for b in blocks)


def test_invalid_json_is_plain_text():
    blocks = parse('{"name": not json')
    assert [b.text for b in blocks] == ['{"name": not json']


def test_small_xml_is_one_block():
    blocks = parse('<?xml version="1.0"?><note><to>Ann</to><body>Call me.</body></note>')
    assert [(b.path, b.text) for b in blocks] == [([], "<note><to>Ann</to><body>Call me.</body></note>")]


def test_large_xml_splits_into_elements_with_tag_paths():
    items = "".join(
        f"<item><title>Story {i}</title><description>{'words ' * 150}</description></item>" for i in range(3)
    )
    blocks = parse(f'<?xml version="1.0"?>\n<rss><channel><title>News</title>{items}</channel></rss>')
    stories = [b for b in blocks if "<title>Story" in b.text]
    assert len(stories) == 3 and all(b.path == ["rss", "channel"] and b.text.startswith("<item>") for b in stories)
    assert any(b.path == ["rss", "channel"] and "<title>News</title>" in b.text for b in blocks)


def test_markdown_starting_with_an_html_tag_is_plain_text():
    blocks = parse('<h1 align="center">Project</h1>\n\nSome intro text here.\n\n## Install\n\nRun pip install.')
    assert [b.path for b in blocks] == [[], [], ["Install"]]


def test_markdown_with_a_centered_logo_keeps_its_headings():
    blocks = parse('<p align="center"><img src="logo.png"></p>\n\n# Title\n\nBody text paragraph.\n')
    assert any(b.path == ["Title"] and b.text == "Body text paragraph." for b in blocks)


def test_xml_without_a_declaration_is_parsed_as_xml():
    blocks = parse('<rss version="2.0"><channel><title>News</title></channel></rss>')
    assert len(blocks) == 1 and blocks[0].text.startswith("<rss")


def test_deeply_nested_json_does_not_crash():
    parse("[" * 100000 + "]" * 100000)


def test_oversized_xml_element_keeps_its_attributes():
    entries = "".join(f"<entry><title>Story {i}</title><summary>{'words ' * 150}</summary></entry>" for i in range(3))
    blocks = parse(f'<?xml version="1.0"?><feed xml:lang="en">{entries}</feed>')
    assert any(b.path == ["feed"] and b.text == '<feed xml:lang="en">' for b in blocks)


def test_json_groups_count_key_length_and_separators():
    doc = json.dumps({"k" * 2000: 1, **{f"key{i}": "v" * 100 for i in range(30)}})
    assert all(len(b.text) <= 1500 for b in parse(doc))
