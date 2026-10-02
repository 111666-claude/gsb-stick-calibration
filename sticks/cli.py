"""命令行入口：跑摇杆样例。"""

import argparse
import math

from .core import Stick


def build_parser():
    parser = argparse.ArgumentParser(prog="stick-calibration", description="摇杆处理")
    parser.add_argument("--sample", default="radial",
                        help="radial / curve / drift / hysteresis / clamp / devices / mix / work")
    return parser


def length(vector):
    return math.hypot(vector[0], vector[1])


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.sample == "radial":
        print("len=%.3f" % length(Stick().process(0.5, 0.5)))
    elif args.sample == "curve":
        print("len=%.3f" % length(Stick().process(0.7, 0.0)))
    elif args.sample == "drift":
        stick = Stick()
        stick.calibrate([(0.5, 0.0)] * 5)
        print("len=%.3f" % length(stick.process(0.5, 0.0)))
    elif args.sample == "hysteresis":
        stick = Stick(deadzone=0.4)
        for value in (0.45, 0.35, 0.45, 0.35, 0.45, 0.35):
            stick.process(value, 0.0)
        print("switches=%d" % stick.switches)
    elif args.sample == "clamp":
        print("len=%.3f" % length(Stick().process(1.5, 0.0)))
    elif args.sample == "devices":
        stick = Stick()
        stick.add_device("pad1")
        stick.add_device("pad2")
        stick.process(0.45, 0.0, device="pad1")
        stick.process(0.1, 0.0, device="pad2")
        print("pad1=%d pad2=%d" % (stick.switches_of("pad1"), stick.switches_of("pad2")))
    elif args.sample == "mix":
        stick = Stick()
        stick.add_device("pad1")
        stick.add_device("pad2")
        for _ in range(2):
            stick.sample("pad1", 0.4, 0.0)
        for _ in range(2):
            stick.sample("pad2", 0.8, 0.0)
        print("center=%.3f" % stick.device_center("pad1")[0])
    elif args.sample == "work":
        stick = Stick()
        stick.add_device("pad1")
        for index in range(5000):
            stick.sample("pad1", (index % 100) / 100.0, 0.0)
        print("work=%d" % stick.work_count())
    else:
        raise SystemExit("需要 --sample radial|curve|drift|hysteresis|clamp|devices|mix|work")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
