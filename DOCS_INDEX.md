# 📚 Agents4PLC 文档导航

欢迎使用Agents4PLC！根据您的需求选择对应文档：

---

## 🚀 快速开始

### 我是新手，想快速了解项目
👉 [README_DEMO.md](README_DEMO.md)
- 项目概述和核心功能
- 5分钟快速开始指南
- API使用示例
- 完整工作流程

### 我想看代码生成的实际例子
👉 [CODE_GENERATION_EXAMPLES.md](CODE_GENERATION_EXAMPLES.md) ⭐ **推荐**
- **示例1**: 交通信号灯控制（含完整代码）
- **示例2**: 温度控制系统（含完整代码）
- **示例3**: 电梯控制系统（含完整代码）
- 输入输出对应关系
- 最佳实践建议

---

## 🎯 实际操作

### 我想运行代码生成演示
**脚本**: `demo_simple_generation.py`

**文档**: [DEMO_SUCCESS_REPORT.md](DEMO_SUCCESS_REPORT.md)
- 演示流程详解
- 技术实现细节
- 代码质量分析
- 统计数据

### 我想测试生成的代码
**脚本**: `test_traffic_light.py`

**文档**: [TEST_GENERATED_TRAFFIC_LIGHT.md](TEST_GENERATED_TRAFFIC_LIGHT.md)
- OpenPLC上传步骤
- Modbus TCP测试指南
- 预期测试结果
- 故障排查

---

## 🔧 环境配置

### 我需要安装OpenPLC
**脚本**: `run_openplc_docker.sh`

**文档**: [NEXT_STEPS.md](NEXT_STEPS.md)
- Docker部署指南
- macOS编译问题说明
- 推荐解决方案
- 性能对比

### 我想快速测试温度控制示例
**脚本**: `test_temp_simple.py`

**文档**: [QUICK_TEST_GUIDE.md](QUICK_TEST_GUIDE.md)
- 2分钟快速测试
- 已完成的准备工作
- 详细操作步骤
- Modbus通信原理

---

## 📖 技术文档

### 项目整体介绍
**文档**: [QUICK_START.md](QUICK_START.md)
- 项目背景
- 架构设计
- 数据集说明
- 研究论文

### 项目架构和配置
**文档**: [CLAUDE.md](CLAUDE.md)
- 项目结构详解
- 核心模块说明
- API配置指南
- 工具链安装

---

## 🛠️ 故障排查

### macOS编译问题
**文档**:
- [MACOS_COMPILATION_FIX.md](MACOS_COMPILATION_FIX.md) - 编译修复说明
- [OPENPLC_MACOS_STATUS.md](OPENPLC_MACOS_STATUS.md) - macOS状态总结
- [NEXT_STEPS.md](NEXT_STEPS.md) - Docker解决方案

### 常见问题
**文档**: [CODE_GENERATION_EXAMPLES.md](CODE_GENERATION_EXAMPLES.md)
- 查看"常见问题"章节
- API调用失败
- 生成质量优化
- 代码结构支持

---

## 📂 文档完整列表

### 核心文档（必读）

| 文档 | 用途 | 优先级 |
|------|------|--------|
| [README_DEMO.md](README_DEMO.md) | 项目概览和快速开始 | ⭐⭐⭐⭐⭐ |
| [CODE_GENERATION_EXAMPLES.md](CODE_GENERATION_EXAMPLES.md) | 代码生成示例集 | ⭐⭐⭐⭐⭐ |
| [DEMO_SUCCESS_REPORT.md](DEMO_SUCCESS_REPORT.md) | 演示技术报告 | ⭐⭐⭐⭐ |

### 操作指南

| 文档 | 用途 | 适用场景 |
|------|------|---------|
| [TEST_GENERATED_TRAFFIC_LIGHT.md](TEST_GENERATED_TRAFFIC_LIGHT.md) | 测试交通灯代码 | 部署测试 |
| [QUICK_TEST_GUIDE.md](QUICK_TEST_GUIDE.md) | 测试温度控制 | 快速验证 |
| [NEXT_STEPS.md](NEXT_STEPS.md) | Docker部署指南 | 环境搭建 |

### 技术参考

| 文档 | 用途 | 适用人群 |
|------|------|---------|
| [CLAUDE.md](CLAUDE.md) | 架构和配置详解 | 开发者 |
| [QUICK_START.md](QUICK_START.md) | 项目整体介绍 | 研究人员 |
| [FUNCTION_BLOCK示例.md](FUNCTION_BLOCK示例.md) | Function Block知识库 | 高级用户 |

### 故障排查

| 文档 | 用途 | 问题类型 |
|------|------|---------|
| [MACOS_COMPILATION_FIX.md](MACOS_COMPILATION_FIX.md) | macOS编译修复 | 编译错误 |
| [OPENPLC_MACOS_STATUS.md](OPENPLC_MACOS_STATUS.md) | macOS状态总结 | 平台兼容 |
| [CLEANUP_REPORT.md](CLEANUP_REPORT.md) | 项目清理记录 | 维护参考 |

### 研究和报告

