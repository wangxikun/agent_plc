#!/usr/bin/env python3
"""
真实示例：简单电梯控制系统
从自然语言 → ST代码 → OpenPLC部署 → Python测试

本脚本会真实调用：
1. SimplePLCGenerator - 代码生成
2. CodeGenerator - LLM调用
3. Verifier - 编译验证
4. AutoFixer - 自动修复（如需要）
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

from src.simple_plc_generator import SimplePLCGenerator
from datetime import datetime
import os
import re

print("=" * 80)
print("🏢 真实示例：简单电梯控制系统")
print("=" * 80)
print()

# ============================================================
# 步骤1: 用自然语言描述需求
# ============================================================
print("【步骤1】定义控制需求（自然语言）")
print("-" * 80)

natural_language_requirement = """
创建一个简单的2层电梯控制系统。

输入变量:
- call_btn_1 : BOOL  (1楼呼叫按钮)
- call_btn_2 : BOOL  (2楼呼叫按钮)
- at_floor_1 : BOOL  (1楼限位开关，电梯到达1楼时为TRUE)
- at_floor_2 : BOOL  (2楼限位开关，电梯到达2楼时为TRUE)
- door_closed : BOOL (门关闭限位，门完全关闭时为TRUE)
- emergency_stop : BOOL (急停按钮)

输出变量:
- motor_up : BOOL    (电机上行控制)
- motor_down : BOOL  (电机下行控制)
- door_open : BOOL   (开门控制)
- alarm : BOOL       (报警指示灯)

控制逻辑:
1. 使用CASE语句实现4个状态: IDLE(空闲), MOVING_UP(上行), MOVING_DOWN(下行), DOOR_OPEN_STATE(开门)
2. IDLE状态: 检测呼叫按钮，决定上行还是下行
3. MOVING_UP状态: 启动上行电机，到达2楼后停止并开门
4. MOVING_DOWN状态: 启动下行电机，到达1楼后停止并开门
5. DOOR_OPEN_STATE状态: 保持门打开3秒（使用TON定时器），然后返回IDLE
6. 安全规则:
   - 急停按钮按下时，所有运动停止，报警开启
   - 门未关闭时，电机不能启动
   - 上行和下行电机不能同时为TRUE

