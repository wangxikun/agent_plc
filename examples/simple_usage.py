"""
SimplePLC Generator - 使用示例
Usage Examples for SimplePLC Generator

这个文件展示了如何使用SimplePLCGenerator进行PLC代码生成和验证
"""

import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from src.simple_plc_generator import SimplePLCGenerator


def example_1_led_control():
    """示例1: 简单的LED控制"""
    print("\n" + "=" * 80)
    print("示例1: LED灯控制")
    print("=" * 80)

    # 初始化生成器
    generator = SimplePLCGenerator(
        compiler="rusty",
        enable_verification=True,
        enable_auto_fix=True
    )

    # 自然语言指令
    instruction = """
    创建一个功能块来控制LED灯。
    输入：按钮 (BOOL)
    输出：LED (BOOL)
    逻辑：当按钮按下时，切换LED的状态（开/关）
    """

    # 生成代码
    result = generator.generate(
        instruction=instruction,
        save_to_file=True,
        output_path="led_control.ST"
    )

    print(result)


def example_2_motor_temperature_control():
    """示例2: 温度控制电机（带属性验证）"""
    print("\n" + "=" * 80)
    print("示例2: 温度控制电机")
    print("=" * 80)

    generator = SimplePLCGenerator(
        compiler="rusty",
        enable_verification=True,
        enable_auto_fix=True,
        max_fix_iterations=3
    )

    instruction = """
    创建一个温度控制功能块。
    当温度超过80度时，启动冷却电机。
    当温度低于75度时，关闭冷却电机。
    """

    # 定义需要验证的属性
    properties = [
        {
            "property_description": "当温度大于80度时，电机应该启动",
            "property": {
                "job_req": "pattern",
                "pattern_id": "pattern-implication",
                "pattern_params": {
                    "1": "instance.temperature > 80.0",
                    "2": "instance.motor = TRUE"
                }
            }
        },
        {
            "property_description": "当温度小于75度时，电机应该关闭",
            "property": {
                "job_req": "pattern",
                "pattern_id": "pattern-implication",
                "pattern_params": {
                    "1": "instance.temperature < 75.0",
                    "2": "instance.motor = FALSE"
                }
            }
        }
    ]

    result = generator.generate(
        instruction=instruction,
        properties=properties,
        save_to_file=True,
        output_path="temp_motor_control.ST"
    )

    print(result)


def example_3_timer_based_control():
    """示例3: 基于定时器的控制"""
    print("\n" + "=" * 80)
    print("示例3: 定时器控制")
    print("=" * 80)

    generator = SimplePLCGenerator(
        compiler="rusty",
        enable_verification=True,
        enable_auto_fix=True
    )

    instruction = """
    创建一个定时器功能块。
    当启动信号触发后，延时5秒后激活输出。
    当复位信号触发时，立即关闭输出并复位定时器。
    """

    result = generator.generate(
        instruction=instruction,
        save_to_file=True,
        output_path="timer_control.ST"
    )

    print(result)


def example_4_quick_generate():
    """示例4: 快速生成模式（无验证）"""
    print("\n" + "=" * 80)
    print("示例4: 快速生成（无验证）")
    print("=" * 80)

    # 禁用验证以获得更快的生成速度
    generator = SimplePLCGenerator(
        enable_verification=False
    )

    instruction = "创建一个功能块，控制传送带。当传感器检测到物体时，停止传送带。"

    st_code = generator.quick_generate(instruction)

    print("生成的ST代码:")
    print("=" * 60)
    print(st_code)
    print("=" * 60)


def example_5_fix_existing_code():
    """示例5: 修复已有的错误代码"""
    print("\n" + "=" * 80)
    print("示例5: 修复已有代码")
    print("=" * 80)

    generator = SimplePLCGenerator(
        compiler="rusty",
        enable_verification=True,
        enable_auto_fix=True
    )

    # 有语法错误的ST代码（缺少分号）
    buggy_code = """
FUNCTION_BLOCK PressureControl
VAR_INPUT
    pressure : REAL
END_VAR

VAR_OUTPUT
    valve : BOOL
END_VAR

    IF pressure > 100.0 THEN
        valve := TRUE
    ELSE
        valve := FALSE
    END_IF

END_FUNCTION_BLOCK
"""

    print("原始代码（有错误）:")
    print(buggy_code)
    print("\n修复中...")

    result = generator.fix_existing_code(
        st_code=buggy_code,
        original_instruction="压力控制：当压力超过100时，打开阀门"
    )

    print(result)


