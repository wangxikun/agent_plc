

## 示例 1: 传送带控制逻辑 (ConveyorControl_FB)

**自然语言输入**: 如果急停按钮被按下，或者系统故障发生，或者停止按钮被按下，就立即停止传送带。否则，如果启动按钮被按下，则启动传送带。

**功能**: 实现带安全互锁的启停逻辑，安全信号具有最高优先级。


FUNCTION_BLOCK ConveyorControl_FB
(*
    功能块说明：
    实现传送带的启停控制。安全信号（急停、故障、停止）具有最高优先级。
*)

// --- 输入变量 (VAR_INPUT) ---
VAR_INPUT
    Start_Button    : BOOL; // 启动按钮信号
    Stop_Button     : BOOL; // 停止按钮信号
    Emergency_Stop  : BOOL; // 急停信号 (安全输入)
    System_Fault    : BOOL; // 系统故障信号 (安全输入)
END_VAR

// --- 输出变量 (VAR_OUTPUT) ---
VAR_OUTPUT
    Conveyor_Run    : BOOL; // 传送带运行状态 (输出到电机接触器)
END_VAR

// --- 程序代码实现 ---
BEGIN

    // 1. 安全和停止逻辑 (最高优先级)
    // 只要任何一个安全或停止条件满足，就强制停止传送带。
    IF "Emergency_Stop" OR "System_Fault" OR "Stop_Button" THEN
        "Conveyor_Run" := FALSE;

    // 2. 启动逻辑 (只有在不满足停止条件时才执行)
    ELSIF "Start_Button" THEN
        "Conveyor_Run" := TRUE;

    END_IF;

END_FUNCTION_BLOCK
```

---

## 示例 2: 液位控制与排水延时 (LevelControl_FB)

**自然语言输入**: 当液位（Liquid_Level）超过95.0时，立即关闭进水阀（Inlet_Valve）。同时，启动一个延时5分钟的定时器，5分钟后启动排水泵（Drain_Pump）。

**功能**: 实现高液位报警和延时排水功能。


FUNCTION_BLOCK LevelControl_FB
(*
    功能块说明：
    监控液位，实现高液位时关闭进水阀，并延时启动排水泵。
*)

// --- 输入变量 (VAR_INPUT) ---
VAR_INPUT
    Liquid_Level    : REAL; // 实时液位值 (例如0.0到100.0)
END_VAR

// --- 输出变量 (VAR_OUTPUT) ---
VAR_OUTPUT
    Inlet_Valve     : BOOL; // 进水阀控制信号 (TRUE = 打开)
    Drain_Pump      : BOOL; // 排水泵控制信号 (TRUE = 运行)
END_VAR

// --- 内部静态变量 (VAR) ---
VAR
    // 标志位：用于锁存高液位状态，作为定时器的启动条件
    High_Level_Reached : BOOL;
    // 关断延时定时器实例
    Drain_Delay_Timer  : TON;
END_VAR

// --- 程序代码实现 ---
BEGIN

    // 1. 液位超限判断和进水阀控制
    IF "Liquid_Level" > 95.0 THEN
        "Inlet_Valve" := FALSE;     // 立即关闭进水阀
        "High_Level_Reached" := TRUE; // 锁存高液位状态，启动定时器
    ELSE
        // 注意：这里需要额外的逻辑来重新打开进水阀，
        // 否则一旦关闭，将永远不会打开。
        // 为了简化，我们只处理高液位逻辑。
        "High_Level_Reached" := FALSE; // 液位恢复正常，复位标志
    END_IF;

    // 2. 调用延时定时器
    "Drain_Delay_Timer"(IN := "High_Level_Reached", // 当高液位标志为TRUE时开始计时
                        PT := T#5m);              // 预设时间5分钟

    // 3. 控制排水泵
    // 当定时器计时完成 (.Q 为 TRUE) 时，启动排水泵
    IF "Drain_Delay_Timer".Q THEN
        "Drain_Pump" := TRUE;
    ELSE
        "Drain_Pump" := FALSE;
    END_IF;

END_FUNCTION_BLOCK
```

---

## 示例 3: 瓶子计数逻辑 (BottleCounter_FB)