请使用状态机结构，INT类型存储当前状态，使用TON定时器控制开门时间。
"""

print(natural_language_requirement)
print()

# ============================================================
# 步骤2: 定义形式化验证属性
# ============================================================
print("【步骤2】定义形式化验证属性")
print("-" * 80)

properties = [
    {
        "property_description": "急停时所有电机必须停止",
        "property": {
            "job_req": "pattern",
            "pattern_id": "pattern-implication",
            "pattern_params": {
                "1": "instance.emergency_stop = TRUE",
                "2": "instance.motor_up = FALSE AND instance.motor_down = FALSE"
            }
        }
    },
    {
        "property_description": "上行和下行电机不能同时运行",
        "property": {
            "job_req": "pattern",
            "pattern_id": "pattern-forbidden",
            "pattern_params": {
                "1": "instance.motor_up = TRUE AND instance.motor_down = TRUE"
            }
        }
    },
    {
        "property_description": "门未关闭时电机不能启动",
        "property": {
            "job_req": "pattern",
            "pattern_id": "pattern-implication",
            "pattern_params": {
                "1": "instance.door_closed = FALSE",
                "2": "instance.motor_up = FALSE AND instance.motor_down = FALSE"
            }
        }
    }
]

for i, prop in enumerate(properties, 1):
    print(f"{i}. {prop['property_description']}")
print()

# ============================================================
# 步骤3: 真实调用SimplePLCGenerator生成代码
# ============================================================
print("【步骤3】真实调用 SimplePLCGenerator（LLM生成代码）")
print("-" * 80)
print("⏳ 正在调用GPT-4生成ST代码...")
print("   (这将发起真实的API请求，请稍候...)")
print()

# 初始化生成器
generator = SimplePLCGenerator(
    compiler="rusty",           # 使用Rusty编译器验证
    enable_verification=True,   # 启用编译验证
    enable_auto_fix=True,       # 启用自动修复
    max_fix_iterations=3        # 最多3次修复迭代
)

# 真实调用生成
start_time = datetime.now()
result = generator.generate(
    instruction=natural_language_requirement,
    properties=properties,
    save_to_file=False  # 暂不保存，稍后转换格式
)
end_time = datetime.now()

elapsed = (end_time - start_time).total_seconds()

print()
print(f"⏱️  生成耗时: {elapsed:.2f}秒")
print()

# 检查生成结果
if not result.success:
    print("❌ 代码生成失败!")
    print(f"错误信息: {result.error_message}")
    sys.exit(1)

print(f"✅ 代码生成成功! (迭代{result.iterations}次)")
print()

# 显示生成的代码
print("【生成的FUNCTION_BLOCK代码】")
print("-" * 80)
print(result.st_code)
print("-" * 80)
print()

# ============================================================
# 步骤4: 转换为OpenPLC格式
# ============================================================
print("【步骤4】转换为OpenPLC兼容的PROGRAM格式")
print("-" * 80)

def convert_to_openplc_format(st_code, program_name="ElevatorControl"):
    """转换FUNCTION_BLOCK为OpenPLC的PROGRAM格式"""

    # 提取变量声明
    var_input_match = re.search(r'VAR_INPUT(.*?)END_VAR', st_code, re.DOTALL)
    var_input = var_input_match.group(1).strip() if var_input_match else ""

    var_output_match = re.search(r'VAR_OUTPUT(.*?)END_VAR', st_code, re.DOTALL)
    var_output = var_output_match.group(1).strip() if var_output_match else ""

    var_match = re.search(r'(?<!VAR_INPUT\s)(?<!VAR_OUTPUT\s)VAR\s(.*?)END_VAR', st_code, re.DOTALL)
    var_internal = var_match.group(1).strip() if var_match else ""

    # 提取主逻辑
    logic_match = re.search(r'END_VAR\s*(.*?)\s*END_FUNCTION_BLOCK', st_code, re.DOTALL)
    logic = logic_match.group(1).strip() if logic_match else ""

    # 构建OpenPLC格式
    openplc_code = f"""(* ================================================================
   OpenPLC Program: {program_name}
   Generated by Agents4PLC from natural language
   Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

   Description: 简单2层电梯控制系统
   ================================================================ *)

PROGRAM {program_name}
VAR
    (* 输入变量 - 映射到OpenPLC物理输入 *)
{var_input}

    (* 输出变量 - 映射到OpenPLC物理输出 *)
{var_output}

    (* 内部变量 *)
{var_internal}
END_VAR

(* ================================================================
   主控制逻辑
   ================================================================ *)

{logic}

