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


def _length(vector):
    return (vector[0] ** 2 + vector[1] ** 2) ** 0.5


class RadialTest(unittest.TestCase):
    def test_diagonal_uses_radial_length(self):
        out = Stick().process(0.5, 0.5)
        self.assertAlmostEqual(_length(out), 0.262, places=3)

    def test_direction_preserved(self):
        x, y = Stick().process(0.5, 0.5)
        self.assertAlmostEqual(x, y)
        self.assertGreater(x, 0.0)
        self.assertGreater(y, 0.0)

    def test_rest_output_is_zero(self):
        stick = Stick()
        for _ in range(3):
            self.assertEqual(stick.process(0.0, 0.0), (0.0, 0.0))
            self.assertEqual(stick.process(0.3, 0.0), (0.0, 0.0))

    def test_monotonic_non_decreasing(self):
        stick = Stick()
        previous = 0.0
        for step in range(101):
            radius = step / 100.0
            current = _length(stick.process(radius, 0.0))
            self.assertGreaterEqual(current + 1e-12, previous)
            previous = current
        self.assertAlmostEqual(previous, 1.0, places=9)


class CurveTest(unittest.TestCase):
    def test_curve_is_power_not_multiply(self):
        out = Stick(exponent=2.0).process(0.7, 0.0)
        self.assertAlmostEqual(_length(out), 0.250, places=3)

    def test_endpoints_of_curve(self):
        stick = Stick(exponent=3.0)
        self.assertEqual(stick.process(0.4, 0.0), (0.0, 0.0))
        self.assertEqual(stick.process(1.0, 0.0), (1.0, 0.0))

    def test_higher_exponent_shrinks_inner_radius(self):
        low = _length(Stick(exponent=1.0).process(0.7, 0.0))
        high = _length(Stick(exponent=4.0).process(0.7, 0.0))
        self.assertLess(high, low)


class CalibrationTest(unittest.TestCase):
    def test_calibrated_center_is_subtracted(self):
        stick = Stick()
        stick.calibrate([(0.5, 0.0)] * 5)
        self.assertEqual(stick.process(0.5, 0.0), (0.0, 0.0))

    def test_empty_calibration_clears_drift(self):
        stick = Stick()
        stick.calibrate([(0.5, 0.0)] * 5)
        stick.calibrate([])
        self.assertEqual(stick.device_center("default"), (0.0, 0.0))
        self.assertGreater(_length(stick.process(0.5, 0.0)), 0.0)

    def test_calibration_is_per_device(self):
        stick = Stick()
        stick.calibrate([(0.3, 0.1)], device="pad1")
        stick.calibrate([(0.8, 0.2)], device="pad2")
        self.assertAlmostEqual(stick.device_center("pad1")[0], 0.3)
        self.assertAlmostEqual(stick.device_center("pad2")[0], 0.8)

    def test_sample_maintains_incremental_mean(self):
        stick = Stick()
        values = [(0.1, 0.0), (0.3, 0.0), (0.5, 0.0)]
        for x, y in values:
            stick.sample("pad1", x, y)
        self.assertAlmostEqual(stick.device_center("pad1")[0], 0.3)
        self.assertEqual(stick.device_center("pad2"), (0.0, 0.0))


class HysteresisTest(unittest.TestCase):
    def test_release_threshold_differs_from_enter(self):
        stick = Stick(deadzone=0.4, release_ratio=0.8)
        stick.process(0.45, 0.0)
        self.assertEqual(stick.switches, 1)
        stick.process(0.35, 0.0)
        self.assertEqual(stick.switches, 1)
        stick.process(0.31, 0.0)
        self.assertEqual(stick.switches, 2)

    def test_inputs_in_deadzone_never_count(self):
        stick = Stick(deadzone=0.4)
        for value in (0.0, 0.1, 0.4, 0.2, 0.0):
            stick.process(value, 0.0)
        self.assertEqual(stick.switches, 0)

    def test_cli_sequence_switches_once(self):
        stick = Stick(deadzone=0.4)
        for value in (0.45, 0.35, 0.45, 0.35, 0.45, 0.35):
            stick.process(value, 0.0)
        self.assertEqual(stick.switches, 1)


class ClampTest(unittest.TestCase):
    def test_axis_overdrive_clamped(self):
        self.assertAlmostEqual(_length(Stick().process(1.5, 0.0)), 1.0)

    def test_diagonal_overdrive_clamped(self):
        x, y = Stick().process(3.0, 4.0)
        self.assertAlmostEqual(_length((x, y)), 1.0)
        self.assertAlmostEqual(x / y, 3.0 / 4.0)


class DeviceIsolationTest(unittest.TestCase):
    def test_switches_are_per_device(self):
        stick = Stick()
        stick.process(0.45, 0.0, device="pad1")
        stick.process(0.1, 0.0, device="pad2")
        self.assertEqual(stick.switches_of("pad1"), 1)
        self.assertEqual(stick.switches_of("pad2"), 0)

    def test_processing_one_device_leaves_other_state(self):
        stick = Stick()
        stick.process(0.9, 0.0, device="pad1")
        for value in (0.1, 0.0, 0.3):
            stick.process(value, 0.0, device="pad2")
        self.assertEqual(stick.switches_of("pad1"), 1)
        self.assertEqual(stick.switches_of("pad2"), 0)
        stick.process(0.35, 0.0, device="pad1")
        self.assertEqual(stick.switches_of("pad1"), 1)

    def test_sample_streams_are_not_mixed(self):
        stick = Stick()
        for _ in range(2):
            stick.sample("pad1", 0.4, 0.0)
        for _ in range(2):
            stick.sample("pad2", 0.8, 0.0)
        self.assertAlmostEqual(stick.device_center("pad1")[0], 0.4)
        self.assertAlmostEqual(stick.device_center("pad2")[0], 0.8)


class DeterminismTest(unittest.TestCase):
    def test_repeated_sequence_gives_same_result(self):
        def run():
            stick = Stick()
            stick.calibrate([(0.05, -0.05)], device="pad1")
            results = []
            for value in (0.45, 0.35, 0.9, 0.31, 0.0, 0.6):
                results.append(stick.process(value, value, device="pad1"))
            return results
        self.assertEqual(run(), run())


class WorkTest(unittest.TestCase):
    def test_work_does_not_grow_with_samples(self):
        stick = Stick()
        stick.add_device("pad1")
        for index in range(5000):
            stick.sample("pad1", (index % 100) / 100.0, 0.0)
        stick.device_center("pad1")
        self.assertLessEqual(stick.work_count(), 10000)

    def test_scale_many_devices(self):
        stick = Stick()
        for index in range(10000):
            name = "pad%d" % index
            stick.add_device(name)
            stick.sample(name, 0.1, 0.0)
            stick.process(0.5, 0.5, device=name)
        self.assertEqual(len(stick.devices), 10000)
        self.assertEqual(stick.switches_of("pad9999"), 1)
        self.assertLessEqual(stick.work_count(), 10000)