**自然语言输入**: (上升沿触发) 每当瓶子检测传感器检测到一个瓶子（即信号从无到有），就让瓶子计数器加1。如果按下了计数复位按钮，就将计数器清零。

**功能**: 实现基于上升沿的精确计数和手动复位。


FUNCTION_BLOCK BottleCounter_FB
(*
    功能块说明：
    使用上升沿检测器和计数器实现瓶子计数，并提供手动复位功能。
*)

// --- 输入变量 (VAR_INPUT) ---
VAR_INPUT
    Bottle_Sensor   : BOOL; // 瓶子传感器信号 (TRUE = 检测到瓶子)
    Count_Reset     : BOOL; // 计数复位按钮信号
END_VAR

// --- 输出变量 (VAR_OUTPUT) ---
VAR_OUTPUT
    Bottle_Count    : INT;  // 瓶子计数器的当前值
END_VAR

// --- 内部静态变量 (VAR) ---
VAR
    // 上升沿检测器实例
    Bottle_Sensor_R_TRIG : R_TRIG;
END_VAR

// --- 程序代码实现 ---
BEGIN

    // 1. 调用上升沿检测器
    // 持续监视 Bottle_Sensor 信号
    "Bottle_Sensor_R_TRIG"(CLK := "Bottle_Sensor");

    // 2. 计数逻辑
    // 只有在上升沿检测器输出 .Q 为 TRUE (仅持续一个扫描周期) 时，才执行加一操作。
    IF "Bottle_Sensor_R_TRIG".Q THEN
        "Bottle_Count" := "Bottle_Count" + 1;
    END_IF;

    // 3. 复位逻辑 (最高优先级)
    // 如果复位按钮被按下，则将计数器清零。
    IF "Count_Reset" THEN
        "Bottle_Count" := 0;
    END_IF;

END_FUNCTION_BLOCK
```

---

## 示例 4: 主电机启停与安全门互锁 (MainMotorControl_FB)

**自然语言输入**: 当操作员按下启动按钮（Start_Button），并且安全门（Safety_Door_Closed）是关闭状态时，启动主电机（Main_Motor）。否则，就让主电机保持停止。

**功能**: 实现带安全门互锁的简单启停控制。


FUNCTION_BLOCK MainMotorControl_FB
(*
    功能块说明：
    控制主电机启停，必须满足安全门关闭的条件才能启动。
*)

// --- 输入变量 (VAR_INPUT) ---
VAR_INPUT
    Start_Button        : BOOL; // 启动按钮信号
    Safety_Door_Closed  : BOOL; // 安全门关闭信号 (TRUE = 关闭)
END_VAR

// --- 输出变量 (VAR_OUTPUT) ---
VAR_OUTPUT
    Main_Motor          : BOOL; // 主电机控制信号
END_VAR

// --- 程序代码实现 ---
BEGIN

    // 启动条件：启动按钮按下 AND 安全门关闭
    IF "Start_Button" AND "Safety_Door_Closed" THEN
        "Main_Motor" := TRUE;

    // 停止条件：否则，电机停止
    ELSE
        "Main_Motor" := FALSE;

    END_IF;

END_FUNCTION_BLOCK
```

---

## 示例 5: 加热器延时启动 (HeaterDelayStart_FB)

**自然语言输入**: (TON定时器) 按下加热启动按钮（Heating_Start）后，等待10秒钟预热，然后才启动加热器（Heater_On）。

**功能**: 实现接通延时启动。


FUNCTION_BLOCK HeaterDelayStart_FB
(*
    功能块说明：
    实现加热器的延时启动，用于预热或安全检查。
*)

// --- 输入变量 (VAR_INPUT) ---
VAR_INPUT
    Heating_Start   : BOOL; // 加热启动请求信号
END_VAR

// --- 输出变量 (VAR_OUTPUT) ---
VAR_OUTPUT
    Heater_On       : BOOL; // 加热器运行状态
END_VAR

// --- 内部静态变量 (VAR) ---
VAR
    // 接通延时定时器实例
    Heating_Delay_Timer : TON;
END_VAR