END_PROGRAM
"""
    return openplc_code

openplc_code = convert_to_openplc_format(result.st_code)

# 保存为.st文件
output_filename = "openplc_elevator_simple.st"
with open(output_filename, 'w', encoding='utf-8') as f:
    f.write(openplc_code)

print(f"✅ 已转换并保存为: {output_filename}")
print()
print("【OpenPLC格式代码】")
print("-" * 80)
print(openplc_code[:1000] + "..." if len(openplc_code) > 1000 else openplc_code)
print("-" * 80)
print()

# ============================================================
# 步骤5: 创建Python测试脚本
# ============================================================
print("【步骤5】创建Python监控测试脚本")
print("-" * 80)

test_script = '''#!/usr/bin/env python3
"""
电梯控制系统测试脚本
通过Modbus TCP与OpenPLC通信，测试电梯控制逻辑
"""

from pyModbusTCP.client import ModbusClient
import time

class ElevatorSimulator:
    def __init__(self, host="localhost", port=502):
        self.client = ModbusClient(host=host, port=port, timeout=5)

    def connect(self):
        """连接到OpenPLC"""
        if self.client.open():
            print("✅ 成功连接到OpenPLC (Modbus TCP)")
            return True
        else:
            print("❌ 连接失败，请确保:")
            print("   1. OpenPLC正在运行")
            print("   2. PLC状态为'Running'")
            print("   3. 程序已上传并编译")
            return False

    def write_inputs(self, call_btn_1=False, call_btn_2=False,
                     at_floor_1=False, at_floor_2=False,
                     door_closed=True, emergency_stop=False):
        """写入输入变量（模拟按钮和传感器）"""
        # Modbus Coil地址映射（根据OpenPLC配置）
        # 假设输入从地址0开始
        self.client.write_single_coil(0, call_btn_1)
        self.client.write_single_coil(1, call_btn_2)
        self.client.write_single_coil(2, at_floor_1)
        self.client.write_single_coil(3, at_floor_2)
        self.client.write_single_coil(4, door_closed)
        self.client.write_single_coil(5, emergency_stop)

    def read_outputs(self):
        """读取输出变量（电机和门控制）"""
        # 假设输出从地址100开始
        coils = self.client.read_coils(100, 4)
        if coils:
            return {
                'motor_up': coils[0],
                'motor_down': coils[1],
                'door_open': coils[2],
                'alarm': coils[3]
            }
        return None

    def print_status(self, outputs):
        """打印状态"""
        if outputs:
            print(f"  电机上行: {'🟢 开' if outputs['motor_up'] else '⚫ 关'} | "
                  f"电机下行: {'🟢 开' if outputs['motor_down'] else '⚫ 关'} | "
                  f"开门: {'🟢 开' if outputs['door_open'] else '⚫ 关'} | "
                  f"报警: {'🔴 是' if outputs['alarm'] else '⚫ 否'}")

    def test_scenario(self):
        """运行测试场景"""

        print("\\n" + "=" * 80)
        print("🧪 电梯控制系统测试")
        print("=" * 80)

        # 测试1: 从1楼呼叫到2楼
        print("\\n测试1: 电梯在1楼，按下2楼呼叫按钮")
        print("-" * 80)
        self.write_inputs(
            call_btn_1=False,
            call_btn_2=True,   # 按下2楼按钮
            at_floor_1=True,   # 当前在1楼
            at_floor_2=False,
            door_closed=True,
            emergency_stop=False
        )
        time.sleep(0.5)
        outputs = self.read_outputs()
        self.print_status(outputs)
        expected = outputs['motor_up'] and not outputs['motor_down']
        print(f"  预期: 电机上行启动")
        print(f"  结果: {'✅ 正确' if expected else '❌ 错误'}")

        # 模拟到达2楼
        print("\\n  模拟电梯上行到达2楼...")
        time.sleep(1)
        self.write_inputs(
            call_btn_1=False,
            call_btn_2=False,
            at_floor_1=False,
            at_floor_2=True,   # 到达2楼
            door_closed=True,
            emergency_stop=False
        )
        time.sleep(0.5)
        outputs = self.read_outputs()
        self.print_status(outputs)
        expected = not outputs['motor_up'] and outputs['door_open']
        print(f"  预期: 电机停止，门打开")
        print(f"  结果: {'✅ 正确' if expected else '❌ 错误'}")

        # 测试2: 从2楼下到1楼
        print("\\n测试2: 电梯在2楼，按下1楼呼叫按钮")
        print("-" * 80)
        time.sleep(3)  # 等待门关闭
        self.write_inputs(
            call_btn_1=True,   # 按下1楼按钮
            call_btn_2=False,
            at_floor_1=False,
            at_floor_2=True,   # 当前在2楼
            door_closed=True,
            emergency_stop=False
        )
        time.sleep(0.5)
        outputs = self.read_outputs()
        self.print_status(outputs)
        expected = outputs['motor_down'] and not outputs['motor_up']
        print(f"  预期: 电机下行启动")
        print(f"  结果: {'✅ 正确' if expected else '❌ 错误'}")

        # 测试3: 急停测试
        print("\\n测试3: 运行中按下急停按钮")
        print("-" * 80)
        self.write_inputs(
            call_btn_1=False,
            call_btn_2=False,
            at_floor_1=False,
            at_floor_2=False,  # 楼层之间
            door_closed=True,
            emergency_stop=True  # 按下急停
        )
        time.sleep(0.5)
        outputs = self.read_outputs()
        self.print_status(outputs)
        expected = not outputs['motor_up'] and not outputs['motor_down'] and outputs['alarm']
        print(f"  预期: 所有电机停止，报警开启")
        print(f"  结果: {'✅ 正确' if expected else '❌ 错误'}")

        # 测试4: 门未关闭时不能启动
        print("\\n测试4: 门未关闭时尝试启动")
        print("-" * 80)
        self.write_inputs(
            call_btn_1=False,
            call_btn_2=True,   # 按下2楼按钮
            at_floor_1=True,
            at_floor_2=False,
            door_closed=False,  # 门未关闭
            emergency_stop=False
        )
        time.sleep(0.5)
        outputs = self.read_outputs()
        self.print_status(outputs)
        expected = not outputs['motor_up'] and not outputs['motor_down']
        print(f"  预期: 电机不启动（安全互锁）")
        print(f"  结果: {'✅ 正确' if expected else '❌ 错误'}")

        print("\\n" + "=" * 80)
        print("✅ 测试完成!")
        print("=" * 80)

    def close(self):
        """关闭连接"""
        self.client.close()

if __name__ == "__main__":
    try:
        # 检查依赖
        print("📦 检查依赖: pyModbusTCP")
        try:
            import pyModbusTCP
            print("✅ pyModbusTCP 已安装\\n")
        except ImportError:
            print("❌ 请先安装: pip install pyModbusTCP")
            exit(1)

        # 运行测试
        sim = ElevatorSimulator()
        if sim.connect():
            print("\\n⚠️  注意: 请确保已在OpenPLC中:")
            print("   1. 上传 openplc_elevator_simple.st")
            print("   2. 编译成功")
            print("   3. 启动PLC (状态为Running)")
            print("\\n按Enter键开始测试...")
            input()

            sim.test_scenario()

        sim.close()

    except KeyboardInterrupt:
        print("\\n\\n⚠️  用户中断")
    except Exception as e:
        print(f"\\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
'''

test_filename = "test_elevator_openplc.py"
with open(test_filename, 'w', encoding='utf-8') as f:
    f.write(test_script)

os.chmod(test_filename, 0o755)

print(f"✅ 已创建测试脚本: {test_filename}")
print()

# ============================================================
# 步骤6: 生成使用说明
# ============================================================
print("【步骤6】生成使用说明")
print("-" * 80)

readme = f"""# 🏢 简单电梯控制系统 - OpenPLC测试

