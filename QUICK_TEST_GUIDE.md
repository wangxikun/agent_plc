# 快速测试指南 - OpenPLC温度控制系统

## ✅ 已完成的准备工作

1. ✅ Docker已安装并运行
2. ✅ OpenPLC容器已创建并运行
3. ✅ OpenPLC Webserver正在运行 (http://localhost:8080)
4. ✅ ST代码已准备: `openplc_temp_simple.st`
5. ✅ 测试脚本已准备: `test_temp_simple.py`
6. ✅ Python测试依赖已安装: pyModbusTCP

## 📋 剩余步骤（2分钟）

### 步骤1: 上传ST程序到OpenPLC

1. 打开浏览器，访问：**http://localhost:8080**

2. **登录**：
   - 用户名：`openplc`
   - 密码：`openplc`

3. 点击顶部菜单 **"Programs"** 标签

4. 点击 **"Choose File"** 按钮

5. 选择文件：
   ```
   /Users/scott/pythonrepo/Agents4PLC_release/openplc_temp_simple.st
   ```

6. 点击 **"Upload Program"** 按钮

7. 等待编译完成（应该看到 "Compilation finished successfully!"）

### 步骤2: 启动PLC

1. 点击顶部菜单 **"Dashboard"** 标签

2. 点击绿色的 **"Start PLC"** 按钮

3. 等待状态变为 **"Running"**（大约2-3秒）

### 步骤3: 运行测试

打开终端，执行：

```bash
cd /Users/scott/pythonrepo/Agents4PLC_release
python3 test_temp_simple.py
```

## 🎯 预期测试结果

测试脚本会运行6个场景：

```
测试1: 低温场景 (15°C)
  → 加热器应该开启
  → 冷却器应该关闭
  ✅ 正确

测试2: 高温场景 (30°C)
  → 加热器应该关闭
  → 冷却器应该开启
  ✅ 正确

测试3: 舒适温度 (22°C)
  → 两者都应该关闭
  ✅ 正确

测试4: 高湿度场景 (80%)
  → 排风扇应该开启
  ✅ 正确

测试5: 异常温度报警 (2°C)
  → 报警应该开启
  ✅ 正确

测试6: 手动模式
  → 所有输出应该关闭
  ✅ 正确
```

## 🛠️ 如果遇到问题

### 问题1: 无法连接到OpenPLC

**症状**:
```
❌ 连接失败
请确保OpenPLC正在运行
```

**解决**:
1. 检查Docker容器状态：
   ```bash
   docker ps | grep openplc
   ```
2. 重启webserver（如果需要）：
   ```bash
   docker exec -d openplc bash -c "cd /opt/openplc/webserver && python3 webserver.py"
   ```

### 问题2: PLC状态显示"Stopped"

**解决**: 点击Dashboard页面的"Start PLC"按钮

### 问题3: 编译失败

**症状**: 上传后显示编译错误

**可能原因**: ST代码格式问题

**解决**: 确保使用的是 `openplc_temp_simple.st`（不是带AT语法的版本）

## 📊 测试原理

测试脚本通过Modbus TCP协议与PLC通信：

- **写入**（模拟传感器）：
  - 温度值 → Holding Register 1024
  - 湿度值 → Holding Register 1025
  - 手动模式开关 → Coil 1024

- **读取**（检查输出）：
  - 加热器状态 ← Coil 0
  - 冷却器状态 ← Coil 1
  - 排风扇状态 ← Coil 2
  - 报警状态 ← Coil 3

## 🚀 一切准备就绪！

完成上述3个步骤后，您就能看到GPT-4生成的温度控制系统在真实的PLC环境中运行！

---

**需要帮助？**
- Docker容器日志：`docker logs openplc`
- 进入容器Shell：`docker exec -it openplc bash`
- 停止容器：`docker stop openplc`
- 重启容器：`docker restart openplc`
