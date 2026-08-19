import unittest

from sovrune.core import BusinessState, Evidence, Metric
from sovrune.demo import AcmeAdapter
from sovrune.offices import run_operating_loop


class CoreTest(unittest.TestCase):
    def test_demo_state_validates_and_has_provenance(self):
        state = AcmeAdapter().build_state()
        state.validate()
        self.assertGreater(state.confidence(), .9)
        self.assertIsNotNone(state.north_star.target)

    def test_forbidden_key_is_rejected(self):
        state = BusinessState("Unsafe", Metric("Goal", 1, "count", evidence=Evidence("test", "today", 1)), [],
                              risks=[{"email": "not-allowed"}])
        with self.assertRaises(ValueError):
            state.validate()

    def test_loop_stops_at_human_boundary(self):
        steps = run_operating_loop(AcmeAdapter().build_state())
        approval = next(step for step in steps if step["office"] == "Approval")
        self.assertTrue(approval["requires_human"])


if __name__ == "__main__":
    unittest.main()