## 📋 生成信息

- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **LLM模型**: GPT-4
- **生成耗时**: {elapsed:.2f}秒
- **迭代次数**: {result.iterations}次
- **编译验证**: {'✅ 通过' if result.success else '❌ 失败'}

## 📁 生成的文件

1. `{output_filename}` - OpenPLC程序（上传到OpenPLC）
2. `{test_filename}` - Python测试脚本
3. `ELEVATOR_DEMO_README.md` - 本说明文件

## 🚀 快速开始

### 步骤1: 确保OpenPLC正在运行

```bash
cd OpenPLC_v3/webserver
sudo node server.js
```

访问: http://localhost:8080

### 步骤2: 上传程序到OpenPLC

1. 登录OpenPLC (openplc/openplc)
2. 点击 "Programs"
3. 选择文件: `{os.path.abspath(output_filename)}`
4. 点击 "Upload Program"
5. 点击 "Compile"
6. 返回 "Dashboard"，点击 "Start PLC"

### 步骤3: 运行测试

```bash
pip install pyModbusTCP
python3 {test_filename}
```

## 🎯 控制逻辑说明

### 输入变量
- call_btn_1: 1楼呼叫按钮
- call_btn_2: 2楼呼叫按钮
- at_floor_1: 1楼限位开关
- at_floor_2: 2楼限位开关
- door_closed: 门关闭检测
- emergency_stop: 急停按钮

### 输出变量
- motor_up: 上行电机
- motor_down: 下行电机
- door_open: 开门控制
- alarm: 报警灯

