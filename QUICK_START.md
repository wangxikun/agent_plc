# Agents4PLC 快速启动指南

## 🚀 快速开始

### 前置要求

1. **Python环境** (已满足 ✓)
   - Python 3.8+
   - 已安装基础依赖

2. **配置文件** (已创建 ✓)
   - `config.py` - 系统配置文件

3. **可选工具** (根据需求安装)
   - Rusty编译器 (用于ST代码编译)
   - PLCverif工具 (用于形式化验证)
   - nuXmv模型检查器 (用于属性验证)

---

## 📋 三种启动方式

### 方式1: 运行简单示例 (推荐新手) ✨

这是最简单的方式，展示系统基本功能：

```bash
python3 simple_demo_example.py
```

**功能演示**:
- ✓ 编译验证 (语法检查)
- ✓ 属性验证 (形式化验证)
- ✓ Benchmark数据加载

**当前状态**:
- ✅ 编译验证: 可用 (Rusty编译器已安装)
- ⚠️ 属性验证: 需要安装依赖 (`pip install beautifulsoup4 lxml`)
- ⚠️ Benchmark: 需要安装 (`pip install langchain langchain-core`)

---

### 方式2: 仅编译验证 (最简单) 🔧

如果只想测试PLC代码的语法正确性：

```python
from src.compiler import rusty_compiler

# 验证ST代码文件
success = rusty_compiler('path/to/your/code.ST')

if success:
    print("✓ 编译成功")
else:
    print("✗ 编译失败")
```

**示例代码** (`test_compile_only.py`):

```python
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

import tempfile
from src.compiler import rusty_compiler

# 创建测试代码
st_code = """
FUNCTION_BLOCK LED_Control
VAR_INPUT
    button : BOOL;
END_VAR
VAR_OUTPUT
    led : BOOL;
END_VAR
    led := button;
END_FUNCTION_BLOCK
"""

# 保存到临时文件
with tempfile.NamedTemporaryFile(mode='w', suffix='.ST', delete=False) as f:
    f.write(st_code)
    temp_file = f.name

# 编译验证
result = rusty_compiler(temp_file)
print(f"编译结果: {'成功' if result else '失败'}")

# 清理
import os
os.unlink(temp_file)
```

运行:
```bash
python3 test_compile_only.py
```

---

### 方式3: 完整验证流程 (需要完整工具链) 🎯

包括编译验证 + 形式化属性验证：

```python
from src.compiler import rusty_compiler
from src.plcverif import plcverif_validation

# 步骤1: 编译验证
st_file_path = "path/to/code.ST"
if rusty_compiler(st_file_path):
    print("✓ 编译通过")

    # 步骤2: 属性验证
    properties = [
        {
            "property_description": "验证输出始终与输入相等",
            "property": {
                "job_req": "pattern",
                "pattern_id": "pattern-invariant",
                "pattern_params": {
                    "1": "instance.output = instance.input"
                }
            }
        }
    ]

    results = plcverif_validation(
        st_dir=st_file_path,
        properties_to_be_validated=properties,
        base_dir="result/verification"
    )

    for result in results:
        print(result)
else:
    print("✗ 编译失败")
```

**需要的工具**:
- PLCverif
- nuXmv或cbmc
- beautifulsoup4, lxml

---

## 📦 安装缺失依赖

### 基础Python依赖

```bash
# 安装基础依赖
pip install beautifulsoup4 lxml

# 如果需要使用LLM功能和RAG
pip install langchain langchain-openai langchain-chroma
```

### 编译器安装 (可选)

#### Rusty编译器

```bash
# 1. 安装依赖
sudo apt-get install build-essential llvm-14-dev liblld-14-dev libz-dev lld libclang-common-14-dev libpolly-14-dev

# 2. 安装Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 3. 构建Rusty
git clone https://github.com/PLC-lang/rusty.git --depth 1
cd rusty
cargo build

# 4. 添加到PATH
export PATH="$PATH:/path/to/rusty/target/debug"
```

#### Matiec编译器

```bash
# 1. 克隆仓库
git clone https://github.com/nucleron/matiec.git
cd matiec

# 2. 安装依赖
sudo apt-get install autoconf flex bison build-essential -y

# 3. 构建
autoreconf -i
./configure
make

# 4. 配置环境变量
export MATIEC_INCLUDE_PATH=/path/to/matiec/lib
export MATIEC_C_INCLUDE_PATH=/path/to/matiec/lib/C
export PATH=/path/to/matiec:$PATH

# 5. 更新config.py
# MATIEC_PATH = "/path/to/matiec"
```

### 验证工具安装 (可选)

#### nuXmv模型检查器

```bash
wget https://nuxmv.fbk.eu/theme/download.php?file=nuXmv-2.0.0-linux64.tar.gz
tar -xzvf nuXmv-2.0.0-linux64.tar.gz
export PATH=$PATH:/path/to/nuXmv-2.0.0-Linux/bin
```

#### PLCverif

```bash
mkdir -p src/plcverif
cd src/plcverif
wget https://plcverif-oss.gitlab.io/cern.plcverif.cli/releases/cern.plcverif.cli.cmdline.app.product-linux.gtk.x86_64.tar.gz
tar -xvzf cern.plcverif.cli.cmdline.app.product-linux.gtk.x86_64.tar.gz
export PATH="/path/to/src/plcverif:$PATH"
```

---

## 🎯 实际使用场景

### 场景1: 快速验证ST代码语法

```bash
# 创建测试代码
cat > test.ST << 'EOF'
FUNCTION_BLOCK TestBlock
VAR_INPUT
    x : INT;
END_VAR
VAR_OUTPUT
    y : INT;
END_VAR
    y := x * 2;
END_FUNCTION_BLOCK
EOF

# 验证
python3 -c "
import sys
sys.path.append('.')
from src.compiler import rusty_compiler
print('编译结果:', '成功' if rusty_compiler('test.ST') else '失败')
"
```

