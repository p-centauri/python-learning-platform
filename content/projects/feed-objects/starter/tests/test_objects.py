from dataclasses import FrozenInstanceError
import pytest
from academy_feed_objects import BoundedInt, Budget, FeedKey, Reading, Snapshot

@pytest.mark.parametrize("value", [0, 1, 64])
def test_descriptor_inclusive_range(value):
    budget = Budget(value)
    assert budget.limit == value and budget.reserve == 0

@pytest.mark.parametrize("value", [True, False, 1.0, "1", None])
def test_descriptor_wrong_types_keep_previous(value):
    budget = Budget(3)
    with pytest.raises(TypeError):
        budget.limit = value
    assert budget.limit == 3

@pytest.mark.parametrize("value", [-1, 65])
def test_descriptor_range_keeps_previous(value):
    budget = Budget(3)
    with pytest.raises(ValueError):
        budget.limit = value
    assert budget.limit == 3

def test_class_access_and_per_instance_storage():
    assert isinstance(Budget.limit, BoundedInt)
    assert Budget.limit is vars(Budget)["limit"]
    a, b = Budget(1, 2), Budget(3, 4)
    a.limit = 9
    assert (a.limit, a.reserve, b.limit, b.reserve) == (9, 2, 3, 4)
    # Ordinary lookup uses the data descriptor before the same-named instance entry.
    vars(a)["limit"] = 99
    assert a.limit == 9

def test_uninitialized_field_is_missing_not_zero():
    budget = object.__new__(Budget)
    budget._values = {}
    with pytest.raises(AttributeError, match="limit"):
        _ = budget.limit

def test_inherited_descriptor_uses_subclass_instance():
    class Child(Budget):
        pass
    assert Child.limit is Budget.limit
    assert Child(4).limit == 4

def test_rebinding_is_rejected_and_unbound_descriptor_fails():
    field = BoundedInt()
    with pytest.raises(RuntimeError, match="not bound"):
        field.__set__(Budget(2), 3)
    field.__set_name__(Budget, "extra")
    field.__set_name__(Budget, "extra")
    with pytest.raises(ValueError):
        field.__set_name__(Budget, "different")

@pytest.mark.parametrize("namespace,name", [("demo", "api"), ("a", "z-9"), ("a"*32, "b"*32)])
def test_key_equal_hash_and_dictionary_lookup(namespace, name):
    a, b = FeedKey(namespace, name), FeedKey(namespace, name)
    assert a is not b and a == b and hash(a) == hash(b)
    assert {a: 7}[b] == 7 and len({a, b}) == 1

@pytest.mark.parametrize("other", [FeedKey("other", "api"), FeedKey("demo", "other")])
def test_both_identity_fields_matter(other):
    assert FeedKey("demo", "api") != other
    # Unequal objects need not have unequal hashes.

@pytest.mark.parametrize("other", [None, ("demo", "api"), "demo/api", 1])
def test_foreign_comparison_defers(other):
    key = FeedKey("demo", "api")
    assert key.__eq__(other) is NotImplemented
    assert (key == other) is False

def test_subclass_comparison_and_reverse_dispatch():
    class Child(FeedKey):
        pass
    key = FeedKey("demo", "api")
    assert key.__eq__(Child("demo", "api")) is NotImplemented
    class Accept:
        def __eq__(self, other):
            return isinstance(other, FeedKey)
    assert key == Accept()

def test_key_is_frozen_and_repr_explains_identity():
    key = FeedKey("demo", "api")
    with pytest.raises(FrozenInstanceError):
        key.name = "changed"
    assert "demo" in repr(key) and "api" in repr(key)

@pytest.mark.parametrize("bad", ["", "A", "a/b", "é", "a"*33])
def test_bounded_ascii_key_fields(bad):
    with pytest.raises(ValueError):
        FeedKey("demo", bad)
    with pytest.raises(ValueError):
        FeedKey(bad, "api")

class TextSubclass(str):
    """Subclasses can override equality/hash, so the key accepts exact strings."""


@pytest.mark.parametrize("bad", [None, 1, TextSubclass("demo")])
def test_key_wrong_type(bad):
    with pytest.raises(TypeError):
        FeedKey(bad, "api")

@pytest.mark.parametrize("value", [0, 60000])
def test_reading_boundaries(value):
    assert Reading(FeedKey("demo", "api"), value).value == value

@pytest.mark.parametrize("bad", [True, 1.0, "1", None])
def test_reading_wrong_type(bad):
    with pytest.raises(TypeError):
        Reading(FeedKey("demo", "api"), bad)

@pytest.mark.parametrize("bad", [-1, 60001])
def test_reading_range(bad):
    with pytest.raises(ValueError):
        Reading(FeedKey("demo", "api"), bad)

def test_reading_rejects_foreign_key():
    with pytest.raises(TypeError):
        Reading("demo/api", 1)

def rows(n):
    return [Reading(FeedKey("demo", f"row-{i}"), i) for i in range(n)]

def test_snapshot_order_index_slice_iteration_and_truth():
    source = rows(3)
    snapshot = Snapshot(iter(source))
    assert len(snapshot) == 3 and bool(snapshot)
    assert list(snapshot) == source and list(reversed(snapshot)) == source[::-1]
    assert snapshot[0] is source[0] and snapshot[-1] is source[-1]
    assert snapshot[1:] == tuple(source[1:]) and snapshot[::-1] == tuple(source[::-1])
    assert source[1] in snapshot and snapshot.index(source[1]) == 1
    with pytest.raises(IndexError):
        _ = snapshot[3]
    assert not Snapshot([])

def test_snapshot_copies_input_and_is_frozen():
    source = rows(2)
    snapshot = Snapshot(source)
    source.clear()
    assert len(snapshot) == 2
    with pytest.raises(FrozenInstanceError):
        snapshot._rows = ()
    with pytest.raises(FrozenInstanceError):
        snapshot[0].value = 9

def test_duplicate_equal_keys_rejected_even_with_different_values():
    with pytest.raises(ValueError, match="Duplicate"):
        Snapshot([Reading(FeedKey("demo", "api"), 1), Reading(FeedKey("demo", "api"), 2)])

def test_snapshot_exact_bound_and_no_trust_in_reported_length():
    assert len(Snapshot(rows(64))) == 64
    pulled = []
    def endless():
        for i in range(1000):
            pulled.append(i)
            yield Reading(FeedKey("demo", f"row-{i}"), i)
    with pytest.raises(ValueError, match="Too many"):
        Snapshot(endless())
    assert len(pulled) == 65
    class Liar:
        def __len__(self):
            return 0
        def __iter__(self):
            return iter(rows(65))
    with pytest.raises(ValueError):
        Snapshot(Liar())

def test_snapshot_borrows_iterator_and_propagates_failure():
    class Broken:
        def __iter__(self):
            yield rows(1)[0]
            raise OSError("input stopped")
    with pytest.raises(OSError, match="input stopped"):
        Snapshot(Broken())
    iterator = iter(rows(66))
    with pytest.raises(ValueError):
        Snapshot(iterator)
    assert next(iterator).key.name == "row-65"

@pytest.mark.parametrize("bad", [None, 1, {"key": "api"}])
def test_snapshot_rejects_wrong_element_types(bad):
    with pytest.raises(TypeError):
        Snapshot([bad])
