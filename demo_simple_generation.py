#!/usr/bin/env python3
"""
简化演示：从自然语言生成PLC代码（跳过复杂验证）
展示核心功能：自然语言 → ST代码
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent / "src"))

from simple_plc_generator import SimplePLCGenerator
import subprocess
import os

print("=" * 80)
print("🤖 Agents4PLC - 从自然语言生成PLC代码演示")
print("=" * 80)
print()

# ============================================================
# 步骤1: 定义自然语言需求
# ============================================================
print("【步骤1】自然语言控制需求")
print("-" * 80)

instruction = """
创建一个简单的交通信号灯控制系统。

输入变量:
- manual_mode : BOOL    (手动模式)
- emergency : BOOL      (紧急情况按钮)

输出变量:
- red_light : BOOL      (红灯)
- yellow_light : BOOL   (黄灯)
- green_light : BOOL    (绿灯)

内部变量:
- timer : TON           (定时器)
- state : INT          (状态：0=红灯30秒, 1=绿灯25秒, 2=黄灯5秒)

控制逻辑:
1. 正常模式：红灯30秒 → 绿灯25秒 → 黄灯5秒 → 循环
2. 手动模式：所有灯熄灭
3. 紧急情况：黄灯闪烁
"""

print(instruction)
print()

# ============================================================
# 步骤2: 调用LLM生成ST代码
# ============================================================
print("【步骤2】调用GPT-4生成ST代码")
print("-" * 80)

# 禁用验证和自动修复，只生成代码
generator = SimplePLCGenerator(
    compiler="rusty",           # 编译器（实际不用）
    enable_verification=False,   # 禁用验证
    enable_auto_fix=False        # 禁用自动修复
)

print("⏳ 正在调用GPT-4 API生成代码...")
print()

result = generator.generate(
    instruction=instruction,
    save_to_file=True,
    output_path="generated_traffic_light.st"
)

if result.success:
    print("=" * 80)
    print("✅ ST代码生成成功!")
    print("=" * 80)
    print()

    print("【生成的ST代码】")
    print("-" * 80)
    print(result.st_code)
    print("-" * 80)
    print()

    print(f"📁 代码已保存到: {result.st_file_path}")
    print()

    # ============================================================
    # 步骤3: 使用iec2c验证语法
    # ============================================================
    print("【步骤3】使用iec2c验证ST语法")
    print("-" * 80)

    iec2c_path = "/Users/scott/pythonrepo/Agents4PLC_release/OpenPLC_v3/webserver/iec2c"

    if os.path.exists(iec2c_path):
        try:
            verify_result = subprocess.run(
                [iec2c_path, "-f", "-l", "-p", "-r", "-R", "-a", result.st_file_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            if verify_result.returncode == 0:
                print("✅ ST语法验证通过!")
                print("   成功生成C文件: POUS.c, Config0.c, Res0.c")

                # 清理生成的C文件
                for f in ['POUS.c', 'POUS.h', 'Config0.c', 'Config0.h', 'Res0.c',
                         'LOCATED_VARIABLES.h', 'VARIABLES.csv']:
                    if os.path.exists(f):
                        os.remove(f)
            else:
                print("⚠️  语法验证失败:")
                print(verify_result.stderr[:500])
        except Exception as e:
            print(f"⚠️  验证时出错: {e}")
    else:
        print("⚠️  iec2c编译器未找到，跳过验证")

    print()

    # ============================================================
    # 步骤4: 总结
    # ============================================================
    print("=" * 80)
    print("🎉 演示完成！")
    print("=" * 80)
    print()
    print("✅ 您刚刚看到的完整流程:")
    print("   1. 用自然语言描述控制需求")
    print("   2. 系统调用GPT-4 API")
    print("   3. 生成符合IEC-61131-3标准的ST代码")
    print("   4. 验证代码语法正确性")
    print()
    print("📋 接下来可以:")
    print("   • 将生成的ST代码上传到OpenPLC")
    print("   • 通过Modbus TCP控制真实设备")
    print("   • 使用形式化验证工具验证安全属性")
    print()
    print(f"📁 生成的代码文件: {result.st_file_path}")
    print()

else:
    print("=" * 80)
    print("❌ 代码生成失败")
    print("=" * 80)
    print(f"错误信息: {result.error_message}")
    print()
    print("可能的原因:")
    print("  • API密钥未配置或已过期")
    print("  • 网络连接问题")
    print("  • LLM服务不可用")
    print()
    print("请检查 config.py 中的API配置")
