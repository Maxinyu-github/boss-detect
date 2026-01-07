#!/usr/bin/env python3
"""
Boss Detect - 老板探测器主程序
检测局域网中老板的手机并发送通知
"""
import time
import logging
import configparser
import os
import sys
from datetime import datetime, timedelta

from network_detector import NetworkDetector
from notification import create_notification_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('boss-detect.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class BossDetector:
    """老板检测器主类"""
    
    def __init__(self, config_file='config.ini'):
        """
        初始化老板检测器
        
        Args:
            config_file: 配置文件路径
        """
        self.config = self._load_config(config_file)
        self.network_detector = self._init_network_detector()
        self.notification_service = self._init_notification_service()
        
        # 状态追踪
        self.boss_online = False
        self.last_notification_time = None
        self.detection_count = 0
        
        logger.info("Boss Detector 初始化完成")
    
    def _load_config(self, config_file):
        """
        加载配置文件
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            configparser.ConfigParser: 配置对象
        """
        if not os.path.exists(config_file):
            logger.error(f"配置文件不存在: {config_file}")
            logger.error("请复制 config.ini.example 为 config.ini 并填写配置")
            sys.exit(1)
        
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')
        
        logger.info(f"配置文件加载成功: {config_file}")
        return config
    
    def _init_network_detector(self):
        """初始化网络检测器"""
        boss_mac = self.config.get('network', 'boss_mac')
        boss_ip = self.config.get('network', 'boss_ip', fallback='')
        network_interface = self.config.get('network', 'network_interface', fallback='')
        
        if not boss_mac:
            logger.error("未配置老板的MAC地址")
            sys.exit(1)
        
        return NetworkDetector(
            target_mac=boss_mac,
            target_ip=boss_ip if boss_ip else None,
            network_interface=network_interface if network_interface else None
        )
    
    def _init_notification_service(self):
        """初始化通知服务"""
        service_type = self.config.get('notification', 'service_type')
        
        kwargs = {}
        if service_type == 'pushdeer':
            kwargs['pushdeer_key'] = self.config.get('notification', 'pushdeer_key')
            if not kwargs['pushdeer_key']:
                logger.error("未配置PushDeer Key")
                sys.exit(1)
        elif service_type == 'webhook':
            kwargs['webhook_url'] = self.config.get('notification', 'webhook_url')
            if not kwargs['webhook_url']:
                logger.error("未配置Webhook URL")
                sys.exit(1)
        
        return create_notification_service(service_type, **kwargs)
    
    def _should_send_notification(self):
        """
        判断是否应该发送通知（考虑冷却时间）
        
        Returns:
            bool: 是否应该发送通知
        """
        if self.last_notification_time is None:
            return True
        
        cooldown = self.config.getint('advanced', 'notification_cooldown', fallback=300)
        time_since_last = datetime.now() - self.last_notification_time
        
        return time_since_last.total_seconds() > cooldown
    
    def _send_notification(self, ip):
        """
        发送通知
        
        Args:
            ip: 检测到的IP地址
        """
        if not self._should_send_notification():
            logger.info("通知在冷却期内，跳过发送")
            return
        
        title = self.config.get('notification', 'notification_title')
        message = self.config.get('notification', 'notification_message')
        
        # 添加详细信息
        detail = f"\n\n**检测信息:**\n- 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n- IP地址: {ip}\n- MAC地址: {self.config.get('network', 'boss_mac')}"
        full_message = message + detail
        
        success = self.notification_service.send(title, full_message)
        
        if success:
            self.last_notification_time = datetime.now()
            logger.info("通知发送成功")
        else:
            logger.error("通知发送失败")
    
    def run(self):
        """运行检测循环"""
        scan_interval = self.config.getint('network', 'scan_interval', fallback=30)
        confirmation_count = self.config.getint('advanced', 'confirmation_count', fallback=2)
        
        logger.info("=" * 60)
        logger.info("Boss Detector 开始运行")
        logger.info(f"扫描间隔: {scan_interval}秒")
        logger.info(f"确认次数: {confirmation_count}次")
        logger.info("=" * 60)
        
        try:
            while True:
                is_online, ip = self.network_detector.is_target_online()
                
                if is_online:
                    if not self.boss_online:
                        # 从离线变为在线，增加检测计数
                        self.detection_count += 1
                        logger.info(f"检测到目标设备 ({self.detection_count}/{confirmation_count})")
                        
                        if self.detection_count >= confirmation_count:
                            # 确认在线
                            logger.warning("🚨 确认老板在线！")
                            self.boss_online = True
                            self.detection_count = 0
                            self._send_notification(ip)
                    else:
                        # 持续在线
                        logger.debug("老板仍在线")
                else:
                    if self.boss_online:
                        # 从在线变为离线
                        logger.info("✅ 老板已离线")
                        self.boss_online = False
                    
                    # 重置检测计数
                    self.detection_count = 0
                
                # 等待下次扫描
                time.sleep(scan_interval)
                
        except KeyboardInterrupt:
            logger.info("\n检测程序已停止")
        except Exception as e:
            logger.error(f"运行时错误: {e}", exc_info=True)
            raise


def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════╗
║        Boss Detect - 老板探测器          ║
║     局域网设备检测与消息推送系统         ║
╚══════════════════════════════════════════╝
    """)
    
    # 检查是否以root/管理员权限运行
    if os.name != 'nt' and os.geteuid() != 0:
        logger.warning("警告: 建议以root权限运行以获得更好的网络扫描效果")
        logger.warning("使用命令: sudo python3 boss_detect.py")
    
    detector = BossDetector()
    detector.run()


if __name__ == "__main__":
    main()
