# AstrBot 插件配置注册完整指南

## 概述

AstrBot 的插件配置系统提供了强大的配置管理和可视化功能，允许用户在管理面板上直接配置插件，而不需要修改代码。

---

## 方案 1：推荐方案 - 使用 `_conf_schema.json` (v3.4.15+)

这是 AstrBot 官方推荐的配置方式。

### 1.1 配置注册使用的函数/文件

- **文件名**：`_conf_schema.json`
- **位置**：插件根目录
- **格式**：JSON Schema

### 1.2 配置命名空间定义

命名空间是**自动确定**的，无需手动指定：
- 配置文件会自动保存在 `data/config/<plugin_name>_config.json`
- `<plugin_name>` 来自 `metadata.yaml` 文件中的 `name` 字段

### 1.3 具体代码示例

#### 步骤 1：创建 `_conf_schema.json`

在插件目录下创建 `_conf_schema.json` 文件：

```json
{
  "token": {
    "description": "Bot Token",
    "type": "string",
    "hint": "Bot 的 Token，获取方式见...",
    "obvious_hint": true
  },
  "enable_feature_x": {
    "description": "是否启用功能X",
    "type": "bool",
    "default": true
  },
  "max_retries": {
    "description": "最大重试次数",
    "type": "int",
    "default": 3
  },
  "api_url": {
    "description": "API 地址",
    "type": "string",
    "default": "https://api.example.com"
  },
  "advanced_settings": {
    "description": "高级设置",
    "type": "object",
    "items": {
      "timeout": {
        "description": "请求超时时间（秒）",
        "type": "float",
        "default": 10.0
      },
      "debug_mode": {
        "description": "调试模式",
        "type": "bool",
        "default": false
      }
    }
  },
  "allowed_platforms": {
    "description": "允许的平台列表",
    "type": "list",
    "hint": "平台名称列表"
  }
}
```

#### 步骤 2：在插件类中使用配置

```python
from astrbot.api import AstrBotConfig, Star, logger
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context

class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        
        # 获取配置值
        self.token = self.config.get("token", "")
        self.enable_feature_x = self.config.get("enable_feature_x", True)
        self.max_retries = self.config.get("max_retries", 3)
        
        # 获取嵌套配置
        self.timeout = self.config.get("advanced_settings", {}).get("timeout", 10.0)
        self.debug_mode = self.config.get("advanced_settings", {}).get("debug_mode", False)
        
        logger.info(f"插件配置加载完成: token={self.token[:10]}...")

    @filter.command("test")
    async def test_command(self, event: AstrMessageEvent):
        """测试插件配置"""
        yield event.plain_result(
            f"Token: {self.token[:10]}...\n"
            f"功能X启用: {self.enable_feature_x}\n"
            f"重试次数: {self.max_retries}"
        )

    async def initialize(self):
        """插件初始化时调用"""
        # 可以在这里验证配置
        if not self.token:
            logger.warning("未配置 Token，部分功能将不可用")
```

### 1.4 Schema 字段说明

| 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `type` | ✅ | string | 配置类型：`string`, `text`, `int`, `float`, `bool`, `object`, `list` |
| `description` | ❌ | string | 配置描述（建议一句话） |
| `hint` | ❌ | string | 鼠标悬停时显示的提示文本 |
| `obvious_hint` | ❌ | boolean | 提示是否醒目显示 |
| `default` | ❌ | any | 默认值 |
| `items` | ❌ | object | 当 type 为 `object` 时，定义子配置项 |
| `invisible` | ❌ | boolean | 是否隐藏该配置项（默认 false） |
| `options` | ❌ | array | 下拉列表选项，如 `["option1", "option2"]` |
| `editor_mode` | ❌ | boolean | 是否启用代码编辑器（v3.5.10+） |
| `editor_language` | ❌ | string | 编辑器代码语言，默认 `json` |
| `editor_theme` | ❌ | string | 编辑器主题：`vs-light`（默认）或 `vs-dark` |
| `_special` | ❌ | string | v4.0.0+：`select_provider`, `select_provider_tts`, `select_provider_stt`, `select_persona` |

### 1.5 高级特性

#### 代码编辑器模式（v3.5.10+）

```json
{
  "custom_json": {
    "description": "自定义 JSON 配置",
    "type": "string",
    "editor_mode": true,
    "editor_language": "json",
    "editor_theme": "vs-dark",
    "default": "{}"
  },
  "custom_python": {
    "description": "自定义 Python 代码",
    "type": "text",
    "editor_mode": true,
    "editor_language": "python",
    "editor_theme": "vs-light"
  }
}
```

