"""摇杆处理：中心偏移校准、径向死区、响应曲线、死区滞回与输出钳制。

缺陷：死区按每轴独立判断、曲线用乘法顶替幂、校准结果不参与运算、
滞回不生效、输出不钳制。
"""

import math


class Stick:
    """把原始摇杆坐标转成响应后的坐标。"""

    def __init__(self, deadzone=0.4, exponent=2.0, release_ratio=0.8):
        self.deadzone = deadzone
        self.exponent = exponent
        self.release_ratio = release_ratio
        self.center = (0.0, 0.0)
        self.active = False
        self.switches = 0

    def calibrate(self, samples):
        """用静止采样求中心偏移。"""
        if not samples:
            self.center = (0.0, 0.0)
            return self.center
        count = len(samples)
        self.center = (sum(s[0] for s in samples) / count,
                       sum(s[1] for s in samples) / count)
        return self.center

    def process(self, x, y):
        """处理一帧摇杆输入。"""
        magnitude = max(abs(x), abs(y))
        if magnitude > self.deadzone and not self.active:
            self.active = True
            self.switches += 1
        elif magnitude <= self.deadzone and self.active:
            self.active = False
            self.switches += 1
        return self._axis(x), self._axis(y)

    def _axis(self, value):
        if abs(value) <= self.deadzone:
            return 0.0
        radius = (abs(value) - self.deadzone) / (1 - self.deadzone)
        radius = radius * self.exponent
        return math.copysign(radius, value)
