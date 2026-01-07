#!/usr/bin/env python3
"""
网络检测模块 - 用于检测局域网中的设备
"""
import time
import logging
from scapy.all import ARP, Ether, srp, ICMP, IP, sr1
import socket
import subprocess
import platform
import os

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
    
    def _ping_host(self, ip):
        """
        使用ICMP ping检测主机是否在线
        
        Args:
            ip: 目标IP地址
            
        Returns:
            bool: 是否在线
        """
        try:
            # 首先尝试使用scapy发送ICMP包（更可靠）
            packet = IP(dst=ip)/ICMP()
            response = sr1(packet, timeout=2, verbose=0)
            if response:
                logger.debug(f"ICMP ping成功: {ip}")
                return True
        except Exception as e:
            logger.debug(f"Scapy ICMP ping失败: {e}")
        
        # 如果scapy失败，尝试使用系统ping命令作为备选
        try:
            # 根据操作系统选择ping命令参数
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            count = '1'
            # 在Linux/Mac上使用-W/-w设置超时
            if platform.system().lower() != 'windows':
                command = ['ping', param, count, '-W', '2', ip]
            else:
                command = ['ping', param, count, '-w', '2000', ip]
            
            # 执行ping命令，禁止输出
            result = subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3
            )
            
            if result.returncode == 0:
                logger.debug(f"系统ping成功: {ip}")
                return True
        except Exception as e:
            logger.debug(f"系统ping失败: {e}")
        
        return False
    
    def _check_arp_cache(self, target_mac):
        """
        检查系统ARP缓存中是否有目标MAC地址
        
        Args:
            target_mac: 目标MAC地址
            
        Returns:
            tuple: (bool, str) - (是否找到, IP地址)
        """
        try:
            # 根据操作系统选择ARP命令
            if platform.system().lower() == 'windows':
                result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=5)
            else:
                result = subprocess.run(['arp', '-n'], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                output = result.stdout.lower()
                target_mac_normalized = target_mac.replace(':', '-')  # Windows使用-分隔符
                
                for line in output.split('\n'):
                    if target_mac in line or target_mac_normalized in line:
                        # 尝试提取IP地址
                        parts = line.split()
                        for part in parts:
                            # 检查是否是IP地址格式
                            if '.' in part and len(part.split('.')) == 4:
                                try:
                                    # 验证是否为有效IP
                                    socket.inet_aton(part)
                                    logger.info(f"在ARP缓存中发现目标设备: IP={part}, MAC={target_mac}")
                                    return True, part
                                except socket.error:
                                    continue
        except Exception as e:
            logger.debug(f"检查ARP缓存失败: {e}")
        
        return False, None
    
    def is_target_online(self, ip_range=None):
        """
        检测目标设备是否在线（使用多种方法）
        
        Args:
            ip_range: IP地址范围
            
        Returns:
            tuple: (bool, str) - (是否在线, IP地址)
        """
        # 方法1: 如果知道目标IP，先尝试ping
        if self.target_ip:
            logger.debug(f"尝试ping目标IP: {self.target_ip}")
            if self._ping_host(self.target_ip):
                logger.info(f"通过ping发现目标设备在线: {self.target_ip}")
                # ping成功后，验证MAC地址（通过ARP缓存或新的ARP请求）
                found, ip = self._check_arp_cache(self.target_mac)
                if found and ip == self.target_ip:
                    return True, self.target_ip
                # 如果缓存中没有，发送ARP请求获取MAC
                devices = self.scan_network(f"{self.target_ip}/32")
                for ip, mac in devices:
                    if mac.lower() == self.target_mac and ip == self.target_ip:
                        logger.info(f"Ping+ARP验证成功: {ip}")
                        return True, self.target_ip
        
        # 方法2: 检查ARP缓存（适用于已连接但不活跃的设备）
        logger.debug("检查ARP缓存...")
        found, ip = self._check_arp_cache(self.target_mac)
        if found:
            # 如果在缓存中找到，尝试ping验证设备是否真的在线
            if self._ping_host(ip):
                logger.info(f"通过ARP缓存+ping验证设备在线: {ip}")
                return True, ip
            else:
                logger.debug(f"ARP缓存中找到设备但ping失败，可能已离线")
        
        # 方法3: ARP扫描网络（主动发现）
        logger.debug("执行ARP网络扫描...")
        devices = self.scan_network(ip_range)
        
        for ip, mac in devices:
            mac = mac.lower()
            if mac == self.target_mac:
                logger.info(f"通过ARP扫描发现目标设备! IP: {ip}, MAC: {mac}")
                return True, ip
            # 如果指定了IP地址，也检查IP
            if self.target_ip and ip == self.target_ip:
                logger.info(f"通过IP地址发现目标设备! IP: {ip}, MAC: {mac}")
                return True, ip
        
        logger.debug("所有检测方法均未发现目标设备")
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
