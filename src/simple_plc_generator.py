"""
SimplePLC Generator - 简化的PLC代码自动生成和验证框架
Simple PLC Generator - Simplified framework for automatic PLC code generation and verification

这是一个用户友好的接口，整合了代码生成、验证和自动修复功能。
"""

import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

import os
import tempfile
from typing import Optional, List, Dict
from dataclasses import dataclass
from datetime import datetime

from src.code_generator import CodeGenerator
from src.verifier import Verifier, VerifyResult
from src.auto_fixer import AutoFixer, IterativeFixer
from src.st_animator import STAnimator


@dataclass
class GenerationResult:
    """
    代码生成结果
    """
    success: bool
    st_code: str
    verify_result: Optional[VerifyResult] = None
    iterations: int = 1
    error_message: str = ""
    st_file_path: str = ""
    animation_html_path: str = ""

    def __str__(self):
        output = []
        output.append("=" * 80)
        output.append("PLC Code Generation Result")
        output.append("=" * 80)

        if self.success:
            output.append(f"Status: ✓ SUCCESS (after {self.iterations} iteration(s))")
        else:
            output.append(f"Status: ✗ FAILED")
            if self.error_message:
                output.append(f"Error: {self.error_message}")

        output.append("\n--- Generated ST Code ---")
        output.append(self.st_code)

        if self.verify_result:
            output.append("\n--- Verification Results ---")
            output.append(str(self.verify_result))

        if self.st_file_path:
            output.append(f"\nST Code saved to: {self.st_file_path}")

        output.append("=" * 80)

        return "\n".join(output)

    def save_to_file(self, output_path: str = None):
        """
        保存ST代码到文件

        Args:
            output_path: 输出文件路径（可选）
        """
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"generated_plc_{timestamp}.ST"

        with open(output_path, 'w') as f:
            f.write(self.st_code)

        self.st_file_path = output_path
        print(f"ST code saved to: {output_path}")

        return output_path


