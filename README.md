# stick-calibration

摇杆处理：多设备校准台账、径向死区、响应曲线、死区滞回与输出钳制。
只用 Python 标准库。

```
python3 -m sticks.cli --sample radial
python3 -m sticks.cli --sample curve
python3 -m sticks.cli --sample drift
python3 -m sticks.cli --sample hysteresis
python3 -m sticks.cli --sample clamp
python3 -m sticks.cli --sample devices
python3 -m sticks.cli --sample mix
python3 -m sticks.cli --sample work
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **多设备台账**：每个设备各自维护中心偏移、激活状态与切换计数；
  处理一个设备不会改动另一个设备的任何状态。
- **校准**：`calibrate(samples, device)` 用一批采样直接写入该设备的中心偏移；
  `sample(device, x, y)` 增量维护该设备的滚动均值；`device_center(device)`
  返回该设备当前均值，没有采样时是 `(0.0, 0.0)`。
- **中心扣除**：`process` 先把该设备的中心偏移从输入里减掉再往下算。
- **径向死区**：先算 `hypot(x, y)`，长度不超过进入阈值时输出 `(0, 0)`；
  超过时把长度从 `[deadzone, 1]` 线性映射到 `[0, 1]`，方向保持不变。
- **响应曲线**：映射后的半径取 `exponent` 次幂（`r ** exponent`），
  保证 0 进 0 出、1 进 1 出、单调不减。
- **滞回**：进入阈值是 `deadzone`，退出阈值是 `deadzone * release_ratio`；
  已激活时要小于退出阈值才回到静止，静止时要达到进入阈值才激活；
  状态每切换一次该设备的计数加一。
- **钳制**：输入长度超过 1 先按单位长度截断，输出向量长度永远不超过 1。
- **代价**：`sample` 单次摊还 O(1)，`work_count` 不随采样次数线性增长；
  `process` 每帧 O(1) 且不随设备数增长。
- **规模**：1 万个设备、每设备 10 万次采样与处理，单次摊还 O(1)，
  内存 O(设备数)。

## 输出契约（不改格式）

```
len=..
switches=..
pad1=.. pad2=..
center=..
work=..
```

## 目录

```
sticks/core.py   多设备校准、死区、曲线、滞回与钳制
sticks/cli.py    命令行入口
tests/           unittest 用例
```
