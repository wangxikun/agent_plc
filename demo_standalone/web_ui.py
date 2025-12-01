"""
Agents4PLC Web UI - Interactive interface based on Gradio
Supports natural language to ST code generation, compilation verification, and animation demo
"""

import gradio as gr
import sys
from pathlib import Path
import tempfile
import os

# Add project path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from src.simple_plc_generator import SimplePLCGenerator
from src.compiler import rusty_compiler
from src.st_animator import STAnimator


class PLCWebUI:
    """PLC Code Generation Web Interface"""
    
    def __init__(self):
        """Initialize UI and backend components"""
        print("🚀 Initializing Agents4PLC Web UI...")
        
        # Initialize generator (code generation only, no auto verification)
        self.generator = SimplePLCGenerator(
            compiler="rusty",
            enable_verification=False,  # Manual verification control
            enable_auto_fix=False
        )
        
        # Initialize animation generator
        self.animator = STAnimator()
        
        # Current session state
        self.current_st_code = None
        self.current_instruction = None
        self.current_temp_file = None
        
        print("✅ Initialization complete!")
    
    def generate_st_code(self, instruction: str, progress=gr.Progress()):
        """
        Step 1: Generate ST code from natural language
        
        Args:
            instruction: Natural language description from user
            progress: Gradio progress bar
            
        Returns:
            (st_code, status_message)
        """
        if not instruction or instruction.strip() == "":
            return "", "❌ Error: Please enter requirement description"
        
        try:
            progress(0.1, desc="🤖 Calling LLM...")
            
            # Save current instruction
            self.current_instruction = instruction
            
            # Call LLM to generate code
            progress(0.3, desc="💭 LLM thinking...")
            st_code = self.generator.quick_generate(instruction)
            
            # Save generated code
            self.current_st_code = st_code
            
            progress(1.0, desc="✅ Code generation complete!")
            
            status_msg = f"""✅ **Code Generated Successfully!**
            
📊 **Statistics**:
- Lines of code: {len(st_code.split(chr(10)))} lines
- Characters: {len(st_code)} chars
- Model: {self.generator.llm_config.get('model', 'default')}

💡 **Next Step**: Click "🔧 Compile & Verify" button to check the code"""
            
            return st_code, status_msg
            
        except Exception as e:
            error_msg = f"❌ **Generation Failed**: {str(e)}\n\nPlease check:\n1. API configuration is correct\n2. Network connection is working"
            return "", error_msg
    
    def verify_st_code(self, st_code: str, progress=gr.Progress()):
        """
        Step 2: Compile and verify ST code
        
        Args:
            st_code: ST code
            progress: Gradio progress bar
            
        Returns:
            (verification_result, status_message)
        """
        if not st_code or st_code.strip() == "":
            return "❌ Error: No code to verify", ""
        
        try:
            progress(0.2, desc="📝 Saving code to temp file...")
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.ST', 
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(st_code)
                self.current_temp_file = f.name
            
            progress(0.5, desc="🔧 Calling Rusty compiler...")
            
            # Call Rusty compiler
            compile_success = rusty_compiler(self.current_temp_file)
            
            progress(1.0, desc="✅ Verification complete!")
            
            if compile_success:
                status_msg = f"""✅ **Compilation Passed!**

🎉 Code syntax is correct, compliant with IEC-61131-3 standard

📋 **Verification Details**:
- Compiler: Rusty
- File: {os.path.basename(self.current_temp_file)}
- Status: ✅ PASSED

💡 **Next Step**: Set input variable values, click "🎬 Generate Animation" to view execution"""
                
                return "✅ Compilation Passed", status_msg
            else:
                status_msg = f"""❌ **Compilation Failed**

Code has syntax errors, please check:
1. Variable declarations are complete
2. Statements end with semicolons
3. Keywords are spelled correctly
4. Brackets are matched

💡 **Suggestion**: Regenerate or manually fix the code"""
                
                return "❌ Compilation Failed", status_msg
                
        except Exception as e:
            error_msg = f"❌ **Verification Error**: {str(e)}\n\nPossible causes:\n1. Rusty compiler not installed\n2. Docker not running (Docker mode)"
            return "❌ Verification Error", error_msg
    
    def generate_animation(self, st_code: str, input_vars_text: str, progress=gr.Progress()):
        """
        Step 3: Generate animation demo
        
        Args:
            st_code: ST code
            input_vars_text: Input variable configuration (format: var1=value1, var2=value2)
            progress: Gradio progress bar
            
        Returns:
            (html_path, status_message)
        """
        if not st_code or st_code.strip() == "":
            error_html = "<div style='text-align:center; padding:50px; color:#e74c3c;'>❌ Error: No code to generate animation</div>"
            return error_html, "❌ Error: No code to generate animation"
        
        try:
            progress(0.2, desc="🎨 Parsing input variables...")
            
            # Parse input variables
            input_values = {}
            if input_vars_text and input_vars_text.strip():
                try:
                    # Parse format: var1=value1, var2=value2
                    pairs = [p.strip() for p in input_vars_text.split(',')]
                    for pair in pairs:
                        if '=' in pair:
                            key, value = pair.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            # Type conversion
                            if value.lower() == 'true':
                                input_values[key] = True
                            elif value.lower() == 'false':
                                input_values[key] = False
                            elif '.' in value:
                                input_values[key] = float(value)
                            else:
                                try:
                                    input_values[key] = int(value)
                                except:
                                    input_values[key] = value
                except Exception as e:
                    error_msg = f"❌ Input variable format error: {str(e)}\n\nCorrect format example: start_button=True, temperature=25.0"
                    error_html = f"<div style='text-align:center; padding:50px; color:#e74c3c;'>{error_msg}</div>"
                    return error_html, error_msg
            
            progress(0.5, desc="🎬 Generating animation...")
            
            # Generate animation
            html_path = self.animator.generate_animation(
                st_code=st_code,
                input_values=input_values,
                output_html_path=None,
                max_cycles=1,
                auto_open=False  # Don't auto-open browser
            )
            
            progress(0.8, desc="📖 Reading animation file...")
            
            # Verify html_path is file path not content
            if not isinstance(html_path, str):
                raise ValueError(f"Generated html_path type error: {type(html_path)}")
            
            # Check if it's a valid file path
            if not os.path.exists(html_path):
                raise FileNotFoundError(f"Animation file not found: {html_path}")
            
            # Check file path length (prevent HTML content)
            if len(html_path) > 300:
                raise ValueError(f"html_path too long, might be content not path. Length: {len(html_path)}")
            
            # Read HTML file content
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            progress(1.0, desc="✅ Animation generation complete!")
            
            # Wrap HTML content in iframe, as Gradio can't directly render full HTML document
            import base64
            html_base64 = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
            iframe_html = f'''
            <iframe 
                src="data:text/html;base64,{html_base64}"
                style="width:100%; height:800px; border:none; border-radius:8px;"
                sandbox="allow-scripts allow-same-origin"
            ></iframe>
            '''
            
            status_msg = f"""✅ **Animation Generated Successfully!**

🎬 **Animation Details**:
- File: {os.path.basename(html_path)}
- Input Variables: {input_values if input_values else 'None (using defaults)'}
- Scan Cycles: 1 cycle

💡 **Tips**: 
- View animation on the right
- Use play/pause/step controls
- Keyboard shortcuts: Space=play/pause, →=next step, ←=previous step"""
            
            return iframe_html, status_msg
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Animation generation error details:\n{error_trace}")  # Print to console for debugging
            
            error_msg = f"""❌ **Animation Generation Failed**: {str(e)}

**Possible Causes**:
1. Code parsing failed
2. Input variables mismatch
3. File write permission issue

**Error Type**: {type(e).__name__}

**Debug Tip**: Check console for detailed error info"""
            
            error_html = f"""<div style='text-align:center; padding:50px; color:#e74c3c; max-width:600px; margin:auto;'>
                <h3>❌ Animation Generation Failed</h3>
                <p style='color:#555; margin:20px 0;'>{str(e)}</p>
                <div style='text-align:left; background:#f5f5f5; padding:15px; border-radius:5px; font-size:12px;'>
                    <strong>Possible Causes:</strong><br>
                    • Code structure doesn't match FUNCTION_BLOCK format<br>
                    • Input variable names don't match<br>
                    • Code contains unsupported syntax
                </div>
            </div>"""
            
            return error_html, error_msg
    
    def load_example(self, example_name: str):
        """Load example"""
        examples = {
            "Motor Control": {
                "instruction": """Create a simple motor control system.

Input Variables:
- start_button: BOOL (Start button)
- stop_button: BOOL (Stop button)

Output Variables:
- motor: BOOL (Motor state)

Logic:
- Press start button, motor starts
- Press stop button, motor stops
- Stop button has higher priority""",
                "input_vars": "start_button=True, stop_button=False"
            },
            "Temperature Control": {
                "instruction": """Create a temperature control system.

Input Variables:
- temperature: REAL (Current temperature in Celsius)
- manual_mode: BOOL (Manual mode)

Output Variables:
- heater: BOOL (Heater)
- cooler: BOOL (Cooler)
- alarm: BOOL (Alarm)

Logic:
- Temperature < 18°C: Start heater
- Temperature > 26°C: Start cooler
- 18°C ≤ Temperature ≤ 26°C: Both off
- Temperature < 5°C or > 40°C: Trigger alarm
- In manual mode, no auto control""",
                "input_vars": "temperature=15.0, manual_mode=False"
            },
            "Traffic Light Control": {
                "instruction": """Create a smart traffic light control system.

Input Variables:
- car_detected: BOOL (Vehicle detection)
- pedestrian_button: BOOL (Pedestrian button)
- emergency_vehicle: BOOL (Emergency vehicle)

Output Variables:
- red_light: BOOL (Red light)
- yellow_light: BOOL (Yellow light)
- green_light: BOOL (Green light)

Logic:
- Default green light
- Car detected and pedestrian pressed button: Yellow → Red
- Emergency vehicle: All lights turn red""",
                "input_vars": "car_detected=True, pedestrian_button=False, emergency_vehicle=False"
            },
            "Tank Level Control": {
                "instruction": """Create a tank level control system.

Input Variables:
- level: REAL (Current level, 0-100%)
- flow_rate: REAL (Inlet flow rate, 0-100%)

Output Variables:
- inlet_valve: BOOL (Inlet valve)
- outlet_valve: BOOL (Outlet valve)
- pump: BOOL (Pump)
- low_alarm: BOOL (Low level alarm)
- high_alarm: BOOL (High level alarm)

Logic:
- level < 20%: Open inlet valve and pump
- level > 80%: Open outlet valve
- 20% ≤ level ≤ 80%: Maintain current state
- level < 10%: Trigger low level alarm
- level > 90%: Trigger high level alarm
- Emergency (level < 5% or > 95%): Enable alarm and corresponding valve""",
                "input_vars": "level=15.0, flow_rate=50.0"
            },
            "Elevator Control System": {
                "instruction": """Create a complex elevator control system (state machine implementation).

Input Variables:
- floor_request: INT (Requested floor, 1-5)
- current_floor: INT (Current floor, 1-5)
- door_sensor: BOOL (Door sensor, TRUE=obstacle detected)
- emergency_stop: BOOL (Emergency stop button)
- weight_overload: BOOL (Overweight sensor)

Output Variables:
- motor_up: BOOL (Motor going up)
- motor_down: BOOL (Motor going down)
- door_open: BOOL (Open door)
- door_close: BOOL (Close door)
- floor_indicator: INT (Floor display)
- alarm: BOOL (Alarm)
- status_code: INT (Status code: 0=idle, 1=up, 2=down, 3=opening, 4=closing, 5=fault)

State Machine Logic:
1. IDLE State:
   - Wait for floor request
   - Determine up or down when request received

2. MOVING_UP State:
   - Motor running upward
   - Switch to DOOR_OPENING after reaching target floor

3. MOVING_DOWN State:
   - Motor running downward
   - Switch to DOOR_OPENING after reaching target floor

4. DOOR_OPENING State:
   - Open elevator door
   - Switch to DOOR_OPEN when fully opened

5. DOOR_OPEN State:
   - Keep door open for a while
   - Switch to DOOR_CLOSING when no obstacle

6. DOOR_CLOSING State:
   - Close elevator door
   - Reopen when obstacle detected
   - Switch to IDLE when fully closed

Safety Logic:
- Emergency stop: Stop all motion immediately, trigger alarm
- Overweight: Don't allow door close, continuous alarm
- Door sensor: Reopen when obstacle detected""",
                "input_vars": "floor_request=3, current_floor=1, door_sensor=False, emergency_stop=False, weight_overload=False"
            }
        }
        
        if example_name in examples:
            return examples[example_name]["instruction"], examples[example_name]["input_vars"]
        return "", ""
    
    def create_ui(self):
        """Create Gradio interface"""
        
        # Custom CSS
        custom_css = """
        .header-container {
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .status-box {
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        .code-output {
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 8px;
        }
        """
        
        # Create Gradio interface (compatible with all Gradio versions)
        with gr.Blocks() as demo:
            
            # Title
            gr.HTML("""
            <div class="header-container">
                <h1>🤖 Agents4PLC - Intelligent PLC Code Generation System</h1>
                <p>From natural language to verifiable ST code with one-click animation demo</p>
            </div>
            """)
            
            with gr.Row():
                # Left side: Input and controls
                with gr.Column(scale=1):
                    gr.Markdown("## 📝 Step 1: Enter Requirement Description")
                    
                    # Example selection
                    with gr.Row():
                        example_dropdown = gr.Dropdown(
                            choices=["Motor Control", "Temperature Control", "Traffic Light Control", "Tank Level Control", "Elevator Control System"],
                            label="💡 Quick Examples (Optional)",
                            value=None
                        )
                    
                    # Requirement input
                    instruction_input = gr.Textbox(
                        label="🎯 Requirement Description",
                        placeholder="Describe your PLC control requirements in natural language...\n\nExample: Create a temperature control system that starts a fan when temperature exceeds 80 degrees",
                        lines=10,
                        max_lines=15
                    )
                    
                    # Generate button
                    generate_btn = gr.Button(
                        "🚀 Generate ST Code",
                        variant="primary",
                        size="lg"
                    )
                    
                    # Generation status
                    generate_status = gr.Markdown(
                        "Waiting for user input...",
                        elem_classes=["status-box"]
                    )
                    
                    gr.Markdown("---")
                    gr.Markdown("## 🔧 Step 2: Compile & Verify")
                    
                    verify_btn = gr.Button(
                        "🔧 Compile & Verify",
                        variant="secondary",
                        size="lg"
                    )
                    
                    verify_status = gr.Markdown(
                        "Waiting for verification...",
                        elem_classes=["status-box"]
                    )
                    
                    gr.Markdown("---")
                    gr.Markdown("## 🎬 Step 3: Generate Animation")
                    
                    input_vars_input = gr.Textbox(
                        label="⚙️ Input Variable Configuration (Optional)",
                        placeholder="Format: var1=value1, var2=value2\nExample: start_button=True, temperature=25.0",
                        lines=2
                    )
                    
                    animation_btn = gr.Button(
                        "🎬 Generate Animation",
                        variant="secondary",
                        size="lg"
                    )
                    
                    animation_status = gr.Markdown(
                        "Waiting to generate animation...",
                        elem_classes=["status-box"]
                    )
                
                # Right side: Output
                with gr.Column(scale=1):
                    gr.Markdown("## 📄 Generated ST Code")
                    
                    st_code_output = gr.Code(
                        label="",
                        language="javascript",  # Use javascript syntax highlighting (similar to ST)
                        lines=20,
                        elem_classes=["code-output"]
                    )
                    
                    verify_result = gr.Textbox(
                        label="✅ Verification Result",
                        lines=2,
                        interactive=False
                    )
                    
                    gr.Markdown("## 🎬 Animation Preview")
                    
                    animation_output = gr.HTML(
                        label="",
                        value="<div style='text-align:center; padding:50px; color:#999;'>Waiting to generate animation...</div>"
                    )
            
            # Bottom instructions
            gr.Markdown("""
            ---
            ### 📖 User Guide
            
            1. **Generate Code**: Enter natural language description, click "Generate ST Code"
            2. **Verify Code**: After generation, click "Compile & Verify" to check syntax
            3. **View Animation**: After verification, set input variables, click "Generate Animation"
            
            ### 💡 Input Variable Format
            - BOOL type: `button=True` or `button=False`
            - INT type: `count=10`
            - REAL type: `temperature=25.5`
            - Multiple variables separated by commas: `var1=True, var2=100, var3=25.5`
            
            ### ⌨️ Animation Shortcuts
            - **Space**: Play/Pause
            - **→**: Next step
            - **←**: Previous step
            - **R**: Reset
            """)
            
            # Event bindings
            
            # Example selection
            example_dropdown.change(
                fn=self.load_example,
                inputs=[example_dropdown],
                outputs=[instruction_input, input_vars_input]
            )
            
            # Generate code
            generate_btn.click(
                fn=self.generate_st_code,
                inputs=[instruction_input],
                outputs=[st_code_output, generate_status]
            )
            
            # Compile & verify
            verify_btn.click(
                fn=self.verify_st_code,
                inputs=[st_code_output],
                outputs=[verify_result, verify_status]
            )
            
            # Generate animation
            def generate_and_display_animation(st_code, input_vars):
                # self.generate_animation now directly returns (html_content, status)
                html_content, status = self.generate_animation(st_code, input_vars)
                return html_content, status
            
            animation_btn.click(
                fn=generate_and_display_animation,
                inputs=[st_code_output, input_vars_input],
                outputs=[animation_output, animation_status]
            )
        
        return demo


def main():
    """Main function"""
    print("="*80)
    print("🚀 Starting Agents4PLC Web UI")
    print("="*80)
    
    # Create UI instance
    ui = PLCWebUI()
    
    # Create and launch Gradio interface
    demo = ui.create_ui()
    
    print("\n✅ Web UI started!")
    print("📱 Open the displayed URL in your browser")
    print("⌨️  Press Ctrl+C to stop the server")
    print("="*80)
    
    # Start server
    demo.launch(
        server_name="0.0.0.0",  # Allow external access
        server_port=7860,
        share=False,  # Set to True to generate public link
        show_error=True
    )


if __name__ == "__main__":
    main()

