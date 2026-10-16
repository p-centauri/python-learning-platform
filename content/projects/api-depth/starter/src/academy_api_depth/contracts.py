class InvalidSignature(Exception):
    """Missing, malformed, stale or untrusted authentication; never include private input."""


class DeliveryConflict(Exception):
    """Same namespace/delivery identity, different authenticated raw bytes."""
