"""
关键词告警插件 - Keyword Alert Plugin
当检测到关键词或模糊关键词时，立即向指定QQ发送警告消息并停止机器人聊天
"""

import time
from typing import Dict, List, Optional
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.message_components import At, Plain
from astrbot.api.event import MessageChain
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig


@register("keyword_alert", "AstrBot Team", "关键词告警插件：检测敏感词并发送警告", "1.0.0")
class KeywordAlertPlugin(Star):
    """
    关键词告警插件
    功能：监听所有消息，检测关键词或模糊关键词，发送警告并停止聊天
    """

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.enabled = config.get("enabled", True)
        self.alert_qqs: List[str] = [str(x) for x in config.get("alert_qqs", [])]
        self.keywords: List[str] = config.get("keywords", [])
        self.fuzzy_keywords: List[str] = config.get("fuzzy_keywords", [])
        self.stop_chat = config.get("stop_chat", True)
        self.stop_duration_seconds = config.get("stop_duration_seconds", 300)
        self.alert_message_template = config.get(
            "alert_message",
            "【检测到关键词警告】\n发送者: {sender}\nQQ: {sender_id}\n消息内容: {message}\n检测词: {keyword}"
        )
        self.alert_origins: Dict[str, str] = {}
        self.blocked_senders: Dict[str, float] = {}
        
        logger.info(f"关键词告警插件已加载，监控关键词数: {len(self.keywords)}, 模糊关键词数: {len(self.fuzzy_keywords)}")

    async def initialize(self):
        """插件初始化"""
        self.alert_origins = await self.get_kv_data("alert_origins", {})
        self.blocked_senders = await self.get_kv_data("blocked_senders", {})
        if not self.enabled:
            logger.warning("关键词告警插件已禁用")
        if not self.alert_qqs:
            logger.warning("未配置接收警告的QQ号，请在插件配置中添加")

    def _check_keywords(self, message: str) -> Optional[str]:
        """
        检查消息是否包含关键词
        返回匹配的关键词，如果没有匹配则返回 None
        """
        # 检查精确匹配
        for keyword in self.keywords:
            if keyword in message:
                return keyword
        
        # 检查模糊匹配（包含检查）
        for keyword in self.fuzzy_keywords:
            if keyword.lower() in message.lower():
                return keyword
        
        return None

    async def _send_alert(self, event: AstrMessageEvent, sender_name: str, sender_id: str, message_text: str, keyword: str):
        """向已知 QQ 私聊 origin 发送告警，否则在当前会话中发送并 @ 目标 QQ"""
        if not self.alert_qqs:
            return

        # 格式化警告消息
        alert_text = self.alert_message_template.format(
            sender=sender_name,
            sender_id=sender_id,
            message=message_text,
            keyword=keyword
        )

        group_id = getattr(event, "group_id", None) or getattr(getattr(event, "message_obj", None), "group_id", None)
        private_targets = [qq for qq in self.alert_qqs if qq in self.alert_origins]
        fallback_targets = [qq for qq in self.alert_qqs if qq not in self.alert_origins]

        try:
            if private_targets:
                for alert_qq in private_targets:
                    origin = self.alert_origins.get(alert_qq)
                    if origin:
                        direct_chain = MessageChain().message(alert_text)
                        await self.context.send_message(origin, direct_chain)
                        logger.warning(f"[关键词告警] 已向 QQ {alert_qq} 私聊发送告警：{alert_text}")

            if fallback_targets:
                if group_id:
                    chain = MessageChain().message(alert_text)
                    await self.context.send_message(event.unified_msg_origin, chain)
                    logger.warning(f"[关键词告警] 已在当前会话发送告警，目标QQ: {', '.join(fallback_targets)}\n{alert_text}")
                else:
                    logger.warning(f"[关键词告警] 未找到已注册私聊 origin，无法将警告发送到目标 QQ: {', '.join(fallback_targets)}。当前会话将不会发送告警消息。")

        except Exception as e:
            logger.error(f"发送告警消息失败 (QQ: {', '.join(self.alert_qqs)}): {str(e)}")

    @filter.event_message_type(filter.EventMessageType.ALL, priority=100)
    async def on_message(self, event: AstrMessageEvent):
        """
        监听所有消息事件
        检测关键词并发送警告
        """
        if not self.enabled:
            return

        try:
            # 获取消息信息
            message_str = event.message_str
            sender_name = event.get_sender_name()
            sender_id = event.get_sender_id()

            # 检查是否包含关键词
            matched_keyword = self._check_keywords(message_str)

            sender_id_str = str(sender_id)
            if not getattr(event, "group_id", None) and event.unified_msg_origin and sender_id_str in self.alert_qqs:
                self.alert_origins[sender_id_str] = event.unified_msg_origin
                await self.put_kv_data("alert_origins", self.alert_origins)
                logger.info(f"已记录 QQ {sender_id} 的私聊 origin")

            blocked_until = self.blocked_senders.get(sender_id_str, 0)
            now_ts = time.time()
            if blocked_until > now_ts:
                logger.info(f"[关键词告警] QQ {sender_id_str} 仍在停止聊天期间，继续拦截消息。")
                event.stop_event()
                return
            elif sender_id_str in self.blocked_senders:
                self.blocked_senders.pop(sender_id_str)
                await self.put_kv_data("blocked_senders", self.blocked_senders)

            if matched_keyword:
                logger.warning(
                    f"[关键词告警] 检测到关键词: {matched_keyword}\n"
                    f"发送者: {sender_name} ({sender_id})\n"
                    f"消息: {message_str}"
                )

                if self.stop_chat and self.stop_duration_seconds > 0:
                    self.blocked_senders[sender_id_str] = now_ts + self.stop_duration_seconds
                    await self.put_kv_data("blocked_senders", self.blocked_senders)
                    logger.info(f"已停止 QQ {sender_id_str} 聊天 {self.stop_duration_seconds} 秒")

                if self.stop_chat:
                    event.stop_event()
                    logger.info(f"已停止消息处理链，关键词: {matched_keyword}")

                await self._send_alert(event, sender_name, sender_id_str, message_str, matched_keyword)

        except Exception as e:
            logger.error(f"关键词检测过程中出错: {str(e)}")

    @filter.command("keyword_alert_status", alias={"告警状态"})
    async def keyword_alert_status(self, event: AstrMessageEvent):
        """查看关键词告警插件状态"""
        status_info = f"""
【关键词告警插件状态】
启用状态: {'✓ 已启用' if self.enabled else '✗ 已禁用'}
精确关键词数: {len(self.keywords)}
模糊关键词数: {len(self.fuzzy_keywords)}
接收警告QQ数: {len(self.alert_qqs)}
已记录私聊 origin QQ数: {len(self.alert_origins)}
停止聊天: {'是' if self.stop_chat else '否'}

精确关键词: {', '.join(self.keywords) if self.keywords else '无'}
模糊关键词: {', '.join(self.fuzzy_keywords) if self.fuzzy_keywords else '无'}
"""
        yield event.plain_result(status_info)

    @filter.command("reload_alert_config", alias={"重载告警配置"})
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def reload_alert_config(self, event: AstrMessageEvent):
        """重新加载告警配置 (仅管理员)"""
        try:
            self.config.reload_config()
            self.enabled = self.config.get("enabled", True)
            self.alert_qqs = [str(x) for x in self.config.get("alert_qqs", [])]
            self.keywords = self.config.get("keywords", [])
            self.fuzzy_keywords = self.config.get("fuzzy_keywords", [])
            self.stop_chat = self.config.get("stop_chat", True)
            self.stop_duration_seconds = self.config.get("stop_duration_seconds", 300)
            self.alert_message_template = self.config.get(
                "alert_message",
                "【检测到关键词警告】\n发送者: {sender}\nQQ: {sender_id}\n消息内容: {message}\n检测词: {keyword}"
            )
            
            yield event.plain_result("✓ 告警配置已重新加载")
        except Exception as e:
            yield event.plain_result(f"✗ 配置重新加载失败: {str(e)}")

    @filter.command("register_alert_origin", alias={"注册告警"})
    async def register_alert_origin(self, event: AstrMessageEvent):
        """将当前 QQ 注册为告警接收者，保存私聊 origin"""
        sender_id = str(event.get_sender_id())
        origin = getattr(event, "unified_msg_origin", None)

        if not origin:
            yield event.plain_result("无法获取当前会话 origin，请确保是在私聊中执行此命令。")
            return

        self.alert_origins[sender_id] = origin
        await self.put_kv_data("alert_origins", self.alert_origins)
        yield event.plain_result(f"已将 QQ {sender_id} 注册为告警接收者。")

    @filter.command("unregister_alert_origin", alias={"取消注册告警"})
    async def unregister_alert_origin(self, event: AstrMessageEvent):
        """取消当前 QQ 的告警接收注册"""
        sender_id = str(event.get_sender_id())
        if sender_id in self.alert_origins:
            self.alert_origins.pop(sender_id)
            await self.put_kv_data("alert_origins", self.alert_origins)
            yield event.plain_result(f"已取消 QQ {sender_id} 的告警接收注册。")
            return

        yield event.plain_result(f"QQ {sender_id} 尚未注册为告警接收者。")

    @filter.command("blocked_senders", alias={"阻断列表", "阻断状态"})
    async def blocked_senders_status(self, event: AstrMessageEvent):
        """查看当前被停止聊天的用户列表"""
        now_ts = time.time()
        active_blocks = []
        for qq, until in self.blocked_senders.items():
            remaining = int(until - now_ts)
            if remaining > 0:
                active_blocks.append(f"QQ {qq} - 剩余 {remaining} 秒")

        if not active_blocks:
            yield event.plain_result("当前没有被停止聊天的用户。")
            return

        yield event.plain_result("当前被停止聊天的用户：\n" + "\n".join(active_blocks))

    @filter.command("unblock_sender", alias={"解除阻断", "取消阻断"})
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def unblock_sender(self, event: AstrMessageEvent):
        """解除指定 QQ 的停止聊天阻断"""
        parts = event.message_str.strip().split()
        if len(parts) < 2:
            yield event.plain_result("请指定要解除阻断的 QQ 号，例如：/unblock_sender 123456789")
            return

        qq = parts[1].strip()
        if qq in self.blocked_senders:
            self.blocked_senders.pop(qq)
            await self.put_kv_data("blocked_senders", self.blocked_senders)
            yield event.plain_result(f"已解除 QQ {qq} 的停止聊天阻断。")
        else:
            yield event.plain_result(f"QQ {qq} 当前没有被停止聊天。")

    @filter.command("clear_blocked_senders", alias={"清除阻断", "解除所有阻断", "清除阻断列表"})
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def clear_blocked_senders(self, event: AstrMessageEvent):
        """清除所有停止聊天的用户阻断记录"""
        self.blocked_senders = {}
        await self.put_kv_data("blocked_senders", self.blocked_senders)
        yield event.plain_result("已清除所有被停止聊天的用户记录。")

    async def terminate(self):
        """插件卸载时的清理工作"""
        logger.info("关键词告警插件已卸载")