class SimplePLCGenerator:
    """
    简化的PLC代码生成器 - 主接口类

    功能:
    1. 从自然语言生成ST代码
    2. 编译验证
    3. 属性验证（可选）
    4. 自动修复错误
    """

    def __init__(self,
                 llm_config: Dict = None,
                 compiler: str = "rusty",
                 enable_verification: bool = True,
                 enable_auto_fix: bool = True,
                 max_fix_iterations: int = 3,
                 enable_rag: bool = False,
                 rag_db_path: str = None):
        """
        初始化SimplePLCGenerator

        Args:
            llm_config: LLM配置字典 {"model": "gpt-4", "api_key": "...", "base_url": "..."}
            compiler: 编译器类型 ("rusty" 或 "matiec")
            enable_verification: 是否启用编译和属性验证
            enable_auto_fix: 是否启用自动修复
            max_fix_iterations: 最大修复迭代次数
            enable_rag: 是否启用RAG
            rag_db_path: RAG数据库路径
        """
        self.llm_config = llm_config or self._load_default_config()
        self.compiler = compiler
        self.enable_verification = enable_verification
        self.enable_auto_fix = enable_auto_fix
        self.max_fix_iterations = max_fix_iterations
        self.enable_rag = enable_rag
        self.rag_db_path = rag_db_path

        # 初始化各个模块
        self.code_generator = CodeGenerator(
            llm_config=self.llm_config,
            enable_rag=self.enable_rag,
            rag_db_path=self.rag_db_path
        )

        self.verifier = Verifier(
            compiler_type=self.compiler,
            enable_property_verification=True
        )

        self.auto_fixer = AutoFixer(llm_config=self.llm_config)

        self.iterative_fixer = IterativeFixer(
            auto_fixer=self.auto_fixer,
            max_iterations=self.max_fix_iterations
        )

        # 初始化动画生成器
        self.animator = STAnimator()

        print(f"SimplePLCGenerator initialized:")
        print(f"  - LLM Model: {self.llm_config.get('model', 'default')}")
        print(f"  - Compiler: {self.compiler}")
        print(f"  - Verification: {self.enable_verification}")
        print(f"  - Auto-fix: {self.enable_auto_fix}")
        print(f"  - RAG: {self.enable_rag}")

    def _load_default_config(self) -> Dict:
        """从config.py加载默认配置"""
        try:
            from config import chat_model, openai_api_key, openai_base_url
            return {
                'model': chat_model,
                'api_key': openai_api_key,
                'base_url': openai_base_url,
                'temperature': 0.1
            }
        except ImportError:
            raise RuntimeError("Failed to load config.py. Please create it based on config_template.py")

    def generate(self,
                 instruction: str,
                 properties: Optional[List[Dict]] = None,
                 save_to_file: bool = True,
                 output_path: str = None) -> GenerationResult:
        """
        生成PLC代码（主要接口）

        Args:
            instruction: 自然语言指令
            properties: 需要验证的属性列表（可选）
            save_to_file: 是否保存到文件
            output_path: 输出文件路径（可选）

        Returns:
            GenerationResult: 生成结果

        Example:
            >>> generator = SimplePLCGenerator()
            >>> result = generator.generate(
            ...     instruction="Create a function block to control a motor when temperature exceeds 80 degrees",
            ...     properties=[
            ...         {
            ...             "property_description": "If temperature > 80, motor should be TRUE",
            ...             "property": {
            ...                 "job_req": "pattern",
            ...                 "pattern_id": "pattern-implication",
            ...                 "pattern_params": {
            ...                     "1": "instance.temperature > 80.0",
            ...                     "2": "instance.motor = TRUE"
            ...                 }
            ...             }
            ...         }
            ...     ]
            ... )
            >>> print(result)
        """
        print("\n" + "=" * 80)
        print("Starting PLC Code Generation")
        print("=" * 80)
        print(f"Instruction: {instruction}")
        print("=" * 80)

        try:
            # 步骤1: 生成ST代码
            print("\n[Step 1] Generating ST code...")
            if properties:
                st_code, enhanced_instruction = self.code_generator.generate_with_properties(
                    instruction, properties
                )
            else:
                st_code = self.code_generator.generate(instruction)
                enhanced_instruction = instruction

            print("✓ ST code generated")

            # 如果不需要验证，直接返回
            if not self.enable_verification:
                result = GenerationResult(
                    success=True,
                    st_code=st_code,
                    iterations=1
                )

                if save_to_file:
                    result.save_to_file(output_path)

                return result

            # 步骤2: 验证代码
            print("\n[Step 2] Verifying ST code...")

            if self.enable_auto_fix:
                # 使用迭代修复器
                fixed_code, verify_result, iterations, success = self.iterative_fixer.fix_iteratively(
                    original_code=st_code,
                    verify_func=self.verifier.verify,
                    original_instruction=enhanced_instruction,
                    properties=properties,
                    save_to_file=True
                )

                result = GenerationResult(
                    success=success,
                    st_code=fixed_code,
                    verify_result=verify_result,
                    iterations=iterations,
                    error_message="" if success else "Failed to fix code after maximum iterations"
                )
            else:
                # 仅验证，不修复
                verify_result = self.verifier.verify(st_code, properties=properties, save_to_file=True)

                result = GenerationResult(
                    success=verify_result.overall_success,
                    st_code=st_code,
                    verify_result=verify_result,
                    iterations=1,
                    error_message="" if verify_result.overall_success else "Verification failed"
                )

            # 保存到文件
            if save_to_file:
                result.save_to_file(output_path)

            return result

        except Exception as e:
            print(f"\n✗ Error occurred: {str(e)}")
            return GenerationResult(
                success=False,
                st_code="",
                error_message=str(e)
            )

    def quick_generate(self, instruction: str) -> str:
        """
        快速生成模式（无验证，仅返回ST代码字符串）

        Args:
            instruction: 自然语言指令

        Returns:
            ST代码字符串
        """
        return self.code_generator.generate(instruction)

    def verify_existing_code(self,
                            st_code: str,
                            properties: Optional[List[Dict]] = None) -> VerifyResult:
        """
        验证已有的ST代码

        Args:
            st_code: ST代码
            properties: 需要验证的属性列表

        Returns:
            VerifyResult: 验证结果
        """
        return self.verifier.verify(st_code, properties=properties)

    def fix_existing_code(self,
                         st_code: str,
                         properties: Optional[List[Dict]] = None,
                         original_instruction: str = "") -> GenerationResult:
        """
        修复已有的ST代码

        Args:
            st_code: 有错误的ST代码
            properties: 需要验证的属性列表
            original_instruction: 原始指令（可选）

        Returns:
            GenerationResult: 修复结果
        """
        print("\n" + "=" * 80)
        print("Fixing Existing ST Code")
        print("=" * 80)

        fixed_code, verify_result, iterations, success = self.iterative_fixer.fix_iteratively(
            original_code=st_code,
            verify_func=self.verifier.verify,
            original_instruction=original_instruction,
            properties=properties,
            save_to_file=False
        )

        return GenerationResult(
            success=success,
            st_code=fixed_code,
            verify_result=verify_result,
            iterations=iterations,
            error_message="" if success else "Failed to fix code"
        )

    def generate_animation(self,
                          st_code: str,
                          input_values: Dict[str, any] = None,
                          output_html_path: str = None,
                          max_cycles: int = 1,
                          auto_open: bool = True) -> str:
        """
        生成ST代码执行动画

        Args:
            st_code: ST代码
            input_values: 输入变量的值字典，例如 {'start_button': True, 'temperature': 25.0}
            output_html_path: 输出HTML文件路径（可选）
            max_cycles: 最大扫描周期数
            auto_open: 是否自动在浏览器中打开

        Returns:
            生成的HTML文件路径

        Example:
            >>> generator = SimplePLCGenerator()
            >>> html_path = generator.generate_animation(
            ...     st_code=my_st_code,
            ...     input_values={'start_button': True, 'temperature': 25.0},
            ...     auto_open=True
            ... )
        """
        print("\n" + "=" * 80)
        print("Generating ST Code Animation")
        print("=" * 80)

        try:
            html_path = self.animator.generate_animation(
                st_code=st_code,
                input_values=input_values,
                output_html_path=output_html_path,
                max_cycles=max_cycles,
                auto_open=auto_open
            )

            print(f"✓ Animation generated: {html_path}")
            return html_path

        except Exception as e:
            print(f"✗ Failed to generate animation: {str(e)}")
            raise

    def generate_with_animation(self,
                               instruction: str,
                               input_values: Dict[str, any] = None,
                               properties: Optional[List[Dict]] = None,
                               save_to_file: bool = True,
                               output_path: str = None,
                               auto_open_animation: bool = True) -> GenerationResult:
        """
        生成PLC代码并同时生成动画演示

        Args:
            instruction: 自然语言指令
            input_values: 动画演示的输入变量值
            properties: 需要验证的属性列表（可选）
            save_to_file: 是否保存到文件
            output_path: 输出文件路径（可选）
            auto_open_animation: 是否自动在浏览器中打开动画

        Returns:
            GenerationResult: 生成结果（包含animation_html_path）

        Example:
            >>> generator = SimplePLCGenerator()
            >>> result = generator.generate_with_animation(
            ...     instruction="Create a motor control system",
            ...     input_values={'start_button': True, 'temperature': 25.0}
            ... )
            >>> print(f"Code: {result.st_file_path}")
            >>> print(f"Animation: {result.animation_html_path}")
        """
        # 首先生成代码
        result = self.generate(
            instruction=instruction,
            properties=properties,
            save_to_file=save_to_file,
            output_path=output_path
        )

        # 如果代码生成成功，生成动画
        if result.success and result.st_code:
            try:
                print("\n[Bonus] Generating animation...")
                animation_path = self.generate_animation(
                    st_code=result.st_code,
                    input_values=input_values,
                    auto_open=auto_open_animation
                )
                result.animation_html_path = animation_path
                print(f"✓ Animation ready: {animation_path}")
            except Exception as e:
                print(f"⚠ Animation generation failed (code generation succeeded): {str(e)}")

        return result


