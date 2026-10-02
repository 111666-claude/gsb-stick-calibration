"""摇杆处理：多设备校准台账、径向死区、响应曲线、死区滞回与输出钳制。

每个设备各自维护中心偏移（滚动均值）、激活状态与切换计数；
sample/device_center/process 均为单次摊还 O(1)，不随采样数或设备数增长。
"""

import math


class _DeviceState:
    """单个设备的台账：滚动均值、激活状态与切换计数。"""

    __slots__ = ("sum_x", "sum_y", "count", "active", "switches")

    def __init__(self):
        self.sum_x = 0.0
        self.sum_y = 0.0
        self.count = 0
        self.active = False
        self.switches = 0

    def center(self):
        if self.count == 0:
            return (0.0, 0.0)
        return (self.sum_x / self.count, self.sum_y / self.count)


class Stick:
    """把原始摇杆坐标转成响应后的坐标。"""

    def __init__(self, deadzone=0.4, exponent=2.0, release_ratio=0.8):
        self.deadzone = deadzone
        self.exponent = exponent
        self.release_ratio = release_ratio
        self.devices = {}
        self.work = 0

    def _state(self, device):
        state = self.devices.get(device)
        if state is None:
            state = self.devices[device] = _DeviceState()
        return state

    @property
    def center(self):
        return self._state("default").center()

    @center.setter
    def center(self, value):
        state = self._state("default")
        state.sum_x = float(value[0])
        state.sum_y = float(value[1])
        state.count = 1

    @property
    def active(self):
        return self._state("default").active

    @property
    def switches(self):
        return self._state("default").switches

    def add_device(self, name):
        """登记一个设备。"""
        self.devices.setdefault(name, _DeviceState())
        return True

    def calibrate(self, samples, device="default"):
        """用一批采样直接写入该设备的中心偏移。"""
        state = self._state(device)
        if not samples:
            state.sum_x = 0.0
            state.sum_y = 0.0
            state.count = 0
            return (0.0, 0.0)
        state.sum_x = float(sum(item[0] for item in samples))
        state.sum_y = float(sum(item[1] for item in samples))
        state.count = len(samples)
        return state.center()

    def sample(self, device, x, y):
        """增量维护该设备的滚动均值，单次 O(1)。"""
        state = self._state(device)
        state.sum_x += x
        state.sum_y += y
        state.count += 1
        return True

    def device_center(self, device):
        """某个设备当前的中心偏移（滚动均值）。"""
        return self._state(device).center()

    def process(self, x, y, device="default"):
        """处理一帧摇杆输入：扣中心、钳制、径向死区、滞回、响应曲线。"""
        state = self._state(device)
        center_x, center_y = state.center()
        x -= center_x
        y -= center_y

        magnitude = math.hypot(x, y)
        if magnitude > 1.0:
            x /= magnitude
            y /= magnitude
            magnitude = 1.0

        enter = self.deadzone
        release = self.deadzone * self.release_ratio
        if state.active:
            if magnitude < release:
                state.active = False
                state.switches += 1
                return (0.0, 0.0)
        else:
            if magnitude > enter:
                state.active = True
                state.switches += 1
            else:
                return (0.0, 0.0)

        radius = (magnitude - enter) / (1.0 - enter)
        if radius <= 0.0:
            return (0.0, 0.0)
        radius = radius ** self.exponent
        scale = radius / magnitude
        return (x * scale, y * scale)

    def switches_of(self, device="default"):
        """某个设备的累计状态切换次数。"""
        return self._state(device).switches

    def work_count(self):
        return self.work
