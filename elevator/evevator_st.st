
(* ================================================================================
    类型定义：电梯状态枚举
================================================================================ *)

TYPE E_ElevState : (
    IDLE,           (* 状态1：空闲状态 *)
    SELECT_TARGET,  (* 状态2：目标选择状态 *)
    MOVE_UP,        (* 状态3：上行状态 *)
    MOVE_DOWN,      (* 状态4：下行状态 *)
    DOOR_OPENING,   (* 状态5：开门过程 *)
    DOOR_OPEN,      (* 状态6：门打开状态 *)
    DOOR_CLOSING,   (* 状态7：关门过程 *)
    FAULT_STATE     (* 状态8：故障状态 *)
);
END_TYPE;


(* ================================================================================
    主程序：三层电梯控制
================================================================================ *)

PROGRAM Elevator

(* ================================================================================
    变量声明
================================================================================ *)

VAR
    (* ========== 系统输入信号 ========== *)

    (* 呼叫按钮：当乘客按下按钮时为TRUE *)
    Btn1            : BOOL;     (* 1楼呼叫按钮 *)
    Btn2            : BOOL;     (* 2楼呼叫按钮 *)
    Btn3            : BOOL;     (* 3楼呼叫按钮 *)

    (* 楼层限位开关：当电梯到达对应楼层时为TRUE *)
    AtFlr1          : BOOL;     (* 1楼限位开关 *)
    AtFlr2          : BOOL;     (* 2楼限位开关 *)
    AtFlr3          : BOOL;     (* 3楼限位开关 *)

    (* 门控制反馈 *)
    DoorClosedSw    : BOOL;     (* 门关闭限位：门完全关闭时为TRUE *)
    DoorOpenedSw    : BOOL;     (* 门打开限位：门完全打开时为TRUE *)

    (* 安全信号 *)
    Overload        : BOOL;     (* 超载检测：超载时为TRUE *)
    EStop           : BOOL;     (* 急停按钮：按下时为TRUE *)


    (* ========== 系统输出信号 ========== *)

    (* 电机控制 *)
    MotorUp         : BOOL;     (* 电梯上行控制 *)
    MotorDown       : BOOL;     (* 电梯下行控制 *)

    (* 门控制 *)
    DoorOpenCmd     : BOOL;     (* 开门命令 *)
    DoorCloseCmd    : BOOL;     (* 关门命令 *)

    (* 楼层指示灯 *)
    FloorLamp1      : BOOL;     (* 1楼指示灯 *)
    FloorLamp2      : BOOL;     (* 2楼指示灯 *)
    FloorLamp3      : BOOL;     (* 3楼指示灯 *)

    (* 故障信号 *)
    Fault           : BOOL;     (* 故障指示 *)


    (* ========== 内部状态变量 ========== *)

    (* 当前状态 *)
    state           : E_ElevState := IDLE;

    (* 楼层信息 *)
    curFloor        : INT := 0;     (* 当前楼层：1~3，0表示未知 *)
    targetFloor     : INT := 0;     (* 目标楼层 *)

    (* 呼叫队列：用内部变量管理呼叫，而不是直接修改输入信号 *)
    callQueue       : ARRAY[1..3] OF BOOL := [FALSE, FALSE, FALSE];

    (* 定时器 *)
    doorTimer       : TON;      (* 门打开保持计时器 *)
    doorOpenTime    : TIME := T#5s;     (* 门保持打开5秒 *)

    doorTimeoutTimer : TON;     (* 开/关门超时保护计时器 *)
    doorTimeoutTime : TIME := T#10s;    (* 开/关门超时10秒 *)

    moveTimeoutTimer : TON;     (* 上/下行超时保护计时器 *)
    moveTimeoutTime : TIME := T#30s;    (* 上/下行超时30秒 *)

    (* 故障恢复 *)
    estopLatched    : BOOL := FALSE;    (* 急停锁存标志 *)

END_VAR;


(* ================================================================================
    程序主体
================================================================================ *)

BEGIN

(* ================================================================================
    第一步：更新当前楼层和楼层指示灯

    根据楼层限位开关的状态，判断电梯当前所在楼层，并点亮对应的指示灯。
================================================================================ *)

IF AtFlr1 THEN
    curFloor := 1;
ELSIF AtFlr2 THEN
    curFloor := 2;
ELSIF AtFlr3 THEN
    curFloor := 3;
ELSE
    curFloor := 0;  (* 未知楼层 *)
END_IF;

(* 更新楼层指示灯 *)
FloorLamp1 := AtFlr1;
FloorLamp2 := AtFlr2;
FloorLamp3 := AtFlr3;