| 文档 | 用途 | 内容 |
|------|------|------|
| [ARCHITECTURE_COMPARISON_REPORT.md](ARCHITECTURE_COMPARISON_REPORT.md) | 架构对比分析 | 设计决策 |
| [FUNCTION_BLOCK_IMPROVEMENT_SUMMARY.md](FUNCTION_BLOCK_IMPROVEMENT_SUMMARY.md) | FB改进总结 | 优化记录 |
| [FUNCTION_BLOCK_TEST_REPORT.md](FUNCTION_BLOCK_TEST_REPORT.md) | FB测试报告 | 测试结果 |

---

## 🎯 按使用场景导航

### 场景1: 第一次使用项目
```
1. 阅读 README_DEMO.md（了解项目）
2. 查看 CODE_GENERATION_EXAMPLES.md（看示例）
3. 运行 demo_simple_generation.py（生成代码）
4. 阅读 DEMO_SUCCESS_REPORT.md（了解细节）
```

### 场景2: 部署和测试代码
```
1. 运行 run_openplc_docker.sh（启动OpenPLC）
2. 阅读 TEST_GENERATED_TRAFFIC_LIGHT.md（上传代码）
3. 运行 test_traffic_light.py（测试控制）
4. 查看 QUICK_TEST_GUIDE.md（其他测试）
```

### 场景3: 开发和定制
```
1. 阅读 CLAUDE.md（理解架构）
2. 查看 CODE_GENERATION_EXAMPLES.md（最佳实践）
3. 阅读 QUICK_START.md（数据集格式）
4. 参考 FUNCTION_BLOCK示例.md（RAG知识库）
```

### 场景4: 解决问题
```
1. 查看 CODE_GENERATION_EXAMPLES.md 常见问题部分
2. 阅读 NEXT_STEPS.md（Docker相关）
3. 查看 MACOS_COMPILATION_FIX.md（macOS问题）
4. 提交 GitHub Issue
```

---

## 📝 演示脚本

| 脚本 | 功能 | 文档 |
|------|------|------|
| `demo_simple_generation.py` | 简化演示（推荐） | README_DEMO.md |
| `real_demo_elevator.py` | 完整演示（含验证） | DEMO_SUCCESS_REPORT.md |
| `demo_real_generation.py` | 水箱控制示例 | - |
| `test_traffic_light.py` | 交通灯测试 | TEST_GENERATED_TRAFFIC_LIGHT.md |
| `test_temp_simple.py` | 温度控制测试 | QUICK_TEST_GUIDE.md |

---

## 🔍 快速查找

**想找...**
- **示例代码**: → [CODE_GENERATION_EXAMPLES.md](CODE_GENERATION_EXAMPLES.md)
- **快速开始**: → [README_DEMO.md](README_DEMO.md)
- **测试指南**: → [TEST_GENERATED_TRAFFIC_LIGHT.md](TEST_GENERATED_TRAFFIC_LIGHT.md)
- **Docker部署**: → [NEXT_STEPS.md](NEXT_STEPS.md)
- **API配置**: → [CLAUDE.md](CLAUDE.md)
- **macOS问题**: → [MACOS_COMPILATION_FIX.md](MACOS_COMPILATION_FIX.md)
- **项目架构**: → [ARCHITECTURE_COMPARISON_REPORT.md](ARCHITECTURE_COMPARISON_REPORT.md)

---

## 💡 推荐阅读顺序

### 对于初学者
1. ⭐ [README_DEMO.md](README_DEMO.md) - 了解项目
2. ⭐ [CODE_GENERATION_EXAMPLES.md](CODE_GENERATION_EXAMPLES.md) - 看实例
3. ⭐ [DEMO_SUCCESS_REPORT.md](DEMO_SUCCESS_REPORT.md) - 深入理解
4. [TEST_GENERATED_TRAFFIC_LIGHT.md](TEST_GENERATED_TRAFFIC_LIGHT.md) - 实际测试

### 对于开发者
1. [CLAUDE.md](CLAUDE.md) - 架构和API
2. [CODE_GENERATION_EXAMPLES.md](CODE_GENERATION_EXAMPLES.md) - 最佳实践
3. [QUICK_START.md](QUICK_START.md) - 数据集和工具链
4. [ARCHITECTURE_COMPARISON_REPORT.md](ARCHITECTURE_COMPARISON_REPORT.md) - 设计决策

### 对于研究人员
1. [QUICK_START.md](QUICK_START.md) - 项目背景
2. [DEMO_SUCCESS_REPORT.md](DEMO_SUCCESS_REPORT.md) - 技术分析
3. [FUNCTION_BLOCK_TEST_REPORT.md](FUNCTION_BLOCK_TEST_REPORT.md) - 测试结果
4. 论文: [Agents4PLC.pdf](Agents4PLC Automating Closed-loop PLC Code Generation and Verification in Industrial Control Systems using LLM-based Agents.pdf)

---

## 📞 获取帮助

1. **查看文档**: 根据上述导航找到对应文档
2. **运行示例**: 执行演示脚本验证功能
3. **查看报告**: 阅读详细的技术分析文档
4. **提交Issue**: GitHub Issues页面

---

**最后更新**: 2025-11-16
**文档数量**: 15+ 个Markdown文件
**演示脚本**: 5个Python脚本
**示例代码**: 3个完整PLC程序
