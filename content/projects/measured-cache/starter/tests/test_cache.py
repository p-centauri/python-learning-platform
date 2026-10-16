from dataclasses import FrozenInstanceError
import gc
from pathlib import Path
import warnings
import weakref
import pytest
from academy_measured_cache import CacheKey, LruCache, legacy_get


@pytest.mark.parametrize(
    "namespace,id,revision,error",
    [
        (True, "a", 1, TypeError),
        ("a", None, 1, TypeError),
        ("", "a", 1, ValueError),
        ("A", "a", 1, ValueError),
        ("a", "é", 1, ValueError),
        ("a" * 33, "a", 1, ValueError),
        ("a", "a" * 33, 1, ValueError),
        ("a", "a", True, TypeError),
        ("a", "a", 1.0, TypeError),
        ("a", "a", 0, ValueError),
        ("a", "a", 9, ValueError),
    ],
)
def test_key_validation(namespace, id, revision, error):
    with pytest.raises(error):
        CacheKey(namespace, id, revision)


@pytest.mark.parametrize(
    "capacity,error",
    [
        (True, TypeError),
        ("4", TypeError),
        (1.0, TypeError),
        (0, ValueError),
        (-1, ValueError),
        (9, ValueError),
    ],
)
def test_capacity_validation(capacity, error):
    with pytest.raises(error):
        LruCache(capacity)


def test_key_boundaries_equality_hash_and_freezing():
    a = CacheKey("a" * 32, "b" * 32, 8)
    b = CacheKey("a" * 32, "b" * 32, 8)
    assert a == b and hash(a) == hash(b)
    with pytest.raises(FrozenInstanceError):
        a.id = "c"


@pytest.mark.parametrize("value", [None, False, 0, [], object()])
def test_hit_identity_and_no_recomputation(value):
    cache = LruCache(1)
    key = CacheKey("a", "b")
    calls = []
    assert cache.get_or_compute(key, lambda: value) is value

    def forbidden():
        calls.append(True)
        raise AssertionError("hit computed")

    assert cache.get_or_compute(key, forbidden) is value
    info = cache.info()
    assert not calls and info.hits == 1 and info.misses == 1 and info.size == 1


def test_context_and_revision_keys_do_not_collide():
    cache = LruCache(4)
    keys = [CacheKey("team-a", "same"), CacheKey("team-b", "same"), CacheKey("team-a", "same", 2)]
    for index, key in enumerate(keys):
        assert cache.get_or_compute(key, lambda: index) == index
    assert cache.info().keys == tuple(keys) and cache.info().misses == 3


def test_lru_hit_promotion_and_eviction():
    cache = LruCache(2)
    a, b, c = [CacheKey("a", n) for n in ["a", "b", "c"]]
    cache.get_or_compute(a, lambda: 1)
    cache.get_or_compute(b, lambda: 2)
    assert cache.get_or_compute(a, lambda: 99) == 1
    assert cache.info().keys == (b, a)
    cache.get_or_compute(c, lambda: 3)
    assert cache.info().keys == (a, c)
    assert cache.get_or_compute(b, lambda: 20) == 20
    assert cache.info().keys == (c, b) and cache.info().hits == 1 and cache.info().misses == 4


@pytest.mark.parametrize("capacity", [1, 4, 8])
def test_entry_bound_over_many_inputs(capacity):
    cache = LruCache(capacity)
    for index in range(32):
        cache.get_or_compute(CacheKey("a", "key-" + str(index)), lambda: index)
        assert cache.info().size <= capacity
    assert cache.info().size == capacity and cache.info().misses == 32


def test_failed_compute_preserves_entries_order_and_counts_attempt():
    cache = LruCache(2)
    a, b = [CacheKey("a", n) for n in ["a", "b"]]
    cache.get_or_compute(a, lambda: 1)
    before = cache.info()
    error = LookupError("compute")

    def fail():
        raise error

    with pytest.raises(LookupError) as caught:
        cache.get_or_compute(b, fail)
    assert caught.value is error and cache.info().keys == before.keys and cache.info().misses == 2
    assert cache.get_or_compute(b, lambda: 2) == 2 and cache.info().misses == 3


