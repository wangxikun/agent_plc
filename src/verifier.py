"""
验证模块 - PLC代码的编译和属性验证
Verifier Module - Compilation and property verification for PLC code
"""

import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

import os
import tempfile
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from src.compiler import rusty_compiler, matiec_compiler
from src.plcverif import plcverif_validation


@dataclass
class CompileResult:
    """编译结果"""
    success: bool
    error_message: str = ""
    compiler_used: str = ""

    def __str__(self):
        if self.success:
            return f"✓ Compilation PASSED ({self.compiler_used})"
        else:
            return f"✗ Compilation FAILED ({self.compiler_used})\nError: {self.error_message}"


@dataclass
class VerifyResult:
    """验证结果"""
    compile_result: CompileResult
    property_results: List[str] = None
    overall_success: bool = False
    summary: str = ""

    def __str__(self):
        output = [str(self.compile_result)]

        if self.property_results:
            output.append("\n--- Property Verification Results ---")
            for i, result in enumerate(self.property_results, 1):
                output.append(f"\nProperty {i}:\n{result}")

        output.append(f"\n{'='*60}")
        output.append(f"Overall: {'✓ SUCCESS' if self.overall_success else '✗ FAILED'}")
        output.append(f"{'='*60}")

        return "\n".join(output)


class Verifier:
    """
    验证器类，负责PLC代码的编译验证和属性验证
    """

    def __init__(self, compiler_type: str = "rusty", enable_property_verification: bool = True):
        """
        初始化验证器

        Args:
            compiler_type: 编译器类型 ("rusty" 或 "matiec")
            enable_property_verification: 是否启用属性验证
        """
        self.compiler_type = compiler_type.lower()
        self.enable_property_verification = enable_property_verification

        # 验证编译器是否可用
        if self.compiler_type not in ["rusty", "matiec"]:
            raise ValueError(f"Unsupported compiler: {compiler_type}. Use 'rusty' or 'matiec'.")

    def verify(self,
               st_code: str,
               properties: Optional[List[Dict]] = None,
               save_to_file: bool = True,
               output_dir: Optional[str] = None) -> VerifyResult:
        """
        完整验证流程：编译 + 属性验证

        Args:
            st_code: ST代码
            properties: 需要验证的属性列表
            save_to_file: 是否保存代码到文件
            output_dir: 输出目录

        Returns:
            VerifyResult: 验证结果
        """
        # 步骤1: 编译验证
        compile_result = self.compile_check(st_code, save_to_file=save_to_file)

        # 如果编译失败，直接返回
        if not compile_result.success:
            return VerifyResult(
                compile_result=compile_result,
                overall_success=False,
                summary="Compilation failed. Property verification skipped."
            )

        # 步骤2: 属性验证（如果启用且提供了属性）
        property_results = None
        if self.enable_property_verification and properties:
            property_results = self.property_check(
                compile_result.compiler_used,  # 使用保存的文件路径
                properties,
                output_dir=output_dir
            )

            # 判断属性验证是否全部通过
            all_properties_passed = all(
                "is satisfied" in result for result in property_results
            )

            overall_success = compile_result.success and all_properties_passed
            summary = "All verifications passed." if overall_success else "Some property verifications failed."
        else:
            overall_success = compile_result.success
            summary = "Compilation passed. No property verification performed."

        return VerifyResult(
            compile_result=compile_result,
            property_results=property_results,
            overall_success=overall_success,
            summary=summary
        )

    def compile_check(self, st_code: str, save_to_file: bool = True) -> CompileResult:
        """
        编译检查

        Args:
            st_code: ST代码
            save_to_file: 是否保存到临时文件

        Returns:
            CompileResult: 编译结果
        """
        # 保存代码到临时文件
        if save_to_file:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ST', delete=False) as f:
                f.write(st_code)
                temp_file = f.name
        else:
            # 如果不保存，这里需要其他处理方式
            # 但通常编译器需要文件路径
            temp_file = None

        try:
            # 调用编译器
            if self.compiler_type == "rusty":
                success = rusty_compiler(temp_file)
                compiler_name = "Rusty"
            else:  # matiec
                success = matiec_compiler(temp_file)
                compiler_name = "Matiec"

            if success:
                return CompileResult(
                    success=True,
                    compiler_used=temp_file,  # 保存文件路径以供后续验证使用
                    error_message=""
                )
            else:
                # 尝试获取更详细的错误信息
                error_msg = self._get_detailed_compile_error(temp_file, self.compiler_type)
                return CompileResult(
                    success=False,
                    compiler_used=compiler_name,
                    error_message=error_msg or "Compilation failed. Check syntax."
                )

        except Exception as e:
            return CompileResult(
                success=False,
                compiler_used=self.compiler_type,
                error_message=f"Compilation error: {str(e)}"
            )

    def _get_detailed_compile_error(self, file_path: str, compiler_type: str) -> str:
        """
        获取详细的编译错误信息

        Args:
            file_path: ST文件路径
            compiler_type: 编译器类型

        Returns:
            错误信息字符串
        """
        import subprocess

        try:
            if compiler_type == "rusty":
                result = subprocess.run(
                    f'plc --check {file_path}',
                    shell=True,
                    capture_output=True,
                    text=True
                )
                return result.stderr + result.stdout
            elif compiler_type == "matiec":
                from config import MATIEC_PATH
                result = subprocess.run(
                    f'iec2iec -f -p "{file_path}"',
                    cwd=MATIEC_PATH,
                    shell=True,
                    capture_output=True,
                    text=True
                )
                return result.stderr + result.stdout
        except Exception as e:
            return f"Failed to get detailed error: {str(e)}"

        return "Unknown compilation error"

    def property_check(self,
                       st_file_path: str,
                       properties: List[Dict],
                       output_dir: Optional[str] = None) -> List[str]:
        """
        属性验证

        Args:
            st_file_path: ST文件路径
            properties: 属性列表
            output_dir: 输出目录

        Returns:
            验证结果列表
        """
        if not output_dir:
            # 使用临时目录
            output_dir = tempfile.mkdtemp(prefix="plcverif_")

        try:
            # 调用plcverif验证
            results = plcverif_validation(
                st_dir=st_file_path,
                properties_to_be_validated=properties,
                base_dir=output_dir
            )
            return results
        except Exception as e:
            return [f"Property verification failed: {str(e)}"]

    def quick_compile_check(self, st_code: str) -> bool:
        """
        快速编译检查（仅返回True/False，不保存详细信息）

        Args:
            st_code: ST代码

        Returns:
            编译是否成功
        """
        result = self.compile_check(st_code)
        return result.success


if __name__ == "__main__":
    """测试验证器"""

    # 测试代码
    test_st_code = """
FUNCTION_BLOCK TemperatureControl
VAR_INPUT
    temperature : REAL;
END_VAR

VAR_OUTPUT
    motor : BOOL;
END_VAR

    IF temperature > 80.0 THEN
        motor := TRUE;
    ELSE
        motor := FALSE;
    END_IF;

END_FUNCTION_BLOCK
"""

    # 测试属性
    test_properties = [
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
        }
    ]

    print("=" * 80)
    print("Testing Verifier Module")
    print("=" * 80)

    # 测试1: 仅编译验证
    print("\n--- Test 1: Compile Check Only ---")
    verifier = Verifier(compiler_type="rusty", enable_property_verification=False)
    result1 = verifier.verify(test_st_code)
    print(result1)

    # 测试2: 编译 + 属性验证
    print("\n--- Test 2: Compile + Property Verification ---")
    verifier2 = Verifier(compiler_type="rusty", enable_property_verification=True)
    result2 = verifier2.verify(test_st_code, properties=test_properties)
    print(result2)

    print("\n" + "=" * 80)
    print("Tests completed")
    print("=" * 80)
