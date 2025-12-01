"""
ST Code Parser - 解析IEC-61131-3 Structured Text代码
提取变量定义、控制流结构等信息，用于动画演示
"""

import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, field


@dataclass
class Variable:
    """变量定义"""
    name: str
    var_type: str  # BOOL, INT, REAL等
    var_class: str  # INPUT, OUTPUT, VAR
    initial_value: Any = None

    def __repr__(self):
        return f"{self.name}: {self.var_type} = {self.initial_value}"


@dataclass
class STProgram:
    """ST程序结构"""
    name: str = ""
    inputs: List[Variable] = field(default_factory=list)
    outputs: List[Variable] = field(default_factory=list)
    internals: List[Variable] = field(default_factory=list)
    code_lines: List[str] = field(default_factory=list)
    raw_code: str = ""

    def get_all_variables(self) -> Dict[str, Variable]:
        """获取所有变量的字典"""
        all_vars = {}
        for var in self.inputs + self.outputs + self.internals:
            all_vars[var.name] = var
        return all_vars


class STParser:
    """ST代码解析器"""

    def __init__(self):
        self.program = STProgram()

    def parse(self, st_code: str) -> STProgram:
        """解析ST代码"""
        self.program = STProgram()
        self.program.raw_code = st_code

        # 提取FUNCTION_BLOCK名称
        self._extract_program_name(st_code)

        # 提取变量定义
        self._extract_variables(st_code)

        # 提取代码行
        self._extract_code_lines(st_code)

        return self.program

    def _extract_program_name(self, st_code: str):
        """提取程序名称"""
        match = re.search(r'FUNCTION_BLOCK\s+(\w+)', st_code, re.IGNORECASE)
        if match:
            self.program.name = match.group(1)

    def _extract_variables(self, st_code: str):
        """提取变量定义"""
        # 提取VAR_INPUT段
        self._extract_var_section(st_code, 'VAR_INPUT', 'INPUT')

        # 提取VAR_OUTPUT段
        self._extract_var_section(st_code, 'VAR_OUTPUT', 'OUTPUT')

        # 提取VAR段（内部变量）
        self._extract_var_section(st_code, r'VAR\b(?!_)', 'VAR')

    def _extract_var_section(self, st_code: str, section_pattern: str, var_class: str):
        """提取指定的变量段"""
        # 匹配变量段
        pattern = rf'{section_pattern}\s*(.*?)\s*END_VAR'
        match = re.search(pattern, st_code, re.IGNORECASE | re.DOTALL)

        if not match:
            return

        var_section = match.group(1)

        # 解析每个变量声明
        # 支持格式: variable_name : TYPE; 或 variable_name : TYPE := initial_value;
        var_pattern = r'(\w+)\s*:\s*(\w+)(?:\s*:=\s*([^;]+))?'

        for line in var_section.split('\n'):
            # 移除注释
            line = re.sub(r'\(\*.*?\*\)', '', line)
            line = line.strip()

            if not line:
                continue

            var_match = re.search(var_pattern, line)
            if var_match:
                var_name = var_match.group(1)
                var_type = var_match.group(2)
                initial_value = var_match.group(3)

                # 解析初始值
                if initial_value:
                    initial_value = self._parse_value(initial_value.strip(), var_type)
                else:
                    initial_value = self._get_default_value(var_type)

                var = Variable(
                    name=var_name,
                    var_type=var_type,
                    var_class=var_class,
                    initial_value=initial_value
                )

                if var_class == 'INPUT':
                    self.program.inputs.append(var)
                elif var_class == 'OUTPUT':
                    self.program.outputs.append(var)
                else:
                    self.program.internals.append(var)

    def _parse_value(self, value_str: str, var_type: str) -> Any:
        """解析变量值"""
        value_str = value_str.strip()

        if var_type == 'BOOL':
            return value_str.upper() in ['TRUE', '1']
        elif var_type in ['INT', 'DINT', 'SINT', 'LINT']:
            try:
                return int(value_str)
            except:
                return 0
        elif var_type in ['REAL', 'LREAL']:
            try:
                return float(value_str)
            except:
                return 0.0
        else:
            return value_str

    def _get_default_value(self, var_type: str) -> Any:
        """获取类型的默认值"""
        if var_type == 'BOOL':
            return False
        elif var_type in ['INT', 'DINT', 'SINT', 'LINT']:
            return 0
        elif var_type in ['REAL', 'LREAL']:
            return 0.0
        else:
            return None

    def _extract_code_lines(self, st_code: str):
        """提取代码行"""
        # 找到最后一个END_VAR之后的代码
        last_end_var = st_code.rfind('END_VAR')
        if last_end_var == -1:
            return

        # 找到END_FUNCTION_BLOCK
        end_fb = st_code.rfind('END_FUNCTION_BLOCK')
        if end_fb == -1:
            code_section = st_code[last_end_var + 7:]
        else:
            code_section = st_code[last_end_var + 7:end_fb]

        # 分割成行，移除注释和空行
        lines = code_section.split('\n')
        cleaned_lines = []

        for i, line in enumerate(lines):
            # 移除注释
            line = re.sub(r'\(\*.*?\*\)', '', line)
            line = line.strip()

            # 跳过空行
            if not line:
                continue

            cleaned_lines.append({
                'line_num': i + 1,
                'code': line,
                'original': lines[i]
            })

        self.program.code_lines = cleaned_lines

    def print_program_structure(self):
        """打印程序结构（用于调试）"""
        print(f"=== Program: {self.program.name} ===\n")

        print("Inputs:")
        for var in self.program.inputs:
            print(f"  {var}")

        print("\nOutputs:")
        for var in self.program.outputs:
            print(f"  {var}")

        print("\nInternal Variables:")
        for var in self.program.internals:
            print(f"  {var}")

        print("\nCode Lines:")
        for line in self.program.code_lines:
            print(f"  {line['line_num']}: {line['code']}")


# 测试代码
if __name__ == "__main__":
    # 测试示例
    test_code = """
    FUNCTION_BLOCK MotorControl
    VAR_INPUT
        start_button : BOOL;
        stop_button : BOOL;
        temperature : REAL;
    END_VAR

    VAR_OUTPUT
        motor : BOOL;
        alarm : BOOL;
    END_VAR

    VAR
        running_time : INT := 0;
        overheat : BOOL := FALSE;
    END_VAR

    (* Main logic *)
    IF start_button AND NOT overheat THEN
        motor := TRUE;
    END_IF;

    IF stop_button THEN
        motor := FALSE;
        running_time := 0;
    END_IF;

    IF temperature > 80.0 THEN
        overheat := TRUE;
        alarm := TRUE;
        motor := FALSE;
    END_IF;

    IF motor THEN
        running_time := running_time + 1;
    END_IF;

    END_FUNCTION_BLOCK
    """

    parser = STParser()
    program = parser.parse(test_code)
    parser.print_program_structure()
