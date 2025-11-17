PROGRAM TemperatureControl
VAR
    (* 输入变量 *)
    temperature : INT;      (* 温度传感器值 (0.01度精度) *)
    humidity : INT;         (* 湿度传感器值 (0.01%精度) *)
    manual_mode : BOOL;     (* 手动模式开关 *)

    (* 输出变量 *)
    heater : BOOL;          (* 加热器控制 *)
    cooler : BOOL;          (* 冷却器控制 *)
    fan : BOOL;             (* 排风扇控制 *)
    alarm : BOOL;           (* 报警指示 *)

    (* 内部变量 *)
    temp_real : REAL;       (* 实际温度值（浮点） *)
    hum_real : REAL;        (* 实际湿度值（浮点） *)
END_VAR

(* 转换输入为实数 *)
temp_real := INT_TO_REAL(temperature) / 100.0;
hum_real := INT_TO_REAL(humidity) / 100.0;

(* 手动模式检查 *)
IF manual_mode THEN
    (* 手动模式：关闭所有自动控制 *)
    heater := FALSE;
    cooler := FALSE;
    fan := FALSE;
    alarm := FALSE;
ELSE
    (* 自动模式 - 温度控制 *)
    IF temp_real < 18.0 THEN
        heater := TRUE;
        cooler := FALSE;
    ELSIF temp_real > 26.0 THEN
        cooler := TRUE;
        heater := FALSE;
    ELSE
        heater := FALSE;
        cooler := FALSE;
    END_IF;

    (* 湿度控制 *)
    IF hum_real > 70.0 THEN
        fan := TRUE;
    ELSE
        fan := FALSE;
    END_IF;

    (* 异常温度报警 *)
    IF (temp_real < 5.0) OR (temp_real > 40.0) THEN
        alarm := TRUE;
    ELSE
        alarm := FALSE;
    END_IF;
END_IF;

END_PROGRAM


CONFIGURATION Config0
  RESOURCE Res0 ON PLC
    TASK Main(INTERVAL := T#50ms, PRIORITY := 0);
    PROGRAM Inst0 WITH Main : TemperatureControl;
  END_RESOURCE
END_CONFIGURATION