def example_6_cotton_candy_machine():
    """示例6: 棉花糖机控制（来自benchmark数据集）"""
    print("\n" + "=" * 80)
    print("示例6: 棉花糖机控制")
    print("=" * 80)

    generator = SimplePLCGenerator(
        compiler="rusty",
        enable_verification=True,
        enable_auto_fix=True
    )

    instruction = """
    Create a PLC function block to manage an automated cotton candy machine,
    controlling sugar feeding and motor spinning speed.

    Inputs:
    - SugarLevel (REAL): Current sugar level
    - SpinningSpeed (INT): Desired spinning speed

    Outputs:
    - SugarFeeder (BOOL): Control sugar feeding mechanism
    - MotorSpeed (INT): Manage spinning motor speed

    Logic:
    - Activate sugar feeder when sugar level is below 10.0 units
    - Deactivate sugar feeder when level is at or above 10.0
    - Set motor speed to input spinning speed if positive
    - Set motor speed to 0 if input speed is 0 or negative
    """

    properties = [
        {
            "property_description": "Sugar feeder activated when sugar level < 10.0",
            "property": {
                "job_req": "pattern",
                "pattern_id": "pattern-implication",
                "pattern_params": {
                    "0": "instance.SugarLevel < 10.0",
                    "1": "instance.SugarFeeder = TRUE"
                }
            }
        },
        {
            "property_description": "Sugar feeder deactivated when sugar level >= 10.0",
            "property": {
                "job_req": "pattern",
                "pattern_id": "pattern-implication",
                "pattern_params": {
                    "0": "instance.SugarLevel >= 10.0",
                    "1": "instance.SugarFeeder = FALSE"
                }
            }
        },
        {
            "property_description": "Motor speed set to input when spinning speed > 0",
            "property": {
                "job_req": "pattern",
                "pattern_id": "pattern-implication",
                "pattern_params": {
                    "0": "instance.SpinningSpeed > 0",
                    "1": "instance.MotorSpeed = instance.SpinningSpeed"
                }
            }
        },
        {
            "property_description": "Motor speed set to 0 when spinning speed <= 0",
            "property": {
                "job_req": "pattern",
                "pattern_id": "pattern-implication",
                "pattern_params": {
                    "0": "instance.SpinningSpeed <= 0",
                    "1": "instance.MotorSpeed = 0"
                }
            }
        }
    ]

    result = generator.generate(
        instruction=instruction,
        properties=properties,
        save_to_file=True,
        output_path="cotton_candy_machine.ST"
    )

    print(result)


def main():
    """运行所有示例"""
    print("\n" + "#" * 80)
    print("# SimplePLCGenerator 使用示例集")
    print("# SimplePLCGenerator Usage Examples")
    print("#" * 80)

    examples = [
        ("LED控制", example_1_led_control),
        ("温度控制电机", example_2_motor_temperature_control),
        ("定时器控制", example_3_timer_based_control),
        ("快速生成", example_4_quick_generate),
        ("修复错误代码", example_5_fix_existing_code),
        ("棉花糖机控制", example_6_cotton_candy_machine)
    ]

    print("\n可用示例:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\n选择要运行的示例 (1-{}, 0=全部运行): ".format(len(examples)), end="")

    try:
        choice = int(input())

        if choice == 0:
            # 运行所有示例
            for name, func in examples:
                print(f"\n\n{'#' * 80}")
                print(f"# 运行示例: {name}")
                print(f"{'#' * 80}")
                func()
        elif 1 <= choice <= len(examples):
            # 运行选中的示例
            name, func = examples[choice - 1]
            print(f"\n\n{'#' * 80}")
            print(f"# 运行示例: {name}")
            print(f"{'#' * 80}")
            func()
        else:
            print("无效的选择")

    except ValueError:
        print("输入无效，运行所有示例...")
        for name, func in examples:
            try:
                print(f"\n\n{'#' * 80}")
                print(f"# 运行示例: {name}")
                print(f"{'#' * 80}")
                func()
            except Exception as e:
                print(f"示例失败: {str(e)}")
                continue

    print("\n" + "#" * 80)
    print("# 所有示例运行完成")
    print("#" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n错误: {str(e)}")
        print("\n请确保:")
        print("  1. config.py已正确配置API密钥")
        print("  2. 编译器(rusty或matiec)已安装并可访问")
        print("  3. PLCverif工具已安装（可选，用于属性验证）")
