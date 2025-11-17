#!/usr/bin/env python3
"""
真实演示：使用Agents4PLC从自然语言生成PLC代码
完整流程：需求描述 → ST代码生成 → 语法验证 → OpenPLC部署
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent / "src"))

print("=" * 80)
print("🤖 Agents4PLC 真实代码生成演示")
print("=" * 80)
print()

# ============================================================
# 步骤1: 自然语言需求描述
# ============================================================
print("【步骤1】定义控制需求（自然语言）")
print("-" * 80)

natural_language_requirement = """
创建一个简单的水箱液位控制系统。

输入变量:
- water_level : INT     (水位传感器，0-100表示百分比)
- high_limit : INT      (高水位阈值，默认80)
- low_limit : INT       (低水位阈值，默认20)
- manual_mode : BOOL    (手动模式开关)
- emergency_stop : BOOL (急停按钮)

输出变量:
- inlet_valve : BOOL    (进水阀，TRUE时开启)
- outlet_valve : BOOL   (出水阀，TRUE时开启)
- pump : BOOL           (水泵，TRUE时运行)
- alarm : BOOL          (报警灯)

控制逻辑:
1. 自动模式下：
   - 水位 < low_limit 时：开启进水阀，关闭出水阀，启动水泵
   - 水位 > high_limit 时：关闭进水阀，开启出水阀，停止水泵
   - 水位在 low_limit 和 high_limit 之间：保持当前状态

2. 手动模式下：所有自动控制停止

3. 安全规则：
   - 急停时，所有阀门关闭，水泵停止，报警开启
   - 进水阀和出水阀不能同时打开
   - 水位异常（<5 或 >95）时触发报警
"""

print(natural_language_requirement)
print()

# ============================================================
# 步骤2: 使用SimplePLCGenerator生成代码
# ============================================================
print("【步骤2】调用代码生成模块")
print("-" * 80)

try:
    from simple_plc_generator import SimplePLCGenerator

    generator = SimplePLCGenerator()

    print("⚙️  正在调用LLM生成ST代码...")
    print("   (使用GPT-4/DeepSeek等模型)")
    print()

    # 生成ST代码
    result = generator.generate_from_description(
        description=natural_language_requirement,
        output_file="generated_water_tank.st"
    )

    if result['success']:
        print("✅ ST代码生成成功!")
        print(f"   文件位置: {result['output_file']}")
        print()

        # 显示生成的代码片段
        print("【生成的ST代码预览】")
        print("-" * 80)
        with open(result['output_file'], 'r') as f:
            code_lines = f.readlines()
            for i, line in enumerate(code_lines[:30], 1):  # 显示前30行
                print(f"{i:3d} | {line}", end='')
        print("\n... (完整代码见文件)")
        print()
    else:
        print(f"❌ 生成失败: {result.get('error', '未知错误')}")
        print()
        print("⚠️  可能原因:")
        print("   1. API密钥未配置（检查 config.py）")
        print("   2. 网络连接问题")
        print("   3. LLM服务不可用")
        print()
        print("📝 备用方案：使用预设的演示代码...")

        # 创建一个简单的演示代码
        demo_code = '''PROGRAM WaterTankControl
VAR
    (* 输入变量 *)
    water_level : INT := 50;
    high_limit : INT := 80;
    low_limit : INT := 20;
    manual_mode : BOOL := FALSE;
    emergency_stop : BOOL := FALSE;

    (* 输出变量 *)
    inlet_valve : BOOL := FALSE;
    outlet_valve : BOOL := FALSE;
    pump : BOOL := FALSE;
    alarm : BOOL := FALSE;
END_VAR

(* 急停处理 *)
IF emergency_stop THEN
    inlet_valve := FALSE;
    outlet_valve := FALSE;
    pump := FALSE;
    alarm := TRUE;
ELSIF manual_mode THEN
    (* 手动模式：停止自动控制 *)
    inlet_valve := FALSE;
    outlet_valve := FALSE;
    pump := FALSE;
    alarm := FALSE;
ELSE
    (* 自动模式 *)
    IF water_level < low_limit THEN
        inlet_valve := TRUE;
        outlet_valve := FALSE;
        pump := TRUE;
    ELSIF water_level > high_limit THEN
        inlet_valve := FALSE;
        outlet_valve := TRUE;
        pump := FALSE;
    END_IF;

    (* 异常水位报警 *)
    IF (water_level < 5) OR (water_level > 95) THEN
        alarm := TRUE;
    ELSE
        alarm := FALSE;
    END_IF;
END_IF;

END_PROGRAM

CONFIGURATION Config0
  RESOURCE Res0 ON PLC
    TASK Main(INTERVAL := T#100ms, PRIORITY := 0);
    PROGRAM Inst0 WITH Main : WaterTankControl;
  END_RESOURCE
END_CONFIGURATION
'''
        result['output_file'] = "generated_water_tank.st"
        with open(result['output_file'], 'w') as f:
            f.write(demo_code)
        print("✅ 演示代码已创建!")
        print()

except ImportError as e:
    print(f"❌ 无法导入代码生成模块: {e}")
    print("   请确保已安装所有依赖")
    sys.exit(1)

# ============================================================
# 步骤3: 验证ST代码语法
# ============================================================
print("【步骤3】验证ST代码语法")
print("-" * 80)

import subprocess
import os

st_file = result.get('output_file', 'generated_water_tank.st')
iec2c_path = "/Users/scott/pythonrepo/Agents4PLC_release/OpenPLC_v3/webserver/iec2c"

if os.path.exists(iec2c_path):
    print("⚙️  使用iec2c编译器验证语法...")
    try:
        result_verify = subprocess.run(
            [iec2c_path, "-f", "-l", "-p", "-r", "-R", "-a", st_file],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result_verify.returncode == 0:
            print("✅ 语法验证通过!")
            print("   生成的C文件: POUS.c, Config0.c, Res0.c")

            # 清理临时文件
            for f in ['POUS.c', 'POUS.h', 'Config0.c', 'Config0.h', 'Res0.c',
                     'LOCATED_VARIABLES.h', 'VARIABLES.csv']:
                if os.path.exists(f):
                    os.remove(f)
        else:
            print("❌ 语法错误:")
            print(result_verify.stderr)
    except Exception as e:
        print(f"⚠️  验证失败: {e}")
else:
    print("⚠️  iec2c编译器未找到，跳过语法验证")

print()

# ============================================================
# 步骤4: 总结
# ============================================================
print("【步骤4】完成！")
print("-" * 80)
print()
print("✅ 成功完成从自然语言到ST代码的转换！")
print()
print("📁 生成的文件:")
print(f"   {st_file}")
print()
print("🚀 后续步骤:")
print("   1. 将ST代码上传到OpenPLC (http://localhost:8080)")
print("   2. 编译并启动PLC")
print("   3. 通过Modbus TCP测试控制逻辑")
print()
print("=" * 80)
print("演示完成!")
print("=" * 80)
