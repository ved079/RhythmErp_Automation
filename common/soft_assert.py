"""
soft_assert.py
--------------
Soft assertion utility for test consolidation.

Collects multiple assertion failures during a single test execution
without stopping at the first failure. Call ``check_all()`` at the
end of the test to raise a combined ``AssertionError`` that lists
every failure.

Usage::

    sa = SoftAssert()
    sa.assert_true(condition, "Expected X to be true")
    sa.assert_equal(actual, expected, "Values should match")
    sa.assert_in(item, container, "Item should be in container")
    # ... more checks ...
    sa.check_all()  # raises if any failures collected

This allows grouping 3-5 related assertions into a single E2E test
function while still getting full diagnostics for every failure.
"""


class SoftAssert:
    """Collects assertion failures without stopping execution.

    All ``assert_*`` methods store failures in a list instead of
    raising immediately.  Call :meth:`check_all` at the end of the
    test to raise a single combined ``AssertionError``.

    Attributes:
        failures: List of failure message strings.
    """

    def __init__(self):
        self.failures: list[str] = []

    # ----- Core assertions -----

    def assert_true(self, condition: bool, msg: str = "") -> None:
        """Assert that *condition* is truthy.

        Args:
            condition: The value to evaluate.
            msg: Human-readable message on failure.
        """
        if not condition:
            self.failures.append(msg or "Expected True, got False")

    def assert_false(self, condition: bool, msg: str = "") -> None:
        """Assert that *condition* is falsy."""
        if condition:
            self.failures.append(msg or "Expected False, got True")

    def assert_equal(self, actual, expected, msg: str = "") -> None:
        """Assert *actual* == *expected*."""
        if actual != expected:
            self.failures.append(
                msg or f"Expected '{expected}', got '{actual}'"
            )

    def assert_not_equal(self, actual, unexpected, msg: str = "") -> None:
        """Assert *actual* != *unexpected*."""
        if actual == unexpected:
            self.failures.append(
                msg or f"Expected value different from '{unexpected}', "
                       f"but both are equal"
            )

    def assert_in(self, item, container, msg: str = "") -> None:
        """Assert *item* is in *container*."""
        if item not in container:
            self.failures.append(
                msg or f"'{item}' not found in {type(container).__name__}"
            )

    def assert_not_in(self, item, container, msg: str = "") -> None:
        """Assert *item* is NOT in *container*."""
        if item in container:
            self.failures.append(
                msg or f"'{item}' unexpectedly found in "
                       f"{type(container).__name__}"
            )

    def assert_less_equal(self, actual, threshold, msg: str = "") -> None:
        """Assert *actual* <= *threshold*."""
        if actual > threshold:
            self.failures.append(
                msg or f"{actual} > {threshold} (expected <= {threshold})"
            )

    def assert_greater_equal(self, actual, threshold, msg: str = "") -> None:
        """Assert *actual* >= *threshold*."""
        if actual < threshold:
            self.failures.append(
                msg or f"{actual} < {threshold} (expected >= {threshold})"
            )

    def assert_is_none(self, value, msg: str = "") -> None:
        """Assert *value* is None."""
        if value is not None:
            self.failures.append(msg or f"Expected None, got '{value}'")

    def assert_is_not_none(self, value, msg: str = "") -> None:
        """Assert *value* is not None."""
        if value is None:
            self.failures.append(msg or "Expected non-None value, got None")

    # ----- Generic failure -----

    def fail(self, msg: str = "") -> None:
        """Explicitly record a failure with the given message.

        Useful when a check is too complex for a simple assert_* call
        and the caller has already determined that a failure occurred.

        Args:
            msg: Human-readable message describing the failure.
        """
        self.failures.append(msg or "Explicit failure (no message provided)")

    # ----- Check & raise -----

    @property
    def failure_count(self) -> int:
        """Number of failures collected so far."""
        return len(self.failures)

    @property
    def passed(self) -> bool:
        """True if no failures have been collected."""
        return len(self.failures) == 0

    def check_all(self) -> None:
        """Raise ``AssertionError`` if any failures were collected.

        The error message lists every failure with a bullet point.

        Raises:
            AssertionError: Combined message of all collected failures.
        """
        if self.failures:
            nl = "\n  - "
            raise AssertionError(
                f"{len(self.failures)} soft assertion(s) failed:"
                f"{nl}{nl.join(self.failures)}"
            )

    def __repr__(self) -> str:
        status = "PASSED" if self.passed else f"{self.failure_count} failure(s)"
        return f"<SoftAssert: {status}>"
