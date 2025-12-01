"""
自动修复模块 - 基于错误信息自动修复PLC代码
Auto Fixer Module - Automatically fix PLC code based on error messages
"""

import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from typing import Dict
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from src.langchain_create_agent import create_agent


class AutoFixer:
    """
    自动修复器类，使用LLM根据错误信息修复代码
    """

    def __init__(self, llm_config: Dict = None, system_prompt_path: str = None):
        """
        初始化自动修复器

        Args:
            llm_config: LLM配置字典
            system_prompt_path: 系统提示词文件路径（可选）
        """
        self.llm_config = llm_config or {}
        self.system_prompt_path = system_prompt_path

        # 创建LLM代理
        self.agent = self._create_agent()

    def _create_agent(self):
        """创建LLM代理"""
        chat_model = self.llm_config.get('model', 'gpt-5.1')
        temperature = self.llm_config.get('temperature', 0.1)

        # 使用嵌入式系统提示词
        system_msg = self._get_system_prompt()

        return create_agent(
            chat_model=chat_model,
            system_msg=system_msg,
            system_msg_is_dir=False,
            temperature=temperature,
            include_rag=False
        )

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        if self.system_prompt_path and Path(self.system_prompt_path).exists():
            with open(self.system_prompt_path, 'r') as f:
                return f.read()

        # 默认嵌入式提示词
        return """You are an expert PLC code debugger specializing in IEC-61131-3 Structured Text (ST).

Your task is to fix errors in ST code based on compilation errors or verification failures.

INSTRUCTIONS:
1. Carefully analyze the error message
2. Identify the root cause of the error
3. Fix the code while preserving the original functionality
4. Ensure the fixed code follows IEC-61131-3 standards
5. Always enclose the fixed ST code within [start_scl] and [end_scl] tags
6. Provide a brief explanation of what you fixed

COMMON ERROR TYPES AND FIXES:
- Syntax errors: Missing semicolons, incorrect keywords, etc.
- Type mismatches: Ensure variables have correct data types
- Undeclared variables: Add missing variable declarations
- Logic errors: Fix conditional statements, loops, etc.
- Property violations: Adjust logic to satisfy verification properties

RESPONSE FORMAT:
Brief explanation: <What was wrong and how you fixed it>

[start_scl]
<Fixed ST code>
[end_scl]

Be concise and focused on fixing the specific error.
"""

    def fix(self,
            original_code: str,
            error_message: str,
            original_instruction: str = "",
            previous_attempts: list = None) -> str:
        """
        修复代码

        Args:
            original_code: 原始有错误的ST代码
            error_message: 错误信息（编译错误或验证错误）
            original_instruction: 原始用户指令（可选，有助于理解意图）
            previous_attempts: 之前的修复尝试（可选，避免重复错误）

        Returns:
            修复后的ST代码
        """
        # 构建修复请求消息
        fix_request = self._build_fix_request(
            original_code,
            error_message,
            original_instruction,
            previous_attempts
        )

        # 调用LLM修复
        messages = [HumanMessage(content=fix_request)]
        response = self.agent.invoke({"messages": messages})

        # 提取修复后的代码
        fixed_code = self._extract_fixed_code(response)

        return fixed_code

    def _build_fix_request(self,
                           original_code: str,
                           error_message: str,
                           original_instruction: str = "",
                           previous_attempts: list = None) -> str:
        """
        构建修复请求消息

        Args:
            original_code: 原始代码
            error_message: 错误信息
            original_instruction: 原始指令
            previous_attempts: 之前的尝试

        Returns:
            修复请求字符串
        """
        request_parts = []

        # 添加原始指令（如果有）
        if original_instruction:
            request_parts.append(f"Original User Instruction:\n{original_instruction}\n")

        # 添加错误的代码
        request_parts.append(f"Code with Error:\n```\n{original_code}\n```\n")

        # 添加错误信息
        request_parts.append(f"Error Message:\n{error_message}\n")

        # 添加之前的尝试（如果有）
        if previous_attempts:
            request_parts.append("\nPrevious Failed Attempts:")
            for i, attempt in enumerate(previous_attempts, 1):
                request_parts.append(f"\nAttempt {i}:")
                request_parts.append(f"Code:\n```\n{attempt['code']}\n```")
                request_parts.append(f"Error:\n{attempt['error']}\n")

            request_parts.append("\nPlease avoid repeating the same mistakes.\n")

        request_parts.append("\nPlease fix the code and provide the corrected version.")

        return "\n".join(request_parts)

    def _extract_fixed_code(self, response) -> str:
        """
        从LLM响应中提取修复后的代码

        Args:
            response: LLM响应

        Returns:
            修复后的代码
        """
        import re

        # 获取响应内容
        if hasattr(response, 'content'):
            response_text = response.content
        elif isinstance(response, str):
            response_text = response
        else:
            response_text = str(response)

        # 提取[start_scl]...[end_scl]之间的内容
        pattern = r'\[start_scl\](.*?)\[end_scl\]'
        match = re.search(pattern, response_text, re.DOTALL)

        if match:
            return match.group(1).strip()

        # 如果没有标记，尝试提取FUNCTION_BLOCK...END_FUNCTION_BLOCK
        pattern_fb = r'(FUNCTION_BLOCK.*?END_FUNCTION_BLOCK)'
        match_fb = re.search(pattern_fb, response_text, re.DOTALL | re.IGNORECASE)

        if match_fb:
            return match_fb.group(1).strip()

        # 如果都没有，返回原始响应
        return response_text.strip()


