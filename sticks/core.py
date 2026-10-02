"""摇杆处理：多设备校准台账、径向死区、响应曲线、死区滞回与输出钳制。

缺陷：死区按每轴判、曲线用乘法顶替幂、校准偏移不参与运算、滞回不生效、
输出不钳制、所有设备共用一份中心与状态、采样混在一起且每次重扫全部样本。
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
        self.devices = {}
        self.samples = []
        self.work = 0

    def add_device(self, name):
        """登记一个设备。"""
        self.devices[name] = True
        return True

    def calibrate(self, samples, device="default"):
        """用一批采样设置中心偏移。"""
        if not samples:
            self.center = (0.0, 0.0)
            return self.center
        count = len(samples)
        self.center = (sum(item[0] for item in samples) / count,
                       sum(item[1] for item in samples) / count)
        return self.center

    def sample(self, device, x, y):
        """记录一个静止采样。"""
        self.work += len(self.samples)
        self.samples.append((device, x, y))
        return True

    def device_center(self, device):
        """某个设备当前的中心偏移。"""
        self.work += len(self.samples)
        if not self.samples:
            return (0.0, 0.0)
        count = len(self.samples)
        return (sum(item[1] for item in self.samples) / count,
                sum(item[2] for item in self.samples) / count)

    def process(self, x, y, device="default"):
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

    def switches_of(self, device="default"):
        """某个设备的累计状态切换次数。"""
        return self.switches

    def work_count(self):
        return self.work
