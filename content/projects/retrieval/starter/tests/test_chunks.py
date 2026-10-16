from dataclasses import FrozenInstanceError, replace
import hashlib
import pytest
from academy_retrieval import Document, Key, make_chunks


def test_unicode_character_offsets_overlap_digest_and_stability():
    doc = Document("alpha", "unicode", 3, "é🙂 abcdefghijklmnopqrstuvwxyz 123456789")
    spans = make_chunks(doc, width=16, overlap=4)
    assert [(s.start, s.end) for s in spans] == [(0, 16), (12, 28), (24, 39)]
    for ordinal, span in enumerate(spans):
        assert span.key == Key("alpha", "unicode", 3, ordinal)
        assert span.text == doc.text[span.start : span.end]
        assert span.digest == hashlib.sha256(span.text.encode()).hexdigest()
    assert spans == make_chunks(doc, width=16, overlap=4)
    assert make_chunks(replace(doc, revision=4), width=16, overlap=4)[0].key != spans[0].key
    with pytest.raises(FrozenInstanceError):
        spans[0].start = 5


def test_whitespace_windows_are_preserved_without_trimming():
    text = "a" + " " * 30 + "b"
    spans = make_chunks(Document("alpha", "spaces", 1, text), width=16, overlap=0)
    assert [s.text for s in spans] == [text[:16], text[16:]]
    assert spans[0].end == spans[1].start


@pytest.mark.parametrize("length, expected", [(1, 1), (16, 1), (17, 2), (28, 2), (29, 3), (384, 32)])
def test_final_suffix_is_not_duplicated(length, expected):
    spans = make_chunks(Document("alpha", "edges", 1, "x" * length), width=16, overlap=4)
    assert len(spans) == expected and spans[-1].end == length


@pytest.mark.parametrize(
    "width, overlap", [(15, 0), (513, 0), (16, -1), (16, 16), (True, 0), (16, True), (16.0, 0)]
)
def test_invalid_window_contract(width, overlap):
    with pytest.raises(ValueError):
        make_chunks(Document("alpha", "edges", 1, "abc"), width=width, overlap=overlap)


def test_window_cap_is_failure_not_silent_truncation():
    with pytest.raises(ValueError, match="too many"):
        make_chunks(Document("alpha", "edges", 1, "x" * 389), width=16, overlap=4)


@pytest.mark.parametrize(
    "changes",
    [
        {"text": ""},
        {"text": " "},
        {"text": "é" * 4097},
        {"revision": True},
        {"active": 1},
        {"groups": ("ops", "ops")},
        {"groups": ([],)},
        {"tenant": "../alpha"},
    ],
)
def test_document_rejects_wrong_current_values(changes):
    with pytest.raises(ValueError):
        replace(Document("alpha", "edges", 1, "abc"), **changes)
