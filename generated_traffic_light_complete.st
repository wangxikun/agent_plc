FUNCTION_BLOCK TrafficLightControl
VAR_INPUT
    manual_mode : BOOL;    (* Manual mode input *)
    emergency : BOOL;      (* Emergency button input *)
END_VAR

VAR_OUTPUT
    red_light : BOOL;      (* Red light output *)
    yellow_light : BOOL;   (* Yellow light output *)
    green_light : BOOL;    (* Green light output *)
END_VAR

VAR
    timer : TON;           (* Timer for state transitions *)
    state : INT := 0;      (* Current state: 0=Red, 1=Green, 2=Yellow *)
    timer_duration : TIME; (* Duration for the current state *)
    yellow_flash_state : BOOL := FALSE; (* Internal state for yellow light flashing *)
END_VAR

(* Main logic *)
IF manual_mode THEN
    (* Manual mode: Turn off all lights *)
    red_light := FALSE;
    yellow_light := FALSE;
    green_light := FALSE;
ELSIF emergency THEN
    (* Emergency mode: Yellow light flashes *)
    timer(IN := TRUE, PT := T#500ms); (* Flashing interval: 500ms *)
    IF timer.Q THEN
        yellow_flash_state := NOT yellow_flash_state; (* Toggle yellow light state *)
        timer(IN := FALSE); (* Reset timer *)
    END_IF;
    red_light := FALSE;
    yellow_light := yellow_flash_state;
    green_light := FALSE;
ELSE
    (* Normal mode: Traffic light sequence *)
    CASE state OF
        0: (* Red light state *)
            red_light := TRUE;
            yellow_light := FALSE;
            green_light := FALSE;
            timer_duration := T#30s; (* Red light duration *)
        1: (* Green light state *)
            red_light := FALSE;
            yellow_light := FALSE;
            green_light := TRUE;
            timer_duration := T#25s; (* Green light duration *)
        2: (* Yellow light state *)
            red_light := FALSE;
            yellow_light := TRUE;
            green_light := FALSE;
            timer_duration := T#5s; (* Yellow light duration *)
    END_CASE;

    (* Timer logic for state transitions *)
    timer(IN := TRUE, PT := timer_duration);
    IF timer.Q THEN
        timer(IN := FALSE); (* Reset timer *)
        state := (state + 1) MOD 3; (* Cycle through states: 0 -> 1 -> 2 -> 0 *)
    END_IF;
END_IF;

END_FUNCTION_BLOCK

PROGRAM TrafficLight
VAR
    (* Input variables *)
    manual_mode : BOOL := FALSE;
    emergency : BOOL := FALSE;

    (* Output variables *)
    red_light : BOOL;
    yellow_light : BOOL;
    green_light : BOOL;

    (* Function block instance *)
    fb_traffic : TrafficLightControl;
END_VAR

(* Call function block *)
fb_traffic(
    manual_mode := manual_mode,
    emergency := emergency,
    red_light => red_light,
    yellow_light => yellow_light,
    green_light => green_light
);

END_PROGRAM

CONFIGURATION Config0
  RESOURCE Res0 ON PLC
    TASK Main(INTERVAL := T#100ms, PRIORITY := 0);
    PROGRAM Inst0 WITH Main : TrafficLight;
  END_RESOURCE
END_CONFIGURATION
