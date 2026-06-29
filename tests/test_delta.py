"""Tests for delta detection module."""

from src.delta import compute_delta


def test_all_new():
    old = {}
    new = {"1": "aaa", "2": "bbb"}
    delta = compute_delta(old, new)
    assert set(delta["added"]) == {"1", "2"}
    assert delta["updated"] == []
    assert delta["skipped"] == []
    assert delta["removed"] == []


def test_no_changes():
    old = {"1": "aaa", "2": "bbb"}
    new = {"1": "aaa", "2": "bbb"}
    delta = compute_delta(old, new)
    assert delta["added"] == []
    assert delta["updated"] == []
    assert set(delta["skipped"]) == {"1", "2"}
    assert delta["removed"] == []


def test_mixed_changes():
    old = {"1": "aaa", "2": "bbb", "3": "ccc"}
    new = {"1": "aaa", "2": "CHANGED", "4": "ddd"}
    delta = compute_delta(old, new)
    assert delta["added"] == ["4"]
    assert delta["updated"] == ["2"]
    assert delta["skipped"] == ["1"]
    assert delta["removed"] == ["3"]


def test_all_removed():
    old = {"1": "aaa", "2": "bbb"}
    new = {}
    delta = compute_delta(old, new)
    assert delta["added"] == []
    assert delta["updated"] == []
    assert delta["skipped"] == []
    assert set(delta["removed"]) == {"1", "2"}