(* ================================================================================
    第二步：管理呼叫队列

    将输入按钮信号复制到内部呼叫队列，以便在关门后清除对应的请求。
    这样做的好处是：不直接修改输入信号，符合PLC编程规范。
================================================================================ *)

IF Btn1 THEN callQueue[1] := TRUE; END_IF;
IF Btn2 THEN callQueue[2] := TRUE; END_IF;
IF Btn3 THEN callQueue[3] := TRUE; END_IF;


(* ================================================================================
    第三步：安全信号处理（最高优先级）

    如果检测到安全问题（急停或超载），立即停止所有运动，进入故障状态。
    这个检查必须在主状态机之前执行，确保安全信号具有最高优先级。
================================================================================ *)

(* 检测急停信号 *)
IF EStop THEN
    estopLatched := TRUE;
END_IF;

(* 如果存在急停或超载，立即停止所有运动 *)
IF estopLatched OR Overload THEN
    MotorUp      := FALSE;
    MotorDown    := FALSE;
    DoorOpenCmd  := FALSE;
    DoorCloseCmd := FALSE;
    Fault        := TRUE;
    state        := FAULT_STATE;
END_IF;

(* 故障状态的恢复逻辑 *)
IF (state = FAULT_STATE) THEN
    IF (NOT EStop) AND (NOT Overload) AND NOT (callQueue[1] OR callQueue[2] OR callQueue[3]) THEN
        estopLatched := FALSE;
        Fault        := FALSE;
        state        := IDLE;
    END_IF;
    (* 故障态下不再执行主状态机 *)
    RETURN;
END_IF;


(* ================================================================================
    第四步：主状态机

    根据当前状态执行相应的动作，并根据条件转移到下一个状态。
================================================================================ *)

