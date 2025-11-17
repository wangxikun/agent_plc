### Configuration for Agents4PLC ###
# This is a minimal config for testing purposes

# Model configuration (not needed for compiler.py testing)
chat_model = "gpt-5.1"
embedding_model = "text-embedding-ada-002"

# API configuration (not needed for compiler.py testing)
# 修复: API路径需要包含 /v1 后缀
openai_base_url = "https://api.openai-proxy.org/v1"
openai_api_key = "sk-VoXDRfA85Bzieu2tUnlof1Ah4t8qoObkRQT5PAsekQ4n4Ry3"

# 备选方案: 如果上面的代理不工作，可以尝试：
# openai_base_url = "https://api.openai.com/v1"  # 官方API
# base_url = "https://api.openai-proxy.org/v1"   # 或使用通用配置

# Compiler configuration
# MATIEC_PATH: Path to matiec compiler installation (only needed if using matiec_compiler)
MATIEC_PATH = None  # Set to your matiec path if available, e.g., "/path/to/matiec"

# Evaluation thresholds
plcverif_verified_threshold = 0.80
plcverif_passed_threshold = 0.80

# Default compiler for evaluation
evaluate_compiler = "rusty"

# Context window size
max_tokens = 4500