#### 模型提供商选择（v4.0.0+）

```json
{
  "preferred_provider": {
    "description": "优先使用的 LLM 提供商",
    "type": "string",
    "_special": "select_provider"
  },
  "tts_provider": {
    "description": "TTS 提供商",
    "type": "string",
    "_special": "select_provider_tts"
  },
  "stt_provider": {
    "description": "STT 提供商",
    "type": "string",
    "_special": "select_provider_stt"
  },
  "default_persona": {
    "description": "默认人格设定",
    "type": "string",
    "_special": "select_persona"
  }
}
```

### 1.6 配置保存和更新

```python
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    @filter.command("update_config")
    async def update_config(self, event: AstrMessageEvent):
        """更新配置示例"""
        # 修改配置
        self.config["token"] = "new_token_value"
        self.config["max_retries"] = 5
        
        # 保存配置到文件
        self.config.save_config()
        
        yield event.plain_result("配置已更新")
```

---

## 方案 2：旧方案 - 使用 `put_config()` 函数（已过时）

这是 AstrBot 早期的配置方式，已过时但仍可用。

### 2.1 API 函数

**位置**：`astrbot.core.star.config`

```python
def put_config(
    namespace: str,
    name: str,
    key: str,
    value,
    description: str
) -> None:
    """将配置项写入配置文件。
    
    Args:
        namespace: 配置命名空间（通常为插件名）
        name: 配置项的显示名字
        key: 配置项的键
        value: 配置项的值（str, int, float, bool, list）
        description: 配置项的描述
    """
```

### 2.2 使用示例

```python
from astrbot.api import put_config, load_config, update_config, logger
from astrbot.api import Star
from astrbot.api.event import filter
from astrbot.api.star import Context

class OldConfigPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.api_key = None
        
        # 在 initialize 中注册配置项
    
    async def initialize(self):
        """插件初始化时注册配置"""
        # 注册配置项
        put_config(
            namespace="my_plugin",  # 插件名
            name="API Key",         # 显示名称
            key="api_key",          # 配置键
            value="",               # 默认值
            description="用于认证的 API Key"
        )
        
        put_config(
            namespace="my_plugin",
            name="Max Retries",
            key="max_retries",
            value=3,
            description="最大重试次数"
        )
        
        # 从文件加载配置
        config = load_config("my_plugin")
        if config:
            self.api_key = config.get("api_key", "")
            logger.info(f"配置加载成功")
        else:
            logger.info(f"首次使用，配置已初始化")
    
    async def terminate(self):
        """插件卸载时调用"""
        pass

    @filter.command("update_api_key")
    async def update_api_key(self, event: AstrMessageEvent, new_key: str):
        """更新 API Key"""
        update_config("my_plugin", "api_key", new_key)
        self.api_key = new_key
        yield event.plain_result("API Key 已更新")
```

### 2.3 配置文件位置

配置文件自动保存在：`data/config/<namespace>.json`

配置文件格式：

```json
{
  "api_key": {
    "config_type": "item",
    "name": "API Key",
    "description": "用于认证的 API Key",
    "path": "api_key",
    "value": "my_secret_key",
    "val_type": "str"
  },
  "max_retries": {
    "config_type": "item",
    "name": "Max Retries",
    "description": "最大重试次数",
    "path": "max_retries",
    "value": 3,
    "val_type": "int"
  }
}
```

---

## 方案 3：混合方案 - 结合两种方式

对于需要兼容性或更灵活控制的插件：

```python
from astrbot.api import AstrBotConfig, Star, logger, put_config, load_config
from astrbot.api.event import filter
from astrbot.api.star import Context

class HybridConfigPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        
        # 优先使用新的 Schema 方式
        if config:
            self.config = config
            self.use_new_schema = True
            logger.info("使用 _conf_schema.json 配置系统")
        else:
            # 回退到旧的 put_config 方式
            self.use_new_schema = False
            self._init_old_config()
    
    def _init_old_config(self):
        """初始化旧式配置"""
        self.config = load_config("hybrid_plugin") or {}
        if not self.config:
            # 首次使用，注册配置
            put_config("hybrid_plugin", "Token", "token", "", "Bot Token")
            put_config("hybrid_plugin", "Enabled", "enabled", True, "是否启用")
```

---

## 重要说明

### 配置版本管理

