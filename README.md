# stick-calibration

摇杆处理：中心偏移校准、径向死区、响应曲线、死区滞回与输出钳制。
只用 Python 标准库。

```
python3 -m sticks.cli --sample radial
python3 -m sticks.cli --sample curve
python3 -m sticks.cli --sample drift
python3 -m sticks.cli --sample hysteresis
python3 -m sticks.cli --sample clamp
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **校准**：`calibrate(samples)` 把样本均值记成中心偏移；`process` 先把偏移从
  输入里减掉再往下算。
- **径向死区**：先算 `r = hypot(x, y)`，`r` 不超过进入阈值 `deadzone` 时输出
  `(0, 0)`；超过时把 `r` 从 `[deadzone, 1]` 线性映射到 `[0, 1]`，方向保持不变。
  死区按长度判断，不是每个轴各自判断。
- **响应曲线**：映射后的半径取 `exponent` 次幂（`r ** exponent`），
  保证 0 进 0 出、1 进 1 出、单调不减。
- **滞回**：进入阈值是 `deadzone`，退出阈值是 `deadzone * release_ratio`；
  已经在激活状态时，只有 `r` 小于退出阈值才回到静止；静止状态下要 `r`
  达到进入阈值才激活。状态每切换一次 `switches` 加一。
- **钳制**：输入长度超过 1 先按单位长度截断；输出向量长度永远不超过 1。
- **不变量**：静止状态输出恒为 `(0, 0)`；同一串输入重复处理结果相同；
  死区内的输入不会让 `switches` 变化。
- **规模**：每帧处理 O(1)，10 万帧单遍跑完，内存 O(1)。

## 输出契约（不改格式）

```
len=..
switches=..
```

## 目录

```
sticks/core.py   校准、死区、曲线、滞回与钳制
sticks/cli.py    命令行入口
tests/           unittest 用例
```