def demo():
    """演示SimplePLCGenerator的使用"""
    print("\n" + "#" * 80)
    print("# SimplePLCGenerator Demo")
    print("#" * 80)

    # 初始化生成器
    generator = SimplePLCGenerator(
        compiler="rusty",
        enable_verification=True,
        enable_auto_fix=True,
        max_fix_iterations=3
    )

    # 示例1: LED控制
    print("\n\n" + "="*80)
    print("Demo 1: LED Control")
    print("="*80)

    instruction1 = """
    Create a function block to control an LED light.
    Input: button (BOOL)
    Output: led (BOOL)
    Logic: Toggle LED state when button is pressed
    """

    result1 = generator.generate(instruction1, save_to_file=True)
    print(result1)

    # 示例2: 温度控制（带属性验证）
    print("\n\n" + "="*80)
    print("Demo 2: Temperature Control with Property Verification")
    print("="*80)

    instruction2 = "Create a function block for temperature control. If temperature exceeds 80 degrees, activate the cooling motor."

    properties2 = [
        {
            "property_description": "If temperature > 80, motor should be TRUE",
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
            "property_description": "If temperature <= 80, motor should be FALSE",
            "property": {
                "job_req": "pattern",
                "pattern_id": "pattern-implication",
                "pattern_params": {
                    "1": "instance.temperature <= 80.0",
                    "2": "instance.motor = FALSE"
                }
            }
        }
    ]

    result2 = generator.generate(instruction2, properties=properties2, save_to_file=True)
    print(result2)

    # 示例3: 快速生成（无验证）
    print("\n\n" + "="*80)
    print("Demo 3: Quick Generate (No Verification)")
    print("="*80)

    quick_generator = SimplePLCGenerator(enable_verification=False)
    instruction3 = "Create a timer that activates an alarm after 10 seconds"
    st_code3 = quick_generator.quick_generate(instruction3)

    print("Generated ST Code:")
    print(st_code3)

    print("\n" + "#" * 80)
    print("# Demo Completed")
    print("#" * 80)


if __name__ == "__main__":
    # 运行演示
    try:
        demo()
    except Exception as e:
        print(f"\nDemo failed: {str(e)}")
        print("\nPlease ensure:")
        print("  1. config.py is properly configured with API keys")
        print("  2. Compiler (rusty or matiec) is installed and accessible")
        print("  3. PLCverif tools are installed (optional, for property verification)")