@pytest.mark.parametrize("operation", ["get", "clear"])
def test_reentrant_access_fails_without_extra_state_mutation(operation):
    cache = LruCache(2)
    a, b = [CacheKey("a", n) for n in ["a", "b"]]
    cache.get_or_compute(a, lambda: 1)

    def reentrant():
        if operation == "get":
            return cache.get_or_compute(a, lambda: 99)
        cache.clear()
        return 99

    with pytest.raises(RuntimeError, match="Reentrant"):
        cache.get_or_compute(b, reentrant)
    assert cache.info().keys == (a,) and cache.info().hits == 0 and cache.info().misses == 2
    assert cache.get_or_compute(b, lambda: 2) == 2


def test_info_allowed_during_compute_is_a_fixed_snapshot():
    cache = LruCache(1)
    key = CacheKey("a", "b")
    snapshots = []

    def compute():
        snapshots.append(cache.info())
        return 1

    cache.get_or_compute(key, compute)
    assert snapshots[0].keys == () and snapshots[0].misses == 1
    assert cache.info().keys == (key,)
    with pytest.raises(FrozenInstanceError):
        snapshots[0].hits = 3


def test_wrong_key_rejected_without_computation_or_counter_changes():
    cache = LruCache(2)
    before = cache.info()
    with pytest.raises(TypeError):
        cache.get_or_compute("bad", lambda: pytest.fail("computed"))
    assert cache.info() == before


def test_clear_resets_counts_releases_references_and_never_closes():
    closed = []

    class Value:
        def close(self):
            closed.append(True)

    cache = LruCache(1)
    key = CacheKey("a", "b")
    value = cache.get_or_compute(key, Value)
    reference = weakref.ref(value)
    cache.get_or_compute(key, lambda: None)
    del value
    gc.collect()
    assert reference() is not None
    cache.clear()
    gc.collect()
    assert reference() is None and not closed
    assert cache.info().keys == () and cache.info().hits == cache.info().misses == 0
    assert cache.get_or_compute(key, lambda: 7) == 7


def test_eviction_drops_cache_reference_but_does_not_close_or_invalidate_borrowers():
    closed = []

    class Value:
        def close(self):
            closed.append(True)

    cache = LruCache(1)
    a, b = [CacheKey("a", n) for n in ["a", "b"]]
    value = Value()
    held = cache.get_or_compute(a, lambda: value)
    cache.get_or_compute(b, lambda: Value())
    assert held is value and not closed


def test_mutable_values_are_returned_without_copy_or_freeze():
    cache = LruCache(1)
    key = CacheKey("a", "b")
    value = []
    held = cache.get_or_compute(key, lambda: value)
    held.append(7)
    assert cache.get_or_compute(key, lambda: []) == [7]


def test_legacy_adapter_warning_caller_location_and_preserved_hit_behavior():
    cache = LruCache(1)
    key = CacheKey("a", "b")
    value = object()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        assert legacy_get(cache, key, lambda: value) is value
        assert legacy_get(cache, key, lambda: pytest.fail("hit")) is value
    assert len(caught) == 2 and all(w.category is DeprecationWarning for w in caught)
    assert all(Path(w.filename).resolve() == Path(__file__).resolve() for w in caught)
    assert cache.info().hits == cache.info().misses == 1


def test_warning_as_error_prevents_delegate_effects():
    cache = LruCache(1)
    key = CacheKey("a", "b")
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        with pytest.raises(DeprecationWarning):
            legacy_get(cache, key, lambda: pytest.fail("delegate ran"))
    assert cache.info().keys == () and cache.info().hits == cache.info().misses == 0
