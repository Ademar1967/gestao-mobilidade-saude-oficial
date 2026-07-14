from django.test.runner import DiscoverRunner


class PollsDiscoverRunner(DiscoverRunner):
    """Restricts default discovery to the polls app to avoid duplicate package imports."""

    def build_suite(self, test_labels=None, extra_tests=None, **kwargs):
        labels = test_labels or ["polls.tests"]
        return super().build_suite(
            test_labels=labels, extra_tests=extra_tests, **kwargs
        )