### 场景2: 使用Benchmark数据测试

```python
#!/usr/bin/env python3
import sys
sys.path.append('.')

from src.tools import parse_plc_file

# 加载benchmark
data = parse_plc_file('benchmark_v1/easy.jsonl')

print(f"加载了 {len(data)} 个测试案例")

# 显示第一个案例
case = data[0]
print(f"\n案例ID: {case['id']}")
print(f"属性数量: {len(case['properties_to_be_validated'])}")
```

### 场景3: 批量评估

需要实现自己的multi_agent_workflow函数（参考论文中的Multi-Agent系统）

```python
from src.batch_run_framework import batch_run_json_dataset
from src.tools import parse_plc_file

# 加载数据
data = parse_plc_file('benchmark_v1/easy.jsonl')

# 批量运行
batch_run_json_dataset(data)
```

---

## 📖 项目结构说明

```
Agents4PLC_release/
├── src/                          # 核心源代码
│   ├── compiler.py               # ✅ 编译器封装 (可用)
│   ├── plcverif.py              # PLCverif验证工具
│   ├── nuXmv.py                 # nuXmv模型检查器
│   ├── langchain_create_agent.py # LLM代理创建
│   ├── tools.py                 # 工具函数
│   └── batch_run_framework.py   # 批量处理框架
│
├── evaluate/                     # 评估脚本
│   ├── plcverif_evaluation.py   # PLCverif评估
│   └── smv_evaluation.py        # SMV评估
│
├── benchmark_v1/                 # 数据集v1
│   ├── easy.jsonl               # 简单案例
│   └── medium.jsonl             # 中等难度
│
├── benchmark_v2/                 # 数据集v2
│   ├── medium.jsonl             # 70个中等案例
│   └── hard.jsonl               # 3个困难案例
│
├── prompts/                      # LLM提示词模板
├── result/                       # 实验结果
├── config.py                     # ✅ 配置文件 (已创建)
├── simple_demo_example.py        # ✅ 简单示例 (已创建)
└── QUICK_START.md               # 本文档
```

---

## ✅ 当前可用功能

| 功能 | 状态 | 说明 |
|------|------|------|
| **编译验证** | ✅ 可用 | Rusty编译器已安装 |
| **配置文件** | ✅ 完成 | config.py已创建 |
| **示例脚本** | ✅ 完成 | simple_demo_example.py |
| **Benchmark数据** | ✅ 可用 | benchmark_v1/v2 |
| 属性验证 | ⚠️ 需要依赖 | 需要PLCverif+nuXmv |
| LLM功能 | ⚠️ 需要依赖 | 需要langchain |
| RAG功能 | ⚠️ 需要依赖 | 需要chromadb |

---

## 🎓 学习路径

### 新手路径

1. ✅ **运行simple_demo_example.py** - 了解系统基本功能
2. 📖 **阅读ORIGINAL_SYSTEM_ARCHITECTURE.md** - 理解系统架构
3. 🧪 **测试编译验证** - 验证自己的ST代码
4. 📚 **查看benchmark数据** - 了解测试案例格式

### 进阶路径

5. 🔧 **安装PLCverif工具** - 启用属性验证
6. 🧪 **运行完整验证** - 编译+属性验证
7. 🤖 **配置LLM API** - 启用LLM功能
8. 📊 **批量评估** - 在benchmark上测试

### 高级路径

9. 🏗️ **实现Multi-Agent工作流** - 参考论文
10. 🔬 **复现论文实验** - 使用完整工具链
11. 🚀 **扩展系统功能** - 添加新的pattern

---

## 🆘 常见问题

### Q1: 编译器找不到？

**现象**: `plc: command not found`

**解决**:
```bash
# 检查rusty是否安装
which plc

# 如果没有，按照上面的说明安装rusty
```

### Q2: 属性验证失败？

**现象**: `No module named 'bs4'`

**解决**:
```bash
pip install beautifulsoup4 lxml
```

### Q3: 如何验证自己的ST代码？

```python
from src.compiler import rusty_compiler

result = rusty_compiler('your_code.ST')
print('编译结果:', '成功' if result else '失败')
```

### Q4: 如何查看benchmark示例？

```bash
# 查看第一个案例
head -n 35 benchmark_v1/easy.jsonl

# 或使用Python
python3 -c "
import json
with open('benchmark_v1/easy.jsonl') as f:
    case = json.loads(f.readline())
    print('ID:', case['id'])
    print('属性数量:', len(case['properties_to_be_validated']))
"
```

---

## 📚 参考文档

- **系统架构**: `ORIGINAL_SYSTEM_ARCHITECTURE.md`
- **论文**: [Agents4PLC Paper](https://arxiv.org/abs/2410.14209)
- **项目说明**: `CLAUDE.md`

---

## 🎯 下一步

### 立即可做 (无需额外安装)

- [x] 运行 `simple_demo_example.py`
- [x] 测试编译验证功能
- [ ] 查看benchmark数据格式
- [ ] 编写自己的ST代码并验证

### 需要安装工具

- [ ] 安装beautifulsoup4 (属性验证)
- [ ] 安装langchain (LLM功能)
- [ ] 安装PLCverif (形式化验证)
- [ ] 安装nuXmv (模型检查)

### 长期目标

- [ ] 实现完整的Multi-Agent工作流
- [ ] 在benchmark上运行批量评估
- [ ] 复现论文中的实验结果
- [ ] 扩展系统支持更多pattern

---

**祝使用愉快！** 🎉

如有问题，请参考相关文档或查看代码注释。
