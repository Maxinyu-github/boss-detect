#!/usr/bin/env python3
"""
通知模块 - 支持多种消息推送服务
"""
import logging
import requests
import json
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NotificationService:
    """通知服务基类"""
    
    def send(self, title, message):
        """发送通知"""
        raise NotImplementedError


class PushDeerNotification(NotificationService):
    """PushDeer推送服务"""
    
    def __init__(self, pushkey):
        """
        初始化PushDeer服务
        
        Args:
            pushkey: PushDeer推送Key
        """
        self.pushkey = pushkey
        self.api_url = "https://api2.pushdeer.com/message/push"
        logger.info("初始化PushDeer通知服务")
    
    def send(self, title, message):
        """
        发送PushDeer通知
        
        Args:
            title: 通知标题
            message: 通知内容
            
        Returns:
            bool: 是否发送成功
        """
        try:
            data = {
                "pushkey": self.pushkey,
                "text": title,
                "desp": message,
                "type": "markdown"
            }
            
            response = requests.post(self.api_url, data=data, timeout=10)
            result = response.json()
            
            if result.get("code") == 0:
                logger.info("PushDeer通知发送成功")
                return True
            else:
                logger.error(f"PushDeer通知发送失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"发送PushDeer通知时出错: {e}")
            return False


class WebhookNotification(NotificationService):
    """自定义Webhook推送服务"""
    
    def __init__(self, webhook_url):
        """
        初始化Webhook服务
        
        Args:
            webhook_url: Webhook URL
        """
        self.webhook_url = webhook_url
        logger.info(f"初始化Webhook通知服务: {webhook_url}")
    
    def send(self, title, message):
        """
        发送Webhook通知
        
        Args:
            title: 通知标题
            message: 通知内容
            
        Returns:
            bool: 是否发送成功
        """
        try:
            data = {
                "title": title,
                "message": message,
                "timestamp": int(time.time())
            }
            
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                self.webhook_url, 
                data=json.dumps(data), 
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Webhook通知发送成功")
                return True
            else:
                logger.error(f"Webhook通知发送失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"发送Webhook通知时出错: {e}")
            return False


def create_notification_service(service_type, **kwargs):
    """
    创建通知服务实例
    
    Args:
        service_type: 服务类型 ("pushdeer" 或 "webhook")
        **kwargs: 服务相关参数
        
    Returns:
        NotificationService: 通知服务实例
    """
    if service_type.lower() == "pushdeer":
        pushkey = kwargs.get("pushdeer_key")
        if not pushkey:
            raise ValueError("PushDeer服务需要提供pushdeer_key")
        return PushDeerNotification(pushkey)
    
    elif service_type.lower() == "webhook":
        webhook_url = kwargs.get("webhook_url")
        if not webhook_url:
            raise ValueError("Webhook服务需要提供webhook_url")
        return WebhookNotification(webhook_url)
    
    else:
        raise ValueError(f"不支持的通知服务类型: {service_type}")


if __name__ == "__main__":
    # 测试代码
    import time
    
    # 测试PushDeer (需要实际的pushkey)
    # service = PushDeerNotification("your_pushkey_here")
    # service.send("测试通知", "这是一条测试消息")
    
    print("通知模块加载成功")
