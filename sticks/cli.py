"""命令行入口：跑摇杆样例。"""

import argparse
import math

from .core import Stick


def build_parser():
    parser = argparse.ArgumentParser(prog="stick-calibration", description="摇杆处理")
    parser.add_argument("--sample", default="radial",
                        help="radial / curve / drift / hysteresis / clamp")
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
    else:
        raise SystemExit("需要 --sample radial|curve|drift|hysteresis|clamp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