class IterativeFixer:
    """
    迭代修复器，支持多轮修复尝试
    """

    def __init__(self, auto_fixer: AutoFixer, max_iterations: int = 3):
        """
        初始化迭代修复器

        Args:
            auto_fixer: AutoFixer实例
            max_iterations: 最大迭代次数
        """
        self.auto_fixer = auto_fixer
        self.max_iterations = max_iterations

    def fix_iteratively(self,
                        original_code: str,
                        verify_func,
                        original_instruction: str = "",
                        **verify_kwargs) -> tuple:
        """
        迭代修复代码直到通过验证或达到最大迭代次数

        Args:
            original_code: 原始代码
            verify_func: 验证函数（应返回VerifyResult对象）
            original_instruction: 原始指令
            **verify_kwargs: 传递给验证函数的额外参数

        Returns:
            (fixed_code, verify_result, iteration_count, success): 修复后的代码、验证结果、迭代次数、是否成功
        """
        current_code = original_code
        previous_attempts = []

        for iteration in range(1, self.max_iterations + 1):
            print(f"\n--- Fix Iteration {iteration}/{self.max_iterations} ---")

            # 验证当前代码
            verify_result = verify_func(current_code, **verify_kwargs)

            # 如果验证通过，返回成功
            if verify_result.overall_success:
                print(f"✓ Code fixed successfully in {iteration} iteration(s)!")
                return current_code, verify_result, iteration, True

            # 提取错误信息
            error_message = self._extract_error_from_result(verify_result)

            print(f"Error found: {error_message[:200]}...")  # 打印前200个字符

            # 记录此次失败的尝试
            previous_attempts.append({
                'code': current_code,
                'error': error_message
            })

            # 如果已经达到最大迭代次数，返回失败
            if iteration >= self.max_iterations:
                print(f"✗ Failed to fix code after {self.max_iterations} attempts.")
                return current_code, verify_result, iteration, False

            # 使用AutoFixer修复代码
            current_code = self.auto_fixer.fix(
                original_code=current_code,
                error_message=error_message,
                original_instruction=original_instruction,
                previous_attempts=previous_attempts[:-1]  # 不包括当前尝试
            )

            print(f"Code fixed. Verifying again...")

        # 理论上不会到这里，但为了安全
        return current_code, verify_result, self.max_iterations, False

    def _extract_error_from_result(self, verify_result) -> str:
        """
        从验证结果中提取错误信息

        Args:
            verify_result: VerifyResult对象

        Returns:
            错误信息字符串
        """
        error_parts = []

        # 编译错误
        if not verify_result.compile_result.success:
            error_parts.append(f"Compilation Error:\n{verify_result.compile_result.error_message}")

        # 属性验证错误
        if verify_result.property_results:
            for i, result in enumerate(verify_result.property_results, 1):
                if "is violated" in result or "is not successfully checked" in result:
                    error_parts.append(f"Property {i} Verification Error:\n{result}")

        return "\n\n".join(error_parts) if error_parts else "Unknown error"


if __name__ == "__main__":
    """测试自动修复器"""

    try:
        from config import chat_model, openai_api_key, openai_base_url

        llm_config = {
            'model': chat_model,
            'api_key': openai_api_key,
            'base_url': openai_base_url,
            'temperature': 0.1
        }

        # 测试AutoFixer
        fixer = AutoFixer(llm_config=llm_config)

        # 错误的ST代码（缺少分号）
        buggy_code = """
FUNCTION_BLOCK MotorControl
VAR_INPUT
    start_button : BOOL
END_VAR

VAR_OUTPUT
    motor : BOOL
END_VAR

    motor := start_button

END_FUNCTION_BLOCK
"""

        error_msg = "Syntax error: Missing semicolon at the end of statement"

        print("=" * 80)
        print("Testing AutoFixer")
        print("=" * 80)
        print(f"\nBuggy Code:\n{buggy_code}")
        print(f"\nError Message:\n{error_msg}")
        print("\n" + "=" * 80)

        fixed_code = fixer.fix(buggy_code, error_msg)

        print(f"\nFixed Code:\n{fixed_code}")
        print("=" * 80)

    except ImportError as e:
        print(f"Error: Please configure config.py first. {e}")
        print("Skipping tests...")
