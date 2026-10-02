"""摇杆处理：多设备校准台账、径向死区、响应曲线、死区滞回与输出钳制。

每个设备各自维护中心偏移、激活状态与切换计数；采样按设备做增量
滚动均值（单次摊还 O(1)）；process 先扣中心，再按径向长度做
钳制、滞回、死区映射与幂曲线，输出长度不超过 1。
"""

import math


class _DeviceState:
    """单个设备的台账：滚动均值、激活状态、切换计数。"""

    __slots__ = ("count", "sum_x", "sum_y", "center", "active", "switches")

    def __init__(self):
        self.count = 0
        self.sum_x = 0.0
        self.sum_y = 0.0
        self.center = (0.0, 0.0)
        self.active = False
        self.switches = 0


class Stick:
    """把原始摇杆坐标转成响应后的坐标。"""

    def __init__(self, deadzone=0.4, exponent=2.0, release_ratio=0.8):
        self.deadzone = deadzone
        self.exponent = exponent
        self.release_ratio = release_ratio
        self.devices = {}
        self._states = {}
        self.work = 0

    def _state(self, device):
        state = self._states.get(device)
        if state is None:
            state = _DeviceState()
            self._states[device] = state
        return state

    def add_device(self, name):
        """登记一个设备。"""
        self.devices[name] = True
        self._state(name)
        return True

    def calibrate(self, samples, device="default"):
        """用一批采样直接写入该设备的中心偏移与滚动均值状态。"""
        state = self._state(device)
        if not samples:
            state.count = 0
            state.sum_x = 0.0
            state.sum_y = 0.0
            state.center = (0.0, 0.0)
            return state.center
        count = len(samples)
        sum_x = math.fsum(item[0] for item in samples)
        sum_y = math.fsum(item[1] for item in samples)
        state.count = count
        state.sum_x = sum_x
        state.sum_y = sum_y
        state.center = (sum_x / count, sum_y / count)
        return state.center

    def sample(self, device, x, y):
        """增量维护该设备的滚动均值（单次摊还 O(1)）。"""
        state = self._state(device)
        state.count += 1
        state.sum_x += x
        state.sum_y += y
        state.center = (state.sum_x / state.count,
                        state.sum_y / state.count)
        self.work += 1
        return True

    def device_center(self, device):
        """某个设备当前的中心偏移；没有采样时是 (0.0, 0.0)。"""
        state = self._states.get(device)
        if state is None or state.count == 0:
            return (0.0, 0.0)
        return state.center

    def process(self, x, y, device="default"):
        """处理一帧摇杆输入：扣中心、钳制、滞回、死区、曲线。"""
        state = self._state(device)
        cx, cy = state.center
        dx = x - cx
        dy = y - cy
        magnitude = math.hypot(dx, dy)
        if magnitude > 1.0:
            dx /= magnitude
            dy /= magnitude
            magnitude = 1.0

        enter = self.deadzone
        exit_ = self.deadzone * self.release_ratio
        if state.active:
            if magnitude < exit_:
                state.active = False
                state.switches += 1
        else:
            if magnitude > enter:
                state.active = True
                state.switches += 1

        if magnitude <= self.deadzone:
            return (0.0, 0.0)

        radius = (magnitude - self.deadzone) / (1.0 - self.deadzone)
        radius = radius ** self.exponent
        if magnitude:
            scale = radius / magnitude
            ox = dx * scale
            oy = dy * scale
            out_len = math.hypot(ox, oy)
            if out_len > 1.0:
                ox /= out_len
                oy /= out_len
            return (ox, oy)
        return (0.0, 0.0)

    def switches_of(self, device="default"):
        """某个设备的累计状态切换次数。"""
        state = self._states.get(device)
        return state.switches if state is not None else 0

    def work_count(self):
        return self.work

    @property
    def center(self):
        """默认设备的中心偏移（兼容直接读取）。"""
        return self.device_center("default")

    @center.setter
    def center(self, value):
        state = self._state("default")
        state.center = (float(value[0]), float(value[1]))
        state.count = max(state.count, 1)
        state.sum_x = state.center[0] * state.count
        state.sum_y = state.center[1] * state.count

    @property
    def active(self):
        return self._state("default").active

    @active.setter
    def active(self, value):
        self._state("default").active = bool(value)

    @property
    def switches(self):
        """默认设备的累计状态切换次数。"""
        return self.switches_of("default")
