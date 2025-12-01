"""
代码生成模块 - 将自然语言转换为IEC-61131-3 ST代码
Code Generator Module - Convert natural language to IEC-61131-3 ST code
"""

import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

import re
from typing import Optional, Dict
from langchain_core.messages import HumanMessage
from src.langchain_create_agent import create_agent


class CodeGenerator:
    """
    代码生成器类，负责使用LLM将自然语言指令转换为PLC ST代码
    """

    def __init__(self,
                 llm_config: Dict = None,
                 system_prompt_path: str = None,
                 enable_rag: bool = False,
                 rag_db_path: str = None):
        """
        初始化代码生成器

        Args:
            llm_config: LLM配置字典，包含model, api_key, base_url等
            system_prompt_path: 系统提示词文件路径
            enable_rag: 是否启用RAG
            rag_db_path: RAG数据库路径
        """
        self.llm_config = llm_config or {}
        self.system_prompt_path = system_prompt_path or self._get_default_prompt_path()
        self.enable_rag = enable_rag
        self.rag_db_path = rag_db_path

        # 创建LLM代理
        self.agent = self._create_agent()

    def _get_default_prompt_path(self) -> str:
        """获取默认的系统提示词路径"""
        return str(parent_dir / "prompts" / "st_code_generation_prompt.txt")

    def _create_agent(self):
        """创建LLM代理"""
        chat_model = self.llm_config.get('model', 'gpt-4')
        embedding_model = self.llm_config.get('embedding_model', 'text-embedding-ada-002')
        temperature = self.llm_config.get('temperature', 0.1)

        # 如果系统提示词文件不存在，使用默认提示词
        if not Path(self.system_prompt_path).exists():
            print(f"Warning: System prompt file not found at {self.system_prompt_path}")
            print("Using default embedded prompt...")
            system_msg = self._get_default_embedded_prompt()
            system_msg_is_dir = False
        else:
            system_msg = self.system_prompt_path
            system_msg_is_dir = True

        return create_agent(
            chat_model=chat_model,
            embedding_model=embedding_model,
            system_msg=system_msg,
            system_msg_is_dir=system_msg_is_dir,
            temperature=temperature,
            include_rag=self.enable_rag,
            database_dir=self.rag_db_path if self.enable_rag else ""
        )

    def _get_default_embedded_prompt(self) -> str:
        """获取默认的嵌入式系统提示词"""
        return """You are an expert PLC programmer specializing in IEC-61131-3 Structured Text (ST) code generation.

Your task is to convert natural language instructions into valid, efficient, and well-structured ST code.

IMPORTANT REQUIREMENTS:
1. Always enclose your ST code within [start_scl] and [end_scl] tags
2. Follow IEC-61131-3 standard strictly
3. Use FUNCTION_BLOCK structure for modular design
4. Declare all variables properly (VAR_INPUT, VAR_OUTPUT, VAR)
5. Add clear comments to explain complex logic
6. Use proper data types (BOOL, INT, REAL, TIME, etc.)
7. Ensure code is compilable and free of syntax errors

CODE STRUCTURE TEMPLATE:
[start_scl]
FUNCTION_BLOCK <BlockName>
VAR_INPUT
    (* Input variables *)
END_VAR

VAR_OUTPUT
    (* Output variables *)
END_VAR

VAR
    (* Internal variables *)
END_VAR

(* Main logic *)

END_FUNCTION_BLOCK
[end_scl]

EXAMPLE:
User: "Create a function block to control a motor. When the start button is pressed, the motor should turn on. When the stop button is pressed, the motor should turn off."

Your response:
[start_scl]
FUNCTION_BLOCK MotorControl
VAR_INPUT
    start_button : BOOL; (* Start button input *)
    stop_button : BOOL;  (* Stop button input *)
END_VAR

VAR_OUTPUT
    motor : BOOL; (* Motor output *)
END_VAR

VAR
    motor_state : BOOL := FALSE; (* Internal motor state *)
END_VAR

(* Main logic: SR latch for motor control *)
IF start_button THEN
    motor_state := TRUE;
END_IF;

IF stop_button THEN
    motor_state := FALSE;
END_IF;

motor := motor_state;

END_FUNCTION_BLOCK
[end_scl]

Now, generate the ST code based on the user's instruction.
"""

    def generate(self, instruction: str, additional_context: str = "") -> str:
        """
        生成ST代码

        Args:
            instruction: 自然语言指令
            additional_context: 额外上下文信息（可选）

        Returns:
            生成的ST代码
        """
        # 构建用户消息
        user_message = instruction
        if additional_context:
            user_message = f"{instruction}\n\nAdditional Context:\n{additional_context}"

        # 调用LLM生成代码
        if self.enable_rag:
            # RAG模式：直接传递问题字符串
            response = self.agent.invoke(user_message)
        else:
            # 普通模式：使用消息列表
            messages = [
                HumanMessage(content=user_message)
            ]
            response = self.agent.invoke({"messages": messages})

        # 提取ST代码
        st_code = self.extract_code_from_response(response)

        return st_code

    def extract_code_from_response(self, response) -> str:
        """
        从LLM响应中提取ST代码

        Args:
            response: LLM响应对象（可能是AIMessage或字符串）

        Returns:
            提取的ST代码
        """
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
            st_code = match.group(1).strip()
        else:
            # 如果没有标记，尝试提取FUNCTION_BLOCK...END_FUNCTION_BLOCK
            pattern_fb = r'(FUNCTION_BLOCK.*?END_FUNCTION_BLOCK)'
            match_fb = re.search(pattern_fb, response_text, re.DOTALL | re.IGNORECASE)

            if match_fb:
                st_code = match_fb.group(1).strip()
            else:
                # 如果还是没有，返回整个响应（可能包含错误信息）
                st_code = response_text.strip()

        return st_code

    def generate_with_properties(self, instruction: str, properties: list) -> tuple:
        """
        生成ST代码并同时考虑需要验证的属性

        Args:
            instruction: 自然语言指令
            properties: 需要验证的属性列表

        Returns:
            (st_code, enhanced_instruction): ST代码和增强的指令
        """
        # 将属性要求加入到指令中
        property_descriptions = []
        for i, prop in enumerate(properties, 1):
            prop_desc = prop.get('property_description', '')
            if prop_desc:
                property_descriptions.append(f"{i}. {prop_desc}")

        if property_descriptions:
            enhanced_instruction = f"""{instruction}

The generated code must satisfy the following properties:
{chr(10).join(property_descriptions)}

Please ensure the ST code is designed to meet all these requirements.
"""
        else:
            enhanced_instruction = instruction

        st_code = self.generate(enhanced_instruction)

        return st_code, enhanced_instruction


if __name__ == "__main__":
    """测试代码生成器"""
    # 简单测试（需要配置config.py）
    try:
        from config import chat_model, openai_api_key, openai_base_url

        llm_config = {
            'model': chat_model,
            'api_key': openai_api_key,
            'base_url': openai_base_url,
            'temperature': 0.1
        }

        generator = CodeGenerator(llm_config=llm_config)

        # 测试案例1: LED控制
        instruction1 = "Create a function block to control an LED. When the button is pressed, toggle the LED state."
        print("=" * 80)
        print(f"Instruction: {instruction1}")
        print("=" * 80)

        code1 = generator.generate(instruction1)
        print(code1)
        print("=" * 80)

        # 测试案例2: 温度控制
        instruction2 = "Create a function block for temperature control. If temperature exceeds 80 degrees, activate the cooling fan."
        print(f"\nInstruction: {instruction2}")
        print("=" * 80)

        code2 = generator.generate(instruction2)
        print(code2)
        print("=" * 80)

    except ImportError as e:
        print(f"Error: Please configure config.py first. {e}")
        print("Skipping tests...")
