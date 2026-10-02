import math
import unittest

from sticks.core import Stick


class BasicTest(unittest.TestCase):
    def test_zero_input_is_zero(self):
        self.assertEqual(Stick().process(0.0, 0.0), (0.0, 0.0))

    def test_small_input_is_zero(self):
        self.assertEqual(Stick().process(0.1, -0.2), (0.0, 0.0))

    def test_output_is_a_pair_of_floats(self):
        out = Stick().process(0.6, 0.6)
        self.assertEqual(len(out), 2)
        self.assertIsInstance(out[0], float)
        self.assertIsInstance(out[1], float)

    def test_switches_starts_at_zero(self):
        self.assertEqual(Stick().switches, 0)

    def test_empty_calibration_resets_center(self):
        stick = Stick()
        stick.center = (0.3, 0.3)
        stick.calibrate([])
        self.assertEqual(stick.center, (0.0, 0.0))


class DeviceTest(unittest.TestCase):
    def test_add_device_registers(self):
        stick = Stick()
        stick.add_device("pad1")
        self.assertIn("pad1", stick.devices)

    def test_device_center_without_samples_is_zero(self):
        self.assertEqual(Stick().device_center("pad1"), (0.0, 0.0))

    def test_sample_returns_true(self):
        stick = Stick()
        stick.add_device("pad1")
        self.assertTrue(stick.sample("pad1", 0.1, 0.1))

    def test_switches_of_default_starts_at_zero(self):
        self.assertEqual(Stick().switches_of(), 0)

    def test_work_starts_at_zero(self):
        self.assertEqual(Stick().work_count(), 0)


if __name__ == "__main__":
    unittest.main()


class RadialDeadzoneTest(unittest.TestCase):
    def test_diagonal_half_push_matches_radial_spec(self):
        out = Stick().process(0.5, 0.5)
        self.assertAlmostEqual(math.hypot(*out), 0.262, places=3)

    def test_direction_is_preserved(self):
        out = Stick().process(0.5, 0.5)
        self.assertAlmostEqual(out[0], out[1])

    def test_at_deadzone_is_zero(self):
        self.assertEqual(Stick().process(0.4, 0.0), (0.0, 0.0))

    def test_just_above_deadzone_is_tiny(self):
        out = Stick().process(0.41, 0.0)
        self.assertGreater(out[0], 0.0)
        self.assertLess(out[0], 0.01)

    def test_monotonic_non_decreasing(self):
        stick = Stick()
        prev = 0.0
        for step in range(101):
            value = step / 100.0
            length = math.hypot(*stick.process(value, 0.0))
            self.assertGreaterEqual(length, prev - 1e-12)
            prev = length


class CurveTest(unittest.TestCase):
    def test_curve_is_power_not_multiplier(self):
        out = Stick().process(0.7, 0.0)
        self.assertAlmostEqual(math.hypot(*out), 0.25, places=3)

    def test_curve_endpoints(self):
        self.assertEqual(Stick().process(0.0, 0.0), (0.0, 0.0))
        out = Stick().process(1.0, 0.0)
        self.assertAlmostEqual(math.hypot(*out), 1.0)

    def test_exponent_one_is_linear(self):
        out = Stick(exponent=1.0).process(0.7, 0.0)
        self.assertAlmostEqual(out[0], 0.5)


class CalibrationTest(unittest.TestCase):
    def test_center_is_subtracted_in_process(self):
        stick = Stick()
        stick.calibrate([(0.5, 0.0)] * 5)
        self.assertEqual(stick.process(0.5, 0.0), (0.0, 0.0))

    def test_calibrate_writes_per_device_center(self):
        stick = Stick()
        stick.calibrate([(0.2, 0.0)] * 3, device="pad1")
        stick.calibrate([(0.6, 0.0)] * 3, device="pad2")
        self.assertAlmostEqual(stick.device_center("pad1")[0], 0.2)
        self.assertAlmostEqual(stick.device_center("pad2")[0], 0.6)

    def test_sample_updates_rolling_mean_incrementally(self):
        stick = Stick()
        stick.sample("pad1", 0.4, 0.0)
        stick.sample("pad1", 0.4, 0.0)
        self.assertAlmostEqual(stick.device_center("pad1")[0], 0.4)
        stick.sample("pad1", 0.7, 0.0)
        self.assertAlmostEqual(stick.device_center("pad1")[0], 0.5)

    def test_other_device_samples_do_not_move_center(self):
        stick = Stick()
        stick.sample("pad1", 0.4, 0.0)
        stick.sample("pad1", 0.4, 0.0)
        for _ in range(2):
            stick.sample("pad2", 0.8, 0.0)
        self.assertAlmostEqual(stick.device_center("pad1")[0], 0.4)


