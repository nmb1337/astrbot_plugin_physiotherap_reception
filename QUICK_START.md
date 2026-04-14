# 快速启动指南 - Quick Start

## 5分钟快速配置

### 第1步: 启用插件
1. 进入 **AstrBot WebUI** 插件管理页面
2. 找到 **"关键词告警插件"** (astrbot_plugin_keyword_alert)
3. 点击 **"启用"** 或 **"加载"**

### 第2步: 配置关键词和QQ号
1. 在插件列表中找到本插件，点击 **"配置"** 按钮
2. 填写以下必要配置：

   **方案A: 只用精确匹配**
   ```
   alert_qqs: ["123456789"]           # 你的QQ号，用来接收告警
   keywords: ["骚扰", "辱骂"]          # 要监控的敏感词
   fuzzy_keywords: []                 # 留空
   enabled: true
   stop_chat: true
   ```

   **方案B: 精确+模糊匹配**
   ```
   alert_qqs: ["123456789", "987654321"]  # 多个QQ号用逗号分隔
   keywords: ["禁用词"]
   fuzzy_keywords: ["脏话"]  # 包含这个字符串就会触发
   enabled: true
   stop_chat: false  # 发警告但继续回复
   ```

3. 点击 **"保存配置"**

### 第3步: 测试
1. 发送包含关键词的消息，比如："你太骚扰了"
2. 查看 AstrBot 日志，应该看到：
   ```
   [WARNING] [关键词告警] 检测到关键词: 骚扰
   发送者: 你的昵称 (你的QQ)
   消息: 你太骚扰了
   ```
3. 运行命令 `/keyword_alert_status` 查看现状

---

## 常见问题速答

| 问题 | 答案 |
|------|------|
| 告警消息在哪看? | 在 AstrBot **日志文件**中 (WebUI 左侧可看实时日志) |
| 如何禁用? | 配置中将 `enabled` 改为 `false` |
| 一次能监控多少词? | 建议不超过 100 个 |
| 区分大小写吗? | 精确匹配区分，模糊匹配不区分 |
| 机器人为什么不回复? | 因为 `stop_chat: true`，改为 `false` 就会回复 |

---

## 配置项速记

```
alert_qqs          → [接收警告的QQ号列表]
keywords           → [精确匹配词汇]
fuzzy_keywords     → [模糊匹配词汇]  
enabled            → true/false (启用/禁用)
stop_chat          → true/false (停止/继续回复)
alert_message      → [告警消息模板]
```

---

## 命令速记

```
/keyword_alert_status          # 查看状态
/告警状态                      # 同上 (别名)
/reload_alert_config           # 重新加载配置
/重载告警配置                  # 同上 (别名)
```

---

## 遇到问题?

1. **重载插件**: WebUI → 插件列表 → 该插件 → **重载**
2. **查看日志**: WebUI → 日志 → 搜索 `关键词告警`
3. **重置配置**: 删除该插件再重新上传安装

---

详细文档请查看 [USAGE.md](USAGE.md)