### 状态机
1. **IDLE (0)**: 空闲，等待呼叫
2. **MOVING_UP (1)**: 上行中
3. **MOVING_DOWN (2)**: 下行中
4. **DOOR_OPEN_STATE (3)**: 开门保持

### 安全规则
✅ 急停时所有电机停止
✅ 上下行电机互锁
✅ 门未关闭时电机不启动

## 🧪 测试场景

运行测试脚本会执行以下场景：
1. ✅ 从1楼呼叫到2楼（上行测试）
2. ✅ 从2楼呼叫到1楼（下行测试）
3. ✅ 急停功能测试
4. ✅ 门未关闭安全互锁测试

## 📊 预期结果

```
🧪 电梯控制系统测试
================================================================================

测试1: 电梯在1楼，按下2楼呼叫按钮
--------------------------------------------------------------------------------
  电机上行: 🟢 开 | 电机下行: ⚫ 关 | 开门: ⚫ 关 | 报警: ⚫ 否
  预期: 电机上行启动
  结果: ✅ 正确

  模拟电梯上行到达2楼...
  电机上行: ⚫ 关 | 电机下行: ⚫ 关 | 开门: 🟢 开 | 报警: ⚫ 否
  预期: 电机停止，门打开
  结果: ✅ 正确

... (更多测试)

✅ 测试完成!
```

## 🔧 故障排除

### 问题1: 连接失败
确保：
- OpenPLC正在运行
- PLC状态为"Running"（绿色）
- 防火墙允许502端口

### 问题2: 编译失败
检查ST代码语法，或重新生成代码

### 问题3: 测试结果不符合预期
- 检查OpenPLC的I/O地址映射
- 查看OpenPLC监控页面的变量值
- 调整测试脚本中的Modbus地址

## 📚 相关文档

- OpenPLC官方文档: https://www.openplcproject.com/reference
- Agents4PLC项目: /Users/scott/pythonrepo/Agents4PLC_release/
- 完整教程: OPENPLC_QUICKSTART.md

---

**生成工具**: Agents4PLC
**论文**: https://arxiv.org/abs/2410.14209
"""

readme_filename = "ELEVATOR_DEMO_README.md"
with open(readme_filename, 'w', encoding='utf-8') as f:
    f.write(readme)

print(f"✅ 已创建说明文档: {readme_filename}")
print()

# ============================================================
# 完成总结
# ============================================================
print("=" * 80)
print("🎉 真实示例生成完成!")
print("=" * 80)
print()

print("📊 生成统计:")
print(f"  - LLM调用耗时: {elapsed:.2f}秒")
print(f"  - 自动修复迭代: {result.iterations}次")
print(f"  - 编译验证: {'✅ 通过' if result.success else '❌ 失败'}")
print(f"  - 代码行数: {len(result.st_code.splitlines())}行")
print()

print("📁 生成的文件:")
print(f"  1. {output_filename} - OpenPLC程序（{os.path.getsize(output_filename)} bytes）")
print(f"  2. {test_filename} - Python测试脚本")
print(f"  3. {readme_filename} - 使用说明")
print()

print("🚀 下一步操作:")
print()
print("方式A - 自动化部署（如果OpenPLC已安装）:")
print("  1. cd OpenPLC_v3/webserver && sudo node server.js")
print("  2. 访问 http://localhost:8080")
print(f"  3. 上传 {output_filename} 并编译")
print("  4. 启动PLC")
print(f"  5. python3 {test_filename}")
print()

print("方式B - 使用一键脚本:")
print("  ./quick_start.sh")
print(f"  然后手动上传 {output_filename}")
print()

print("📖 详细说明:")
print(f"  cat {readme_filename}")
print()

print("=" * 80)
print("✅ 本脚本真实调用了以下模块:")
print("  ✓ SimplePLCGenerator")
print("  ✓ CodeGenerator (GPT-4 API)")
print("  ✓ Verifier (Rusty编译器)")
print("  ✓ AutoFixer (如需要)")
print("=" * 80)
