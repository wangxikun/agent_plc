#!/usr/bin/env python3
"""温度控制系统测试 - OpenPLC默认I/O映射"""

from pyModbusTCP.client import ModbusClient
import time

client = ModbusClient(host="localhost", port=502, timeout=5)

def connect():
    if client.open():
        print("✅ 成功连接到OpenPLC")
        return True
    else:
        print("❌ 连接失败")
        print("请确保:")
        print("  1. OpenPLC正在运行")
        print("  2. PLC状态为'Running'")
        print("  3. 已编译 openplc_temp_simple.st")
        return False

def write_inputs(temp, humidity, manual):
    """
    写入输入变量
    OpenPLC默认映射:
    - 前8个INT变量 -> %IW0-%IW7 (Modbus Input Registers 0-7)
    - 前8个BOOL变量 -> %IX0.0-%IX0.7 (Modbus Discrete Inputs 0-7)

    我们的程序变量顺序:
    1. temperature (INT) -> %IW0 -> Input Register 0
    2. humidity (INT)    -> %IW1 -> Input Register 1
    3. manual_mode (BOOL) -> %IX0.0 -> Discrete Input 0
    """
    temp_int = int(temp * 100)
    hum_int = int(humidity * 100)

    # 写入Input Registers (需要用Holding Registers模拟)
    # OpenPLC将程序的输入映射到 1024+ 的保持寄存器
    client.write_single_register(1024, temp_int)
    client.write_single_register(1025, hum_int)

    # 写入Discrete Input (用Coil模拟)
    client.write_single_coil(1024, manual)

def read_outputs():
    """
    读取输出变量
    输出顺序:
    1. heater (BOOL) -> %QX0.0 -> Coil 0
    2. cooler (BOOL) -> %QX0.1 -> Coil 1
    3. fan (BOOL)    -> %QX0.2 -> Coil 2
    4. alarm (BOOL)  -> %QX0.3 -> Coil 3
    """
    result = client.read_coils(0, 4)
    if result:
        return {
            'heater': result[0],
            'cooler': result[1],
            'fan': result[2],
            'alarm': result[3]
        }
    return None

def test_scenarios():
    print("\n" + "=" * 80)
    print("🧪 温度控制系统测试")
    print("=" * 80)

    # 测试1: 低温场景
    print("\n测试1: 低温场景 (15°C)")
    print("-" * 80)
    write_inputs(15.0, 50.0, False)
    time.sleep(0.2)

    outputs = read_outputs()
    if outputs:
        print(f"温度: 15°C")
        print(f"加热器: {'🟢 开' if outputs['heater'] else '⚫ 关'}")
        print(f"冷却器: {'🟢 开' if outputs['cooler'] else '⚫ 关'}")
        print(f"预期: 加热器开，冷却器关")
        result = outputs['heater'] and not outputs['cooler']
        print(f"结果: {'✅ 正确' if result else '❌ 错误'}")

    # 测试2: 高温场景
    print("\n测试2: 高温场景 (30°C)")
    print("-" * 80)
    write_inputs(30.0, 50.0, False)
    time.sleep(0.2)

    outputs = read_outputs()
    if outputs:
        print(f"温度: 30°C")
        print(f"加热器: {'🟢 开' if outputs['heater'] else '⚫ 关'}")
        print(f"冷却器: {'🟢 开' if outputs['cooler'] else '⚫ 关'}")
        print(f"预期: 加热器关，冷却器开")
        result = not outputs['heater'] and outputs['cooler']
        print(f"结果: {'✅ 正确' if result else '❌ 错误'}")

    # 测试3: 舒适温度
    print("\n测试3: 舒适温度 (22°C)")
    print("-" * 80)
    write_inputs(22.0, 50.0, False)
    time.sleep(0.2)

    outputs = read_outputs()
    if outputs:
        print(f"温度: 22°C")
        print(f"加热器: {'🟢 开' if outputs['heater'] else '⚫ 关'}")
        print(f"冷却器: {'🟢 开' if outputs['cooler'] else '⚫ 关'}")
        print(f"预期: 两者都关")
        result = not outputs['heater'] and not outputs['cooler']
        print(f"结果: {'✅ 正确' if result else '❌ 错误'}")

    # 测试4: 高湿度
    print("\n测试4: 高湿度场景 (湿度80%)")
    print("-" * 80)
    write_inputs(22.0, 80.0, False)
    time.sleep(0.2)

    outputs = read_outputs()
    if outputs:
        print(f"湿度: 80%")
        print(f"排风扇: {'🟢 开' if outputs['fan'] else '⚫ 关'}")
        print(f"预期: 排风扇开")
        result = outputs['fan']
        print(f"结果: {'✅ 正确' if result else '❌ 错误'}")

    # 测试5: 异常温度报警
    print("\n测试5: 异常温度报警 (2°C)")
    print("-" * 80)
    write_inputs(2.0, 50.0, False)
    time.sleep(0.2)

    outputs = read_outputs()
    if outputs:
        print(f"温度: 2°C")
        print(f"报警: {'🔴 开' if outputs['alarm'] else '⚫ 关'}")
        print(f"预期: 报警开启")
        result = outputs['alarm']
        print(f"结果: {'✅ 正确' if result else '❌ 错误'}")

    # 测试6: 手动模式
    print("\n测试6: 手动模式")
    print("-" * 80)
    write_inputs(15.0, 50.0, True)  # 启用手动模式
    time.sleep(0.2)

    outputs = read_outputs()
    if outputs:
        print(f"温度: 15°C (手动模式)")
        print(f"加热器: {'🟢 开' if outputs['heater'] else '⚫ 关'}")
        print(f"冷却器: {'🟢 开' if outputs['cooler'] else '⚫ 关'}")
        print(f"风扇: {'🟢 开' if outputs['fan'] else '⚫ 关'}")
        print(f"报警: {'🟢 开' if outputs['alarm'] else '⚫ 关'}")
        print(f"预期: 手动模式下所有输出关闭")
        all_off = not (outputs['heater'] or outputs['cooler'] or outputs['fan'] or outputs['alarm'])
        print(f"结果: {'✅ 正确' if all_off else '❌ 错误'}")

    print("\n" + "=" * 80)
    print("✅ 测试完成!")
    print("=" * 80)

if __name__ == "__main__":
    try:
        import pyModbusTCP
    except ImportError:
        print("❌ 请先安装: pip3 install --break-system-packages pyModbusTCP")
        exit(1)

    if connect():
        print("\n⚠️  请确保OpenPLC中已:")
        print("   1. 选择 openplc_temp_simple.st")
        print("   2. 编译成功")
        print("   3. 启动PLC\n")
        input("按Enter开始测试...")
        test_scenarios()

    client.close()
