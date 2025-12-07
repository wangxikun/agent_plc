"""
ST Code Simulator - ST代码执行模拟器
模拟ST代码的逐步执行，记录每一步的状态变化
"""

import re
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field
from copy import deepcopy
from src.st_parser import STParser, STProgram, Variable


@dataclass
class ExecutionStep:
    """执行步骤"""
    step_num: int
    line_index: int  # 当前执行的代码行索引
    code_line: str  # 当前执行的代码
    variables: Dict[str, Any]  # 当前变量状态
    description: str = ""  # 执行描述
    changed_vars: List[str] = field(default_factory=list)  # 本步改变的变量


@dataclass
class SimulationResult:
    """模拟执行结果"""
    steps: List[ExecutionStep] = field(default_factory=list)
    final_variables: Dict[str, Any] = field(default_factory=dict)
    total_steps: int = 0
    success: bool = True
    error_message: str = ""


class STSimulator:
    """ST代码执行模拟器"""

    def __init__(self, program: STProgram):
        self.program = program
        self.variables: Dict[str, Any] = {}
        self.steps: List[ExecutionStep] = []
        self.current_step = 0

        # 嵌套IF分支控制状态 - 使用栈结构支持嵌套
        self.if_stack: List[Dict[str, bool]] = []  # 每层IF的状态栈
        # 每个栈元素包含: {'branch_taken': bool, 'skip_until_next': bool}

    def initialize_variables(self, input_values: Dict[str, Any] = None):
        """初始化变量"""
        self.variables = {}

        # 初始化所有变量为默认值
        for var in self.program.inputs + self.program.outputs + self.program.internals:
            self.variables[var.name] = var.initial_value

        # 设置输入值
        if input_values:
            for name, value in input_values.items():
                if name in self.variables:
                    self.variables[name] = value

    def simulate(self, input_values: Dict[str, Any] = None, max_cycles: int = 1) -> SimulationResult:
        """
        模拟执行ST代码

        Args:
            input_values: 输入变量的值
            max_cycles: 最大循环次数（PLC通常循环执行）
        """
        result = SimulationResult()
        self.steps = []
        self.current_step = 0

        try:
            # 初始化变量
            self.initialize_variables(input_values)

            # 记录初始状态
            initial_step = ExecutionStep(
                step_num=0,
                line_index=-1,
                code_line="[INITIALIZATION]",
                variables=deepcopy(self.variables),
                description="初始化变量"
            )
            self.steps.append(initial_step)

            # 模拟执行多个扫描周期
            for cycle in range(max_cycles):
                self._execute_one_cycle(cycle)

            result.steps = self.steps
            result.final_variables = self.variables
            result.total_steps = len(self.steps)
            result.success = True

        except Exception as e:
            result.success = False
            result.error_message = str(e)

        return result

    def _execute_one_cycle(self, cycle_num: int):
        """执行一个扫描周期"""
        code_lines = self.program.code_lines

        # 重置分支控制状态 - 清空栈
        self.if_stack = []

        for i, line_info in enumerate(code_lines):
            code = line_info['code']
            code_upper = code.strip().upper()

            # 检查是否应该跳过这一行
            if self._should_skip_line(code_upper):
                continue

            self.current_step += 1

            # 执行前的变量状态
            prev_vars = deepcopy(self.variables)

            # 执行代码行
            description = self._execute_line(code)

            # 检测变化的变量
            changed_vars = []
            for var_name, value in self.variables.items():
                if prev_vars.get(var_name) != value:
                    changed_vars.append(var_name)

            # 记录执行步骤
            step = ExecutionStep(
                step_num=self.current_step,
                line_index=i,
                code_line=code,
                variables=deepcopy(self.variables),
                description=description,
                changed_vars=changed_vars
            )
            self.steps.append(step)

    def _should_skip_line(self, code_upper: str) -> bool:
        """
        判断是否应该跳过当前行
        实现嵌套IF-ELSIF-ELSE的分支控制逻辑
        """
        # 遇到END_IF，弹出当前IF层的状态
        if code_upper.startswith('END_IF'):
            if self.if_stack:
                self.if_stack.pop()
            return False  # END_IF本身不跳过

        # 遇到ELSIF或ELSE，不跳过（让_execute_line处理）
        if code_upper.startswith('ELSIF') or code_upper.startswith('ELSE'):
            # 重置当前层的skip标志
            if self.if_stack:
                self.if_stack[-1]['skip_until_next'] = False
            return False

        # 检查是否需要跳过当前行
        # 只要有任何一层IF需要跳过，就跳过这一行
        for if_state in self.if_stack:
            if if_state['skip_until_next']:
                return True

        return False

    def _execute_line(self, code: str) -> str:
        """执行单行代码"""
        code = code.strip()

        # 跳过空行和注释
        if not code or code.startswith('(*'):
            return "跳过注释或空行"

        # 处理赋值语句
        if ':=' in code:
            return self._execute_assignment(code)

        # 处理IF语句
        if code.upper().startswith('IF'):
            return self._execute_if(code)

        # 处理ELSIF
        if code.upper().startswith('ELSIF'):
            return self._execute_elsif(code)

        # 处理ELSE
        if code.upper().startswith('ELSE'):
            if not self.if_stack:
                return "ELSE语句错误：没有对应的IF"

            # 获取当前IF层的状态
            current_if = self.if_stack[-1]

            if current_if['branch_taken']:
                # 前面的分支已经执行，跳过ELSE块
                current_if['skip_until_next'] = True
                return "跳过ELSE分支（前面的分支已执行）"
            else:
                # 执行ELSE分支
                current_if['branch_taken'] = True
                current_if['skip_until_next'] = False
                return "进入ELSE分支"

        # 处理END_IF
        if code.upper().startswith('END_IF'):
            return "结束IF语句"

        # 其他语句
        return f"执行: {code}"

    def _execute_assignment(self, code: str) -> str:
        """执行赋值语句"""
        # 解析赋值语句: variable := expression;
        match = re.match(r'(\w+)\s*:=\s*(.+?);?$', code)
        if not match:
            return f"无法解析赋值语句: {code}"

        var_name = match.group(1)
        expression = match.group(2).strip().rstrip(';')

        # 计算表达式
        try:
            value = self._evaluate_expression(expression)
            old_value = self.variables.get(var_name)
            self.variables[var_name] = value
            return f"赋值: {var_name} = {value} (原值: {old_value})"
        except Exception as e:
            return f"赋值失败: {e}"

    def _execute_if(self, code: str) -> str:
        """执行IF语句"""
        # 解析IF条件: IF condition THEN
        match = re.match(r'IF\s+(.+?)\s+THEN', code, re.IGNORECASE)
        if not match:
            return f"无法解析IF语句: {code}"

        condition = match.group(1).strip()

        try:
            result = self._evaluate_expression(condition)

            # 压入新的IF状态到栈
            if_state = {
                'branch_taken': result,  # IF条件是否成立
                'skip_until_next': not result  # 如果条件不成立，跳过IF块
            }
            self.if_stack.append(if_state)

            return f"IF条件: {condition} = {result}"
        except Exception as e:
            return f"IF条件评估失败: {e}"

    def _execute_elsif(self, code: str) -> str:
        """执行ELSIF语句"""
        if not self.if_stack:
            return "ELSIF语句错误：没有对应的IF"

        # 获取当前IF层的状态
        current_if = self.if_stack[-1]

        # 如果已经执行了某个分支，跳过所有后续分支
        if current_if['branch_taken']:
            current_if['skip_until_next'] = True
            return "跳过ELSIF分支（前面的分支已执行）"

        match = re.match(r'ELSIF\s+(.+?)\s+THEN', code, re.IGNORECASE)
        if not match:
            return f"无法解析ELSIF语句: {code}"

        condition = match.group(1).strip()

        try:
            result = self._evaluate_expression(condition)

            if result:
                # ELSIF条件成立，执行ELSIF块内的代码
                current_if['branch_taken'] = True
                current_if['skip_until_next'] = False
            else:
                # ELSIF条件不成立，跳过ELSIF块内的代码
                current_if['skip_until_next'] = True

            return f"ELSIF条件: {condition} = {result}"
        except Exception as e:
            return f"ELSIF条件评估失败: {e}"

    def _evaluate_expression(self, expr: str) -> Any:
        """
        计算表达式
        支持: 变量名, 布尔值, 数字, 比较运算, 逻辑运算, 算术运算
        """
        expr = expr.strip()

        # 替换ST关键字为Python关键字
        expr = self._convert_st_to_python(expr)

        # 替换变量名为实际值
        expr = self._replace_variables(expr)

        # 使用eval计算（注意：在生产环境中应该使用更安全的方法）
        try:
            result = eval(expr, {"__builtins__": {}}, {})
            return result
        except Exception as e:
            raise ValueError(f"无法计算表达式 '{expr}': {e}")

    def _convert_st_to_python(self, expr: str) -> str:
        """将ST表达式转换为Python表达式"""
        # TRUE/FALSE -> True/False
        expr = re.sub(r'\bTRUE\b', 'True', expr, flags=re.IGNORECASE)
        expr = re.sub(r'\bFALSE\b', 'False', expr, flags=re.IGNORECASE)

        # AND -> and
        expr = re.sub(r'\bAND\b', 'and', expr, flags=re.IGNORECASE)

        # OR -> or
        expr = re.sub(r'\bOR\b', 'or', expr, flags=re.IGNORECASE)

        # NOT -> not
        expr = re.sub(r'\bNOT\b', 'not', expr, flags=re.IGNORECASE)

        # MOD -> %
        expr = re.sub(r'\bMOD\b', '%', expr, flags=re.IGNORECASE)

        return expr

    def _replace_variables(self, expr: str) -> str:
        """替换变量名为实际值"""
        # 找到所有可能的变量名
        var_names = re.findall(r'\b[a-zA-Z_]\w*\b', expr)

        for var_name in var_names:
            # 跳过Python关键字
            if var_name in ['True', 'False', 'and', 'or', 'not']:
                continue

            # 替换变量
            if var_name in self.variables:
                value = self.variables[var_name]

                # 根据类型格式化值
                if isinstance(value, bool):
                    value_str = 'True' if value else 'False'
                elif isinstance(value, str):
                    value_str = f"'{value}'"
                else:
                    value_str = str(value)

                # 使用边界匹配替换，避免部分匹配
                expr = re.sub(rf'\b{var_name}\b', value_str, expr)

        return expr


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

    # 解析代码
    parser = STParser()
    program = parser.parse(test_code)

    # 创建模拟器
    simulator = STSimulator(program)

    # 测试场景1: 按下启动按钮
    print("=== 场景1: 按下启动按钮 ===")
    result = simulator.simulate(input_values={
        'start_button': True,
        'stop_button': False,
        'temperature': 25.0
    })

    for step in result.steps:
        if step.changed_vars:
            print(f"Step {step.step_num}: {step.description}")
            print(f"  Changed: {step.changed_vars}")
            print(f"  Variables: {step.variables}")
            print()

    # 测试场景2: 温度过高
    print("\n=== 场景2: 温度过高 ===")
    result = simulator.simulate(input_values={
        'start_button': True,
        'stop_button': False,
        'temperature': 85.0
    })

    for step in result.steps:
        if step.changed_vars:
            print(f"Step {step.step_num}: {step.description}")
            print(f"  Changed: {step.changed_vars}")
            print(f"  Variables: {step.variables}")
            print()
