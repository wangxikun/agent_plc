"""
验证模块 - PLC代码的编译和属性验证 (修复版)
Verifier Module - Compilation and property verification for PLC code (Fixed Version)

主要修复:
1. CompileResult数据结构分离compiler_name和temp_file_path
2. 添加临时文件自动清理机制
3. 改进错误处理
"""

import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

import os
import tempfile
from typing import Optional, List, Dict
from dataclasses import dataclass
from contextlib import contextmanager
from src.compiler import rusty_compiler, matiec_compiler
from src.plcverif import plcverif_validation


@contextmanager
def temp_st_file(st_code: str):
    """
    创建临时ST文件的上下文管理器，自动清理

    Args:
        st_code: ST代码内容

    Yields:
        str: 临时文件路径
    """
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ST', delete=False) as f:
            f.write(st_code)
            temp_file = f.name
        yield temp_file
    finally:
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except Exception as e:
                print(f"Warning: Failed to delete temp file {temp_file}: {e}")


@dataclass
class CompileResult:
    """编译结果 (修复版: 分离compiler_name和temp_file_path)"""
    success: bool
    compiler_name: str = ""          # 编译器名称 (Rusty/Matiec)
    temp_file_path: str = ""         # 临时文件路径（成功时非空）
    error_message: str = ""          # 错误信息（失败时非空）

    def __str__(self):
        if self.success:
            return f"✓ Compilation PASSED ({self.compiler_name})"
        else:
            return f"✗ Compilation FAILED ({self.compiler_name})\nError: {self.error_message}"


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
            save_to_file: 是否保存代码到文件（如果需要属性验证，会强制为True）
            output_dir: 输出目录

        Returns:
            VerifyResult: 验证结果
        """
        # 如果需要属性验证，必须保存文件
        if self.enable_property_verification and properties:
            save_to_file = True

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
            if not compile_result.temp_file_path:
                # 如果没有保存文件，现在保存
                with temp_st_file(st_code) as temp_file:
                    property_results = self.property_check(
                        temp_file,  # ✅ 使用明确的临时文件路径
                        properties,
                        output_dir=output_dir
                    )
            else:
                property_results = self.property_check(
                    compile_result.temp_file_path,  # ✅ 使用CompileResult中的路径
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
        if not save_to_file:
            # 不保存文件的情况（需要编译器支持字符串输入，当前不支持）
            return CompileResult(
                success=False,
                compiler_name=self.compiler_type,
                error_message="Compiler requires file input. Set save_to_file=True."
            )

        # 确定编译器名称
        compiler_name = "Rusty" if self.compiler_type == "rusty" else "Matiec"

        # 使用临时文件进行编译
        with temp_st_file(st_code) as temp_file:
            try:
                # 调用编译器
                if self.compiler_type == "rusty":
                    success = rusty_compiler(temp_file)
                else:  # matiec
                    success = matiec_compiler(temp_file)

                if success:
                    # ✅ 成功：保存文件路径以供后续使用
                    # 注意：这里我们创建一个持久化的副本，因为temp_file会被清理
                    persistent_file = temp_file + ".verified"
                    import shutil
                    shutil.copy(temp_file, persistent_file)

                    return CompileResult(
                        success=True,
                        compiler_name=compiler_name,
                        temp_file_path=persistent_file,  # ✅ 使用持久化文件
                        error_message=""
                    )
                else:
                    # ✅ 失败：获取详细错误信息
                    error_msg = self._get_detailed_compile_error(temp_file, self.compiler_type)
                    return CompileResult(
                        success=False,
                        compiler_name=compiler_name,
                        temp_file_path="",  # ✅ 失败时为空
                        error_message=error_msg or "Compilation failed. Check syntax."
                    )

            except Exception as e:
                return CompileResult(
                    success=False,
                    compiler_name=compiler_name,
                    temp_file_path="",
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
                    text=True,
                    timeout=10  # 添加超时
                )
                return result.stderr + result.stdout
            elif compiler_type == "matiec":
                try:
                    from config import MATIEC_PATH
                except ImportError:
                    return "MATIEC_PATH not configured in config.py"

                if not MATIEC_PATH:
                    return "MATIEC_PATH is empty in config.py"

                result = subprocess.run(
                    f'iec2iec -f -p "{file_path}"',
                    cwd=MATIEC_PATH,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10  # 添加超时
                )
                return result.stderr + result.stdout
        except subprocess.TimeoutExpired:
            return "Compilation timed out after 10 seconds"
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
        # 清理临时文件
        if result.temp_file_path and os.path.exists(result.temp_file_path):
            try:
                os.unlink(result.temp_file_path)
            except:
                pass
        return result.success

    def __del__(self):
        """析构函数：清理所有创建的临时文件"""
        # 这里可以添加全局的临时文件清理逻辑
        pass


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
    print("Testing Verifier Module (Fixed Version)")
    print("=" * 80)

    # 测试1: 仅编译验证
    print("\n--- Test 1: Compile Check Only ---")
    verifier = Verifier(compiler_type="rusty", enable_property_verification=False)
    result1 = verifier.verify(test_st_code)
    print(result1)
    print(f"\nCompile Result Details:")
    print(f"  - Success: {result1.compile_result.success}")
    print(f"  - Compiler: {result1.compile_result.compiler_name}")
    print(f"  - Temp File: {result1.compile_result.temp_file_path}")

    # 测试2: 编译 + 属性验证
    print("\n--- Test 2: Compile + Property Verification ---")
    verifier2 = Verifier(compiler_type="rusty", enable_property_verification=True)
    result2 = verifier2.verify(test_st_code, properties=test_properties)
    print(result2)

    print("\n" + "=" * 80)
    print("Tests completed")
    print("=" * 80)
