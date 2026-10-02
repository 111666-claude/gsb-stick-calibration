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