class HysteresisTest(unittest.TestCase):
    def test_release_threshold_differs_from_enter(self):
        stick = Stick(deadzone=0.4)
        for value in (0.45, 0.35, 0.45, 0.35, 0.45, 0.35):
            stick.process(value, 0.0)
        self.assertEqual(stick.switches, 1)

    def test_full_cycle_counts_two_switches(self):
        stick = Stick(deadzone=0.4)
        stick.process(0.5, 0.0)
        stick.process(0.3, 0.0)
        self.assertEqual(stick.switches, 2)

    def test_deadzone_input_never_counts(self):
        stick = Stick(deadzone=0.4)
        for value in (0.1, 0.2, 0.39, 0.4, 0.1):
            stick.process(value, 0.0)
        self.assertEqual(stick.switches, 0)

    def test_exit_boundary_stays_active(self):
        stick = Stick(deadzone=0.4, release_ratio=0.5)
        stick.process(0.5, 0.0)
        stick.process(0.2, 0.0)
        self.assertEqual(stick.switches, 1)
        stick.process(0.19, 0.0)
        self.assertEqual(stick.switches, 2)


class ClampTest(unittest.TestCase):
    def test_axis_input_is_clamped(self):
        out = Stick().process(1.5, 0.0)
        self.assertAlmostEqual(math.hypot(*out), 1.0)

    def test_diagonal_input_is_clamped(self):
        out = Stick().process(1.5, 1.5)
        self.assertAlmostEqual(math.hypot(*out), 1.0)

    def test_output_never_exceeds_unit_length(self):
        stick = Stick()
        for step in range(-20, 21):
            value = step / 10.0
            out = stick.process(value, value)
            self.assertLessEqual(math.hypot(*out), 1.0 + 1e-9)


class DeviceIsolationTest(unittest.TestCase):
    def test_processing_one_device_does_not_touch_another(self):
        stick = Stick()
        stick.add_device("pad1")
        stick.add_device("pad2")
        stick.process(0.45, 0.0, device="pad1")
        stick.process(0.1, 0.0, device="pad2")
        self.assertEqual(stick.switches_of("pad1"), 1)
        self.assertEqual(stick.switches_of("pad2"), 0)

    def test_states_are_independent(self):
        stick = Stick()
        stick.calibrate([(0.5, 0.0)] * 4, device="pad1")
        self.assertEqual(stick.process(0.5, 0.0, device="pad1"), (0.0, 0.0))
        out = stick.process(0.5, 0.0, device="pad2")
        self.assertGreater(math.hypot(*out), 0.0)


class InvariantTest(unittest.TestCase):
    def test_same_input_sequence_is_deterministic(self):
        sequence = [(0.1, 0.2), (0.5, 0.5), (0.9, -0.3), (0.35, 0.0), (0.45, 0.0)]
        runs = []
        for _ in range(2):
            stick = Stick()
            stick.calibrate([(0.1, 0.0)] * 3)
            runs.append([stick.process(x, y) for x, y in sequence])
        self.assertEqual(runs[0], runs[1])


class ScaleTest(unittest.TestCase):
    def test_work_grows_linearly_with_samples_only(self):
        stick = Stick()
        for index in range(5000):
            stick.sample("pad1", (index % 100) / 100.0, 0.0)
        self.assertEqual(stick.work_count(), 5000)
        self.assertLessEqual(stick.work_count(), 10000)

    def test_work_does_not_depend_on_device_count(self):
        stick = Stick()
        for index in range(1000):
            stick.add_device("pad%d" % index)
        self.assertEqual(stick.work_count(), 0)
        for index in range(1000):
            stick.sample("pad%d" % index, 0.1, 0.0)
        self.assertEqual(stick.work_count(), 1000)

    def test_many_devices_many_samples_stay_fast(self):
        stick = Stick()
        devices = ["pad%d" % index for index in range(1000)]
        for name in devices:
            stick.add_device(name)
        for _ in range(20):
            for name in devices:
                stick.sample(name, 0.1, 0.2)
                stick.process(0.5, 0.5, device=name)
        self.assertEqual(stick.work_count(), 20000)
        center = stick.device_center("pad999")
        self.assertAlmostEqual(center[0], 0.1)
        self.assertAlmostEqual(center[1], 0.2)



if __name__ == "__main__":
    unittest.main()