CASE state OF

    (* ========== 状态1：IDLE（空闲） ========== *)
    IDLE:
        (*
            入口条件：电梯已停在某个楼层，门已完全关闭，没有运动中的电机信号

            状态内的动作：
            1. 停止所有电机运动
            2. 停止所有门控制
            3. 根据楼层限位开关更新楼层指示灯

            状态转移条件（按优先级）：
            1. 如果门没有完全关闭，转移到DOOR_CLOSING状态
            2. 如果有任何呼叫请求，转移到SELECT_TARGET状态
            3. 否则保持在IDLE状态
        *)

        (* 停止所有运动 *)
        MotorUp      := FALSE;
        MotorDown    := FALSE;
        DoorOpenCmd  := FALSE;
        DoorCloseCmd := FALSE;

        (* 状态转移逻辑 *)
        IF NOT DoorClosedSw THEN
            (* 优先级1：门没有关闭，尝试关门 *)
            state := DOOR_CLOSING;
        ELSIF (callQueue[1] OR callQueue[2] OR callQueue[3]) THEN
            (* 优先级2：有呼叫请求，进行目标选择 *)
            state := SELECT_TARGET;
        END_IF;
        (* 否则保持在IDLE状态 *)


    (* ========== 状态2：SELECT_TARGET（目标选择） ========== *)
    SELECT_TARGET:
        (*
            入口条件：从IDLE状态转移而来，有至少一个呼叫请求

            状态内的动作：
            根据当前楼层和呼叫请求，选择下一个目标楼层。
            实现"本层优先"和"最近优先"的策略。

            状态转移条件：
            1. 如果目标楼层等于当前楼层，转移到DOOR_OPENING状态
            2. 如果目标楼层大于当前楼层，转移到MOVE_UP状态
            3. 如果目标楼层小于当前楼层，转移到MOVE_DOWN状态
            4. 如果当前楼层未知，进入FAULT_STATE故障状态
        *)

        (* 优先级规则1：本层优先 *)
        IF (curFloor = 1) AND callQueue[1] THEN
            targetFloor := 1;
        ELSIF (curFloor = 2) AND callQueue[2] THEN
            targetFloor := 2;
        ELSIF (curFloor = 3) AND callQueue[3] THEN
            targetFloor := 3;
        ELSE
            (* 优先级规则2：根据当前楼层选择最近的请求 *)
            CASE curFloor OF

                1:  (* 当前在1楼 *)
                    IF callQueue[2] THEN
                        targetFloor := 2;
                    ELSIF callQueue[3] THEN
                        targetFloor := 3;
                    ELSE
                        (* 没有有效请求，回到IDLE *)
                        state := IDLE;
                    END_IF;

                2:  (* 当前在2楼 *)
                    IF callQueue[1] AND NOT callQueue[3] THEN
                        targetFloor := 1;
                    ELSIF callQueue[3] THEN
                        targetFloor := 3;
                    ELSE
                        state := IDLE;
                    END_IF;

                3:  (* 当前在3楼 *)
                    IF callQueue[2] THEN
                        targetFloor := 2;
                    ELSIF callQueue[1] THEN
                        targetFloor := 1;
                    ELSE
                        state := IDLE;
                    END_IF;

                ELSE
                    (* 当前楼层未知，尝试寻找已知楼层 *)
                    IF AtFlr1 THEN
                        curFloor := 1;
                        state := IDLE;
                    ELSIF AtFlr2 THEN
                        curFloor := 2;
                        state := IDLE;
                    ELSIF AtFlr3 THEN
                        curFloor := 3;
                        state := IDLE;
                    ELSE
                        (* 所有限位都未触发，硬件故障 *)
                        Fault := TRUE;
                        state := FAULT_STATE;
                    END_IF;

            END_CASE;
        END_IF;

        (* 根据目标楼层与当前楼层的关系决定下一步动作 *)
        IF targetFloor = curFloor AND curFloor <> 0 THEN
            (* 同层请求，直接打开门 *)
            state := DOOR_OPENING;
        ELSIF (curFloor <> 0) THEN
            IF targetFloor > curFloor THEN
                (* 目标在上方，上行 *)
                state := MOVE_UP;
            ELSIF targetFloor < curFloor THEN
                (* 目标在下方，下行 *)
                state := MOVE_DOWN;
            END_IF;
        END_IF;


    (* ========== 状态3：MOVE_UP（上行） ========== *)
    MOVE_UP:
        (*
            入口条件：从SELECT_TARGET状态转移而来，目标楼层大于当前楼层

            状态内的动作：
            1. 检查安全条件（门关闭、无超载、无急停）
            2. 如果安全条件满足，启动电机上行
            3. 启动运动超时保护计时器

            状态转移条件：
            1. 如果到达目标楼层，转移到DOOR_OPENING状态
            2. 如果运动超过30秒未到达，进入FAULT_STATE故障状态
        *)

        (* 检查安全条件 *)
        IF DoorClosedSw AND (NOT Overload) AND (NOT EStop) THEN
            MotorUp   := TRUE;
            MotorDown := FALSE;
        ELSE
            MotorUp := FALSE;
        END_IF;

        (* 启动运动超时保护计时器 *)
        moveTimeoutTimer(IN := TRUE, PT := moveTimeoutTime);

        (* 检查是否到达目标楼层 *)
        IF (targetFloor = 1 AND AtFlr1) OR
           (targetFloor = 2 AND AtFlr2) OR
           (targetFloor = 3 AND AtFlr3) THEN
            MotorUp := FALSE;
            moveTimeoutTimer(IN := FALSE, PT := moveTimeoutTime);  (* 复位超时计时器 *)
            state := DOOR_OPENING;
        ELSIF moveTimeoutTimer.Q THEN
            (* 运动超时，进入故障状态 *)
            MotorUp := FALSE;
            Fault := TRUE;
            state := FAULT_STATE;
        END_IF;


    (* ========== 状态4：MOVE_DOWN（下行） ========== *)
    MOVE_DOWN:
        (*
            入口条件：从SELECT_TARGET状态转移而来，目标楼层小于当前楼层

            状态内的动作：
            1. 检查安全条件（门关闭、无超载、无急停）
            2. 如果安全条件满足，启动电机下行
            3. 启动运动超时保护计时器

            状态转移条件：
            1. 如果到达目标楼层，转移到DOOR_OPENING状态
            2. 如果运动超过30秒未到达，进入FAULT_STATE故障状态
        *)

        (* 检查安全条件 *)
        IF DoorClosedSw AND (NOT Overload) AND (NOT EStop) THEN
            MotorDown := TRUE;
            MotorUp   := FALSE;
        ELSE
            MotorDown := FALSE;
        END_IF;

        (* 启动运动超时保护计时器 *)
        moveTimeoutTimer(IN := TRUE, PT := moveTimeoutTime);

        (* 检查是否到达目标楼层 *)
        IF (targetFloor = 1 AND AtFlr1) OR
           (targetFloor = 2 AND AtFlr2) OR
           (targetFloor = 3 AND AtFlr3) THEN
            MotorDown := FALSE;
            moveTimeoutTimer(IN := FALSE, PT := moveTimeoutTime);  (* 复位超时计时器 *)
            state := DOOR_OPENING;
        ELSIF moveTimeoutTimer.Q THEN
            (* 运动超时，进入故障状态 *)
            MotorDown := FALSE;
            Fault := TRUE;
            state := FAULT_STATE;
        END_IF;


    (* ========== 状态5：DOOR_OPENING（开门过程） ========== *)
    DOOR_OPENING:
        (*
            入口条件：从MOVE_UP、MOVE_DOWN或SELECT_TARGET状态转移而来

            状态内的动作：
            1. 停止所有电机运动
            2. 发送开门命令
            3. 启动开门超时保护计时器

            状态转移条件：
            1. 如果门完全打开，转移到DOOR_OPEN状态
            2. 如果开门超过10秒未完成，进入FAULT_STATE故障状态
        *)

        (* 停止所有电机运动 *)
        MotorUp      := FALSE;
        MotorDown    := FALSE;

        (* 发送开门命令 *)
        DoorCloseCmd := FALSE;
        DoorOpenCmd  := TRUE;

        (* 启动开门超时保护计时器 *)
        doorTimeoutTimer(IN := TRUE, PT := doorTimeoutTime);

        (* 检查门是否完全打开 *)
        IF DoorOpenedSw THEN
            DoorOpenCmd := FALSE;
            doorTimeoutTimer(IN := FALSE, PT := doorTimeoutTime);  (* 复位超时计时器 *)
            (* 启动门打开保持计时器 *)
            doorTimer(IN := TRUE, PT := doorOpenTime);
            state := DOOR_OPEN;
        ELSIF doorTimeoutTimer.Q THEN
            (* 开门超时，进入故障状态 *)
            Fault := TRUE;
            state := FAULT_STATE;
        END_IF;


    (* ========== 状态6：DOOR_OPEN（门打开） ========== *)
    DOOR_OPEN:
        (*
            入口条件：从DOOR_OPENING状态转移而来，门已完全打开

            状态内的动作：
            1. 保持门打开状态
            2. 启动门保持打开计时器（5秒）

            状态转移条件：
            1. 当门保持打开计时器计时完成（5秒已过），转移到DOOR_CLOSING状态
        *)

        (* 保持门打开 *)
        DoorOpenCmd  := FALSE;  (* 门已打开，无需继续发送命令 *)
        DoorCloseCmd := FALSE;

        (* 启动门保持打开计时器 *)
        doorTimer(IN := TRUE, PT := doorOpenTime);

        (* 检查计时是否完成 *)
        IF doorTimer.Q THEN
            state := DOOR_CLOSING;
        END_IF;


    (* ========== 状态7：DOOR_CLOSING（关门过程） ========== *)
    DOOR_CLOSING:
        (*
            入口条件：从DOOR_OPEN状态转移而来，或从IDLE状态转移而来

            状态内的动作：
            1. 发送关门命令
            2. 启动关门超时保护计时器

            状态转移条件：
            1. 如果门完全关闭，清除本层请求，检查是否还有其他请求
               - 如果有其他请求，转移到SELECT_TARGET状态
               - 否则转移到IDLE状态
            2. 如果关门超过10秒未完成，进入FAULT_STATE故障状态
        *)

        (* 发送关门命令 *)
        DoorOpenCmd  := FALSE;
        DoorCloseCmd := TRUE;

        (* 启动关门超时保护计时器 *)
        doorTimeoutTimer(IN := TRUE, PT := doorTimeoutTime);

        (* 检查门是否完全关闭 *)
        IF DoorClosedSw THEN
            DoorCloseCmd := FALSE;
            doorTimeoutTimer(IN := FALSE, PT := doorTimeoutTime);  (* 复位超时计时器 *)

            (* 清除本层的呼叫请求 *)
            CASE curFloor OF
                1: callQueue[1] := FALSE;
                2: callQueue[2] := FALSE;
                3: callQueue[3] := FALSE;
            END_CASE;

            (* 检查是否还有其他请求 *)
            IF (callQueue[1] OR callQueue[2] OR callQueue[3]) THEN
                state := SELECT_TARGET;
            ELSE
                state := IDLE;
            END_IF;
        ELSIF doorTimeoutTimer.Q THEN
            (* 关门超时，进入故障状态 *)
            Fault := TRUE;
            state := FAULT_STATE;
        END_IF;


    (* ========== 状态8：FAULT_STATE（故障） ========== *)
    FAULT_STATE:
        (*
            入口条件：检测到安全问题或硬件故障

            状态内的动作：
            1. 停止所有电机运动
            2. 停止所有门控制
            3. 设置故障信号

            故障恢复条件（同时满足以下所有条件）：
            1. 急停信号已释放（EStop = FALSE）
            2. 超载状态已解除（Overload = FALSE）
            3. 所有呼叫请求已清除（callQueue[1..3] = FALSE）

            如果以上条件都满足，则转移到IDLE状态
        *)

        (* 停止所有运动 *)
        MotorUp      := FALSE;
        MotorDown    := FALSE;
        DoorOpenCmd  := FALSE;
        DoorCloseCmd := FALSE;
        Fault        := TRUE;

        (* 故障恢复逻辑已在第三步中处理 *)


END_CASE;

END_PROGRAM;


