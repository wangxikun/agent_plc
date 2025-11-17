#!/usr/bin/env python3
"""
构建FUNCTION_BLOCK示例的RAG数据库
Build RAG Database from FUNCTION_BLOCK Examples

功能：
1. 从FUNCTION_BLOCK示例.md文档中提取9个示例
2. 将每个示例转换为结构化的JSON格式
3. 生成向量数据库用于RAG检索
4. 支持基于自然语言查询相似示例

使用场景：
- 当用户输入自然语言时，检索最相似的示例代码
- 提供给LLM作为few-shot learning的参考
- 提高代码生成质量，特别是状态机等复杂场景
"""

import sys
import os
import json
import re
from pathlib import Path
from typing import List, Dict

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

from config import openai_api_key, openai_base_url

# ===========================================================================
# 配置
# ===========================================================================

# FUNCTION_BLOCK示例文档路径
FUNCTION_BLOCK_DOC = "FUNCTION_BLOCK示例.md"

# 输出JSON文件路径
OUTPUT_JSON = "data/function_block_examples.json"

# RAG数据库路径
RAG_DB_DIR = "databases/function_block_rag_db"

# ===========================================================================
# 示例提取
# ===========================================================================

def extract_function_block_examples(md_file_path: str) -> List[Dict]:
    """
    从FUNCTION_BLOCK示例.md文档中提取所有示例

    返回格式:
    [
        {
            "id": 1,
            "title": "传送带安全互锁控制",
            "category": "safety_logic",
            "difficulty": "medium",
            "description": "...",
            "instruction": "...",
            "st_code": "...",
            "keywords": ["IF", "ELSIF", "safety", "interlock"]
        },
        ...
    ]
    """

    with open(md_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    examples = []

    # 定义9个示例的元数据
    example_metadata = [
        {
            "id": 1,
            "title": "传送带安全互锁控制",
            "category": "safety_logic",
            "difficulty": "medium",
            "keywords": ["IF", "ELSIF", "safety", "interlock", "priority_logic"]
        },
        {
            "id": 2,
            "title": "液位控制与延时排水",
            "category": "timer_ton",
            "difficulty": "hard",
            "keywords": ["TON", "timer", "level_control", "state_latch"]
        },
        {
            "id": 3,
            "title": "瓶子精确计数",
            "category": "edge_detection",
            "difficulty": "hard",
            "keywords": ["R_TRIG", "edge_detection", "counter", "CLK"]
        },
        {
            "id": 4,
            "title": "电机安全门互锁",
            "category": "basic_logic",
            "difficulty": "easy",
            "keywords": ["AND", "safety_door", "motor_control"]
        },
        {
            "id": 5,
            "title": "加热器延时启动",
            "category": "timer_ton",
            "difficulty": "medium",
            "keywords": ["TON", "timer", "delayed_start", "heater"]
        },
        {
            "id": 6,
            "title": "风扇关断延时",
            "category": "timer_tof",
            "difficulty": "hard",
            "keywords": ["TOF", "timer", "delayed_stop", "cooling"]
        },
        {
            "id": 7,
            "title": "批次计数与报警",
            "category": "counter_ctu",
            "difficulty": "hard",
            "keywords": ["CTU", "counter", "batch", "PV", "CV", "CU"]
        },
        {
            "id": 8,
            "title": "三步顺序控制",
            "category": "state_machine",
            "difficulty": "very_hard",
            "keywords": ["CASE", "state_machine", "sequential_control", "TON"]
        },
        {
            "id": 9,
            "title": "模拟量缩放",
            "category": "function_math",
            "difficulty": "medium",
            "keywords": ["FUNCTION", "scaling", "INT_TO_REAL", "math"]
        }
    ]

    # 使用正则表达式提取示例
    # 每个示例以 "## 示例X:" 开头
    pattern = r'## 示例(\d+):(.*?)\n(.*?)(?=## 示例\d+:|$)'
    matches = re.findall(pattern, content, re.DOTALL)

    for match in matches:
        example_id = int(match[0])
        title = match[1].strip()
        body = match[2].strip()

        # 提取代码块（```st ... ```）
        code_pattern = r'```st\n(.*?)```'
        code_matches = re.findall(code_pattern, body, re.DOTALL)
        st_code = code_matches[0] if code_matches else ""

        # 提取需求描述（## 需求描述 部分）
        desc_pattern = r'## 需求描述\n(.*?)(?=## |$)'
        desc_matches = re.findall(desc_pattern, body, re.DOTALL)
        description = desc_matches[0].strip() if desc_matches else ""

        # 获取元数据
        metadata = next((m for m in example_metadata if m['id'] == example_id), {})

        example = {
            "id": example_id,
            "title": metadata.get('title', title),
            "category": metadata.get('category', 'unknown'),
            "difficulty": metadata.get('difficulty', 'medium'),
            "description": description,
            "st_code": st_code,
            "keywords": metadata.get('keywords', []),
            "instruction": description  # 作为instruction用于RAG检索
        }

        examples.append(example)

    return sorted(examples, key=lambda x: x['id'])


def save_examples_to_json(examples: List[Dict], output_path: str):
    """保存示例到JSON文件"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(examples, f, ensure_ascii=False, indent=2)

    print(f"✓ 已保存 {len(examples)} 个示例到: {output_path}")


# ===========================================================================
# RAG数据库构建
# ===========================================================================

def create_documents_from_examples(examples: List[Dict]) -> List[Document]:
    """
    将示例转换为LangChain Document对象

    每个Document包含:
    - page_content: 示例的文本表示（instruction + code）
    - metadata: 示例的元数据（id, title, category, keywords等）
    """
    documents = []

    for example in examples:
        # 构建page_content（用于语义检索）
        page_content = f"""
示例: {example['title']}
类别: {example['category']}
难度: {example['difficulty']}

需求描述:
{example['description']}

ST代码:
{example['st_code']}

关键技术: {', '.join(example['keywords'])}
"""

        # 构建metadata
        metadata = {
            "id": example['id'],
            "title": example['title'],
            "category": example['category'],
            "difficulty": example['difficulty'],
            "keywords": ','.join(example['keywords']),
            "source": "FUNCTION_BLOCK示例.md"
        }

        doc = Document(page_content=page_content.strip(), metadata=metadata)
        documents.append(doc)

    return documents


def build_rag_database(examples: List[Dict], db_dir: str):
    """
    构建RAG向量数据库

    Args:
        examples: 示例列表
        db_dir: 数据库保存目录
    """
    print(f"正在构建RAG数据库...")
    print(f"  - 示例数量: {len(examples)}")
    print(f"  - 数据库路径: {db_dir}")

    # 初始化Embeddings
    embedding = OpenAIEmbeddings(
        model="text-embedding-ada-002",
        api_key=openai_api_key,
        base_url=openai_base_url
    )

    # 转换为Document对象
    documents = create_documents_from_examples(examples)

    # 文本分割（示例比较短，不需要太多分割）
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,  # 较大的chunk_size保持示例完整性
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(documents)

    print(f"  - 文档分块数: {len(splits)}")

    # 创建或更新向量数据库
    if os.path.exists(db_dir):
        print(f"  - 检测到已存在的数据库，将更新...")
        vectorstore = Chroma(
            embedding_function=embedding,
            persist_directory=db_dir
        )
        # 添加新文档
        vectorstore.add_documents(splits)
    else:
        print(f"  - 创建新的向量数据库...")
        os.makedirs(db_dir, exist_ok=True)
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embedding,
            persist_directory=db_dir
        )

    print(f"✓ RAG数据库构建完成: {db_dir}")
    return vectorstore


# ===========================================================================
# 测试RAG检索
# ===========================================================================

def test_rag_retrieval(db_dir: str, query: str, top_k: int = 3):
    """
    测试RAG检索功能

    Args:
        db_dir: 数据库路径
        query: 查询文本
        top_k: 返回top-k个最相似的结果
    """
    print(f"\n{'='*80}")
    print(f"测试RAG检索")
    print(f"{'='*80}")
    print(f"查询: {query}")
    print()

    # 初始化Embeddings
    embedding = OpenAIEmbeddings(
        model="text-embedding-ada-002",
        api_key=openai_api_key,
        base_url=openai_base_url
    )

    # 加载向量数据库
    vectorstore = Chroma(
        embedding_function=embedding,
        persist_directory=db_dir
    )

    # 执行检索
    results = vectorstore.similarity_search_with_score(query, k=top_k)

    print(f"找到 {len(results)} 个相似示例:\n")

    for i, (doc, score) in enumerate(results, 1):
        print(f"--- 结果 {i} (相似度分数: {score:.4f}) ---")
        print(f"标题: {doc.metadata.get('title', 'Unknown')}")
        print(f"类别: {doc.metadata.get('category', 'Unknown')}")
        print(f"难度: {doc.metadata.get('difficulty', 'Unknown')}")
        print(f"关键词: {doc.metadata.get('keywords', 'N/A')}")
        print()
        print("内容摘要:")
        print(doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content)
        print()


# ===========================================================================
# 主程序
# ===========================================================================

def main():
    """主程序"""
    print("="*80)
    print("FUNCTION_BLOCK示例RAG数据库构建工具")
    print("="*80)
    print()

    # 步骤1: 提取示例
    print("【步骤1】从文档中提取示例")
    print("-"*80)

    if not os.path.exists(FUNCTION_BLOCK_DOC):
        print(f"✗ 错误: 找不到文档 {FUNCTION_BLOCK_DOC}")
        print(f"   请确保文件存在于项目根目录")
        return

    examples = extract_function_block_examples(FUNCTION_BLOCK_DOC)
    print(f"✓ 成功提取 {len(examples)} 个示例")
    print()

    # 步骤2: 保存为JSON
    print("【步骤2】保存示例到JSON文件")
    print("-"*80)
    save_examples_to_json(examples, OUTPUT_JSON)
    print()

    # 步骤3: 构建RAG数据库
    print("【步骤3】构建RAG向量数据库")
    print("-"*80)
    try:
        vectorstore = build_rag_database(examples, RAG_DB_DIR)
        print()
    except Exception as e:
        print(f"✗ 构建数据库失败: {e}")
        print("  提示: 请检查config.py中的API配置")
        return

    # 步骤4: 测试检索
    print("【步骤4】测试RAG检索功能")
    print("-"*80)

    test_queries = [
        "我需要实现一个状态机，控制多步骤顺序操作",
        "如何使用定时器实现延时关断？风扇需要在关闭后继续运行一段时间",
        "实现一个计数器，统计产品数量并在达到目标时报警",
        "需要检测传感器信号的上升沿，避免重复计数"
    ]

    for query in test_queries:
        test_rag_retrieval(RAG_DB_DIR, query, top_k=2)

    # 完成
    print("="*80)
    print("✓ 数据库构建完成!")
    print("="*80)
    print()
    print("使用方法:")
    print(f"  1. RAG数据库已保存到: {RAG_DB_DIR}")
    print(f"  2. 示例JSON已保存到: {OUTPUT_JSON}")
    print()
    print("集成到代码生成器:")
    print("""
from src.langchain_create_agent import create_agent

# 创建带RAG的代码生成Agent
agent = create_agent(
    model_name="gpt-4",
    system_prompt="...",
    enable_rag=True,
    db_dir="databases/function_block_rag_db"
)

# 使用Agent生成代码
result = agent.invoke({"messages": [("user", "创建一个三步顺序控制程序")]})
""")
    print()
    print("下一步:")
    print("  - 修改src/simple_plc_generator.py，集成RAG检索")
    print("  - 运行tests/test_function_block_examples.py测试效果")
    print()


if __name__ == "__main__":
    main()