当更新插件版本并修改 Schema 时：
- ✅ AstrBot **会**自动为缺失的配置项添加默认值
- ❌ AstrBot **不会**删除旧 Schema 中已删除但配置文件中仍存在的项

### 配置文件路径

| 方式 | 路径 | 文件名 |
|------|------|--------|
| `_conf_schema.json` | `data/config/` | `<plugin_name>_config.json` |
| `put_config()` | `data/config/` | `<namespace>.json` |

### 命名空间约定

- **推荐方案**：使用插件的 `metadata.yaml` 中的 `name` 字段作为命名空间
- **旧方案**：通常使用插件名作为命名空间，格式为小写、下划线分隔，如 `my_plugin`, `web_searcher`

---

## 完整插件示例

```python
"""
完整的插件配置示例
"""

from astrbot.api import AstrBotConfig, Star, logger
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context


class ConfiguredPlugin(Star):
    """一个具有完整配置功能的插件"""
    
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.context = context
        self.config = config
        
        # 初始化配置
        self._load_config()
    
    def _load_config(self):
        """加载配置"""
        self.api_key = self.config.get("api_key", "")
        self.enable_logging = self.config.get("enable_logging", True)
        self.timeout = self.config.get("advanced_settings", {}).get("timeout", 30)
        self.debug_mode = self.config.get("advanced_settings", {}).get("debug_mode", False)
        
        if self.debug_mode:
            logger.info(f"插件已加载，配置: api_key={self.api_key[:10]}...")
    
    async def initialize(self):
        """插件初始化"""
        if not self.api_key:
            logger.warning("未配置 API Key，请在管理面板配置")
    
    @filter.command("status")
    async def show_status(self, event: AstrMessageEvent):
        """显示插件状态"""
        status_info = f"""
插件配置信息：
- API Key 已配置: {'是' if self.api_key else '否'}
- 日志记录: {'启用' if self.enable_logging else '禁用'}
- 超时时间: {self.timeout}s
- 调试模式: {'启用' if self.debug_mode else '禁用'}
        """.strip()
        
        yield event.plain_result(status_info)
    
    @filter.command("update_timeout", {int})
    async def update_timeout(self, event: AstrMessageEvent, new_timeout: int):
        """更新超时时间"""
        self.config["advanced_settings"]["timeout"] = new_timeout
        self.config.save_config()
        self.timeout = new_timeout
        
        yield event.plain_result(f"超时时间已更新为 {new_timeout}s")
```

对应的 `_conf_schema.json`：

```json
{
  "api_key": {
    "description": "API 密钥",
    "type": "string",
    "hint": "从官方网站获取",
    "obvious_hint": true
  },
  "enable_logging": {
    "description": "是否启用日志记录",
    "type": "bool",
    "default": true
  },
  "advanced_settings": {
    "description": "高级设置",
    "type": "object",
    "items": {
      "timeout": {
        "description": "请求超时时间（秒）",
        "type": "int",
        "default": 30
      },
      "debug_mode": {
        "description": "是否启用调试模式",
        "type": "bool",
        "default": false
      }
    }
  }
}
```

---

## 总结表格

| 特性 | `_conf_schema.json` | `put_config()` |
|------|------------------|-----------------|
| 推荐等级 | ⭐⭐⭐⭐⭐ 推荐 | ⚠️ 已过时 |
| 最低版本 | v3.4.15+ | 早期版本 |
| 配置定义 | JSON Schema 文件 | Python 函数 |
| 显示位置 | WebUI 管理面板 | WebUI 管理面板 |
| 嵌套对象 | ✅ 支持 | ❌ 不支持 |
| 代码编辑器 | ✅ 支持(v3.5.10+) | ❌ 不支持 |
| 自动加载 | ✅ 自动创建 | ⚠️ 需手动初始化 |
| 版本兼容 | ✅ 声明版本范围 | ❌ 不支持 |
| 命名空间 | 自动生成 | 手动指定 |

---

## 遗留注意事项

### 过时提示

`astrbot.core.star.config` 模块顶部有过时提示：
```
此功能已过时，参考 https://astrbot.app/dev/plugin.html#%E6%B3%A8%E5%86%8E%E6%8F%92%E4%BB%B6%E9%85%8C%E7%BD%AE-beta
```

虽然代码仍可用，但官方已不再维护该方式。

### 数据持久化

无论使用哪种方式，配置数据都应：
- 存储在 `data/config/` 目录下（由 AstrBot 自动管理）
- 不要存储在插件目录（防止升级时丢失）
- 使用 `get_astrbot_data_path()` 获取数据目录

