## valid compilers for evaluate part, which is independent with the fixing part.
## only return True or False indicating that compilation passed(True) or failed(False)
## however, if compiler donnot exist, 
import subprocess
import sys
from pathlib import Path
# Resolve the parent directory as an absolute path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

import config
import os


def is_docker_available():
    """检查 Docker 是否可用"""
    try:
        subprocess.run(
            ['docker', 'info'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def is_plc_local_available():
    """检查本地 plc 命令是否可用"""
    try:
        subprocess.run(
            ['plc', '--version'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def rusty_compiler_local(file_dir):
    """本地方式调用 RuSTy 编译器"""
    print(f"\n🔧 [RuSTy Compiler] Calling local plc compiler...")
    print(f"   Command: plc --check {file_dir}")

    # Verify file exists and show proof
    import os
    if file_dir and os.path.exists(file_dir):
        file_size = os.path.getsize(file_dir)
        print(f"   ✅ File exists: {file_dir}")
        print(f"   📄 File size: {file_size} bytes")
        # Show first few lines as proof
        with open(file_dir, 'r') as f:
            first_lines = ''.join(f.readlines()[:3])
            print(f"   📝 First 3 lines:")
            for line in first_lines.split('\n')[:3]:
                print(f"      {line}")
    else:
        print(f"   ⚠️  File path is None or doesn't exist: {file_dir}")

    try:
        output = subprocess.check_output(
            f'plc --check {file_dir} 2>&1 | sed "s/\\x1b\\[[0-9;]*m//g"',
            shell=True,
            text=True
        )

        print(f"   Output: {output[:200] if output else '(no output - compilation successful)'}")

        if 'error' in output:
            print(f"   Result: ❌ Compilation FAILED")
            return False
        else:
            print(f"   Result: ✅ Compilation SUCCESSFUL")
            return True
    except subprocess.CalledProcessError as e:
        print(f"   Result: ❌ Compilation ERROR: {e}")
        return False


def rusty_compiler_docker(file_dir):
    """Docker 方式调用 RuSTy 编译器"""
    try:
        # 获取 Docker 镜像配置
        docker_image = getattr(config, 'rusty_docker_image', 'ghcr.io/plc-lang/rusty-docker:docker-x86_64')

        # 获取文件的绝对路径和目录
        abs_file_path = os.path.abspath(file_dir)
        file_name = os.path.basename(abs_file_path)
        file_dir_parent = os.path.dirname(abs_file_path)

        # 使用 Docker 运行 plc --check
        output = subprocess.check_output(
            f'docker run --rm '
            f'-v "{file_dir_parent}:/workspace" '
            f'--entrypoint plc '
            f'{docker_image} '
            f'--check /workspace/{file_name} '
            f'2>&1 | grep -v WARNING | sed "s/\\x1b\\[[0-9;]*m//g"',
            shell=True,
            text=True
        )

        if 'error' in output.lower():
            return False
        else:
            return True
    except subprocess.CalledProcessError as e:
        return False


def rusty_compiler(file_dir):
    """
    RuSTy 编译器入口函数，根据配置自动选择调用方式

    支持三种模式（在 config.rusty_mode 中配置）：
    - "local": 强制使用本地 plc 命令
    - "docker": 强制使用 Docker 镜像
    - "auto": 自动选择（优先本地，不可用则用 Docker）
    """
    # 获取配置的模式，默认 auto
    mode = getattr(config, 'rusty_mode', 'auto')
    print(f"\n📋 [RuSTy Compiler Entry] Mode: {mode}")

    if mode == "local":
        # 强制使用本地模式
        print(f"   → Using LOCAL mode")
        return rusty_compiler_local(file_dir)

    elif mode == "docker":
        # 强制使用 Docker 模式
        print(f"   → Using DOCKER mode")
        return rusty_compiler_docker(file_dir)

    elif mode == "auto":
        # 自动模式：优先本地，失败则尝试 Docker
        print(f"   → Using AUTO mode (detecting available compiler...)")
        if is_plc_local_available():
            print(f"   → Detected: Local plc command available")
            return rusty_compiler_local(file_dir)
        elif is_docker_available():
            print(f"   → Detected: Docker available")
            return rusty_compiler_docker(file_dir)
        else:
            raise RuntimeError(
                "Neither local 'plc' nor Docker is available. "
                "Please install RuSTy locally or ensure Docker is running."
            )

    else:
        raise ValueError(f"Invalid rusty_mode: {mode}. Must be 'local', 'docker', or 'auto'.")


def matiec_compiler(file_dir):
    MATIEC_PATH = getattr(config, 'MATIEC_PATH', None)

    if MATIEC_PATH is None:
        MATIEC_PATH = os.getenv('MATIEC_PATH')

    if MATIEC_PATH is None:
        raise ValueError("MATIEC_PATH is not set in config or as an environment variable.")
    
    try:
        output = subprocess.check_output(
            f'iec2iec -f -p "{file_dir}" 2>&1 | head -n -2',
            cwd=MATIEC_PATH,
            shell=True,   # execute in shell
            text=True     # return string
        )
        
        if 'error' in output:
            return False
        else:
            return True
    except subprocess.CalledProcessError as e:
        # raise subprocess.CalledProcessError
        return False