// --- 程序代码实现 ---
BEGIN

    // 1. 调用TON定时器
    "Heating_Delay_Timer"(IN := "Heating_Start", // 启动条件
                          PT := T#10s);          // 预设时间10秒

    // 2. 控制加热器 (只有当定时器计时完成时才启动)
    IF "Heating_Delay_Timer".Q THEN
        "Heater_On" := TRUE;
    ELSE
        "Heater_On" := FALSE;
    END_IF;

END_FUNCTION_BLOCK
```

---

## 示例 6: 风扇关断延时 (FanDelayStop_FB)

**自然语言输入**: 当关闭风扇开关后，让风扇继续运行30秒以进行散热，然后自动停止。

**功能**: 实现关断延时停止（散热功能）。


FUNCTION_BLOCK FanDelayStop_FB
(*
    功能块说明：
    实现风扇的关断延时停止，用于散热或排风。
    (此功能块基于您文件中的完整结构进行优化和注释)
*)

// --- 输入变量 (VAR_INPUT) ---
VAR_INPUT
    Fan_Switch : BOOL; // 外部的风扇开关信号 (TRUE = 打开)
END_VAR

// --- 输出变量 (VAR_OUTPUT) ---
VAR_OUTPUT
    Fan_Motor : BOOL; // 输出到风扇电机的控制信号
END_VAR

// --- 内部静态变量 (VAR) ---
VAR
    // 关断延时定时器实例
    Fan_Stop_Delay_Timer : TOF;
END_VAR

// --- 程序代码实现 ---
BEGIN

    // 1. 调用TOF定时器
    // 当 IN 端从 TRUE 变为 FALSE 时，定时器开始计时。
    "Fan_Stop_Delay_Timer"(IN := "Fan_Switch",
                          PT := T#30s);

    // 2. 将定时器的输出Q直接赋给风扇电机
    // Q 的状态：
    // - Fan_Switch = TRUE: Q 立即为 TRUE (风扇运行)
    // - Fan_Switch = FALSE: Q 保持 TRUE 30秒后才变为 FALSE (延时停止)
    "Fan_Motor" := "Fan_Stop_Delay_Timer".Q;

END_FUNCTION_BLOCK
```

## 示例 7: 批次计数与完成报警 (BatchCounter_FB)

**自然语言输入**: 使用计数器（CTU）计算产品数量。每当产品传感器（Product_Pulse）出现脉冲时计数加一。当达到预设的批次数量（Batch_Size）时，触发批次完成信号（Batch_Done）。按下复位按钮（Reset_Count）时，计数器清零。

**功能**: 实现基于脉冲的批次计数和完成状态输出。


FUNCTION_BLOCK BatchCounter_FB
(*
    功能块说明：
    实现一个可复用的批次计数器。
*)

// --- 输入变量 (VAR_INPUT) ---
VAR_INPUT
    Product_Pulse   : BOOL; // 计数脉冲信号 (通常来自上升沿)
    Reset_Count     : BOOL; // 计数复位信号
    Batch_Size      : INT;  // 预设的批次数量 (PV)
END_VAR

// --- 输出变量 (VAR_OUTPUT) ---
VAR_OUTPUT
    Current_Count   : INT;  // 当前计数值 (CV)
    Batch_Done      : BOOL; // 批次完成信号 (Q)
END_VAR

// --- 内部静态变量 (VAR) ---
VAR
    // CTU 计数器实例
    Batch_CTU : CTU;
END_VAR

// --- 程序代码实现 ---
BEGIN

    // 1. 调用 CTU 计数器
    // CU: 计数输入 (Product_Pulse)
    // R: 复位输入 (Reset_Count)
    // PV: 预设值 (Batch_Size)
    // CV: 当前值 (Current_Count)
    // Q: 完成输出 (Batch_Done)
    "Batch_CTU"(CU := "Product_Pulse",
                R  := "Reset_Count",
                PV := "Batch_Size",
                CV => "Current_Count",
                Q  => "Batch_Done");

    // 注：在西门子TIA Portal中，CTU指令通常直接在程序中调用，
    // 它的输出 Q 和 CV 可以直接映射到 VAR_OUTPUT 变量。

END_FUNCTION_BLOCK
```

---

## 示例 8: 简单的三步顺序控制 (ThreeStepSequence_FB)

**自然语言输入**: 实现一个三步顺序控制：第一步（Step 10）等待启动信号（Start_Request）。收到信号后，进入第二步（Step 20），运行电机（Motor_Run）10秒。10秒后，进入第三步（Step 30），打开阀门（Valve_Open）5秒。5秒后，返回第一步（Step 10）等待下一个循环。

**功能**: 实现最常见的顺序控制逻辑（状态机）。


FUNCTION_BLOCK ThreeStepSequence_FB
(*
    功能块说明：
    实现一个简单的三步状态机，用于顺序控制。
*)

// --- 输入变量 (VAR_INPUT) ---
VAR_INPUT
    Start_Request   : BOOL; // 启动循环请求
END_VAR

// --- 输出变量 (VAR_OUTPUT) ---
VAR_OUTPUT
    Motor_Run       : BOOL; // 电机运行输出
    Valve_Open      : BOOL; // 阀门打开输出
END_VAR

// --- 内部静态变量 (VAR) ---
VAR
    Current_Step    : INT := 10; // 当前状态编号，初始为10
    Step_Timer      : TON;       // 步骤计时器
END_VAR

// --- 程序代码实现 ---
BEGIN

    // 默认关闭所有输出，防止在状态切换瞬间出现意外
    "Motor_Run" := FALSE;
    "Valve_Open" := FALSE;

    // 调用步骤计时器 (IN端由CASE语句内部控制)
    "Step_Timer"(PT := T#0s); // PT 在CASE内部赋值

    // 状态机核心逻辑
    CASE "Current_Step" OF

        10: // 步骤 10: 空闲/等待启动
            IF "Start_Request" THEN
                "Current_Step" := 20; // 满足条件，跳转到下一步
            END_IF;

        20: // 步骤 20: 运行电机 10 秒
            "Motor_Run" := TRUE;
            "Step_Timer"(IN := TRUE, PT := T#10s); // 启动计时器
            IF "Step_Timer".Q THEN
                "Current_Step" := 30; // 计时完成，跳转到下一步
            END_IF;

        30: // 步骤 30: 打开阀门 5 秒
            "Valve_Open" := TRUE;
            "Step_Timer"(IN := TRUE, PT := T#5s); // 启动计时器
            IF "Step_Timer".Q THEN
                "Current_Step" := 10; // 计时完成，返回空闲状态
            END_IF;

    ELSE // 默认安全状态
        "Current_Step" := 10;

    END_CASE;

END_FUNCTION_BLOCK
```



## 示例 9: 模拟量数据缩放 (ScaleAnalog_FC)

**自然语言输入**: 将PLC的原始模拟量输入值（Raw_Value），从0到27648的范围，线性缩放到0.0到100.0的工程单位（Engineering_Value）。

**功能**: 实现模拟量数据的线性缩放（这是一个典型的 **FUNCTION** 示例）。


FUNCTION ScaleAnalog_FC : REAL
(*
    函数说明：
    将模拟量原始值（0-27648）线性缩放到工程值（0.0-100.0）。
    这是一个纯粹的数学计算，不依赖内部记忆，因此使用 FUNCTION。
*)

// --- 输入变量 (VAR_INPUT) ---
VAR_INPUT
    Raw_Value   : INT;  // 原始模拟量输入值 (例如 0 到 27648)
END_VAR

// --- 临时变量 (VAR) ---
VAR
    // 临时变量用于存储计算结果
    Scaled_Value : REAL;
END_VAR

// --- 程序代码实现 ---
BEGIN

    // 线性缩放公式：
    // 工程值 = (原始值 - 原始最小值) * (工程最大值 - 工程最小值) / (原始最大值 - 原始最小值) + 工程最小值

    // 1. 将原始值转换为实数 (REAL) 进行计算
    Scaled_Value := INT_TO_REAL("Raw_Value");

    // 2. 执行缩放计算
    // (Scaled_Value - 0) * (100.0 - 0.0) / (27648.0 - 0.0) + 0.0
    Scaled_Value := Scaled_Value * 100.0 / 27648.0;

    // 3. 将结果赋给函数名 (即函数的返回值)
    ScaleAnalog_FC := Scaled_Value;

END_FUNCTION
