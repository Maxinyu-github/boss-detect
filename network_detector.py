#!/usr/bin/env python3
"""
网络检测模块 - 用于检测局域网中的设备
"""
import time
import logging
from scapy.all import ARP, Ether, srp
import socket

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NetworkDetector:
    """网络设备检测器"""
    
    def __init__(self, target_mac, target_ip=None, network_interface=None):
        """
        初始化网络检测器
        
        Args:
            target_mac: 目标MAC地址
            target_ip: 目标IP地址 (可选)
            network_interface: 网络接口 (可选)
        """
        self.target_mac = target_mac.lower().replace('-', ':')
        self.target_ip = target_ip
        self.network_interface = network_interface
        logger.info(f"初始化网络检测器 - 目标MAC: {self.target_mac}, 目标IP: {target_ip}")
    
    def scan_network(self, ip_range=None):
        """
        扫描局域网中的设备
        
        Args:
            ip_range: IP地址范围 (例如: "192.168.1.0/24")
            
        Returns:
            list: 发现的设备列表 [(ip, mac), ...]
        """
        if ip_range is None:
            # 自动获取本地网络段
            ip_range = self._get_local_network_range()
        
        logger.info(f"开始扫描网络: {ip_range}")
        
        try:
            # 创建ARP请求包
            arp = ARP(pdst=ip_range)
            ether = Ether(dst="ff:ff:ff:ff:ff:ff")
            packet = ether/arp
            
            # 发送请求并接收响应
            result = srp(packet, timeout=3, verbose=0, iface=self.network_interface)[0]
            
            devices = []
            for sent, received in result:
                devices.append((received.psrc, received.hwsrc))
            
            logger.info(f"扫描完成，发现 {len(devices)} 个设备")
            return devices
            
        except Exception as e:
            logger.error(f"网络扫描失败: {e}")
            return []
    
    def is_target_online(self, ip_range=None):
        """
        检测目标设备是否在线
        
        Args:
            ip_range: IP地址范围
            
        Returns:
            tuple: (bool, str) - (是否在线, IP地址)
        """
        devices = self.scan_network(ip_range)
        
        for ip, mac in devices:
            mac = mac.lower()
            if mac == self.target_mac:
                logger.info(f"发现目标设备! IP: {ip}, MAC: {mac}")
                return True, ip
            # 如果指定了IP地址，也检查IP
            if self.target_ip and ip == self.target_ip:
                logger.info(f"通过IP地址发现目标设备! IP: {ip}, MAC: {mac}")
                return True, ip
        
        return False, None
    
    def _get_local_network_range(self):
        """
        获取本地网络地址段
        
        Returns:
            str: 网络地址段 (例如: "192.168.1.0/24")
        """
        try:
            # 获取本机IP地址
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # 转换为网络地址段
            ip_parts = local_ip.split('.')
            network_range = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
            
            logger.info(f"自动检测到网络地址段: {network_range}")
            return network_range
            
        except Exception as e:
            logger.warning(f"无法自动检测网络地址段: {e}，使用默认值")
            return "192.168.1.0/24"


if __name__ == "__main__":
    # 测试代码
    detector = NetworkDetector("00:11:22:33:44:55")
    is_online, ip = detector.is_target_online()
    print(f"目标设备在线: {is_online}, IP: {ip}")
