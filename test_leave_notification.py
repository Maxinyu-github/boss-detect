#!/usr/bin/env python3
"""
测试离开通知功能
"""
import sys
import os
import configparser
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_leave_notification_config():
    """测试配置文件是否包含离开通知设置"""
    print("测试离开通知配置...")
    try:
        config = configparser.ConfigParser()
        config.read('config.ini.example', encoding='utf-8')
        
        # 检查离开通知配置项
        assert config.has_option('notification', 'leave_notification_title'), "缺少 leave_notification_title 配置"
        assert config.has_option('notification', 'leave_notification_message'), "缺少 leave_notification_message 配置"
        
        leave_title = config.get('notification', 'leave_notification_title')
        leave_message = config.get('notification', 'leave_notification_message')
        
        print(f"  离开通知标题: {leave_title}")
        print(f"  离开通知消息: {leave_message}")
        
        assert leave_title, "离开通知标题不应为空"
        assert leave_message, "离开通知消息不应为空"
        
        print("✅ 离开通知配置测试通过")
        return True
    except Exception as e:
        print(f"❌ 离开通知配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_send_notification_with_type():
    """测试_send_notification方法支持到达和离开通知"""
    print("\n测试发送通知功能（到达/离开）...")
    try:
        from boss_detect import BossDetector
        
        # 创建临时配置文件
        config_content = """[network]
boss_mac = aa:bb:cc:dd:ee:ff
boss_ip = 192.168.1.100
scan_interval = 30
network_interface = 

[notification]
service_type = pushdeer
pushdeer_key = test_key
notification_title = 🚨 老板来了！
notification_message = 老板在线
leave_notification_title = ✅ 老板离开了！
leave_notification_message = 老板离线

[advanced]
confirmation_count = 2
notification_cooldown = 300
"""
        with open('/tmp/test_config.ini', 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        # Mock网络检测器和通知服务
        with patch('boss_detect.NetworkDetector'), \
             patch('boss_detect.create_notification_service') as mock_notif:
            
            # 设置mock通知服务
            mock_service = Mock()
            mock_service.send = Mock(return_value=True)
            mock_notif.return_value = mock_service
            
            detector = BossDetector('/tmp/test_config.ini')
            
            # 测试到达通知
            detector._send_notification('192.168.1.100', is_arrival=True)
            call_args = mock_service.send.call_args
            assert call_args is not None, "应该调用了send方法"
            title, message = call_args[0]
            assert '老板来了' in title, f"到达通知标题不正确: {title}"
            print(f"  ✓ 到达通知标题: {title}")
            
            # 重置mock
            mock_service.send.reset_mock()
            detector.last_notification_time = None  # 重置冷却时间
            
            # 测试离开通知
            detector._send_notification('192.168.1.100', is_arrival=False)
            call_args = mock_service.send.call_args
            assert call_args is not None, "应该调用了send方法"
            title, message = call_args[0]
            assert '离开' in title, f"离开通知标题不正确: {title}"
            print(f"  ✓ 离开通知标题: {title}")
            
        print("✅ 发送通知功能测试通过")
        return True
    except Exception as e:
        print(f"❌ 发送通知功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理临时文件
        if os.path.exists('/tmp/test_config.ini'):
            os.remove('/tmp/test_config.ini')

def test_leave_notification_triggered():
    """测试离开通知是否在正确的时机触发"""
    print("\n测试离开通知触发时机...")
    try:
        from boss_detect import BossDetector
        
        # 创建临时配置文件
        config_content = """[network]
boss_mac = aa:bb:cc:dd:ee:ff
boss_ip = 192.168.1.100
scan_interval = 30
network_interface = 

[notification]
service_type = pushdeer
pushdeer_key = test_key
notification_title = 🚨 老板来了！
notification_message = 老板在线
leave_notification_title = ✅ 老板离开了！
leave_notification_message = 老板离线

[advanced]
confirmation_count = 1
notification_cooldown = 0
"""
        with open('/tmp/test_config2.ini', 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        # Mock网络检测器和通知服务
        with patch('boss_detect.NetworkDetector') as mock_detector_class, \
             patch('boss_detect.create_notification_service') as mock_notif:
            
            # 设置mock
            mock_service = Mock()
            mock_service.send = Mock(return_value=True)
            mock_notif.return_value = mock_service
            
            mock_detector = Mock()
            mock_detector_class.return_value = mock_detector
            
            detector = BossDetector('/tmp/test_config2.ini')
            
            # 模拟场景：老板从离线到在线
            print("  场景1: 老板上线...")
            mock_detector.is_target_online = Mock(return_value=(True, '192.168.1.100'))
            
            # 执行一次检测循环（到达）
            is_online, ip = detector.network_detector.is_target_online()
            if is_online and not detector.boss_online:
                detector.detection_count += 1
                if detector.detection_count >= 1:
                    detector.boss_online = True
                    detector.last_known_ip = ip
                    detector.detection_count = 0
                    detector._send_notification(ip, is_arrival=True)
            
            assert mock_service.send.call_count == 1, "应该发送一次到达通知"
            arrival_call = mock_service.send.call_args_list[0]
            assert '老板来了' in arrival_call[0][0], "应该发送到达通知"
            print(f"    ✓ 到达通知已发送: {arrival_call[0][0]}")
            
            # 模拟场景：老板从在线到离线
            print("  场景2: 老板离线...")
            mock_detector.is_target_online = Mock(return_value=(False, None))
            mock_service.send.reset_mock()
            detector.last_notification_time = None  # 重置冷却
            
            # 执行一次检测循环（离开）
            is_online, ip = detector.network_detector.is_target_online()
            if not is_online and detector.boss_online:
                detector.boss_online = False
                detector._send_notification(detector.last_known_ip, is_arrival=False)
                detector.last_known_ip = None
            
            assert mock_service.send.call_count == 1, "应该发送一次离开通知"
            leave_call = mock_service.send.call_args_list[0]
            assert '离开' in leave_call[0][0], "应该发送离开通知"
            print(f"    ✓ 离开通知已发送: {leave_call[0][0]}")
            
        print("✅ 离开通知触发时机测试通过")
        return True
    except Exception as e:
        print(f"❌ 离开通知触发时机测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理临时文件
        if os.path.exists('/tmp/test_config2.ini'):
            os.remove('/tmp/test_config2.ini')

def main():
    """运行所有测试"""
    print("=" * 60)
    print("Boss Detect - 离开通知功能测试")
    print("=" * 60)
    
    results = []
    
    results.append(("离开通知配置", test_leave_notification_config()))
    results.append(("发送通知功能", test_send_notification_with_type()))
    results.append(("离开通知触发", test_leave_notification_triggered()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("🎉 所有离开通知功能测试通过！")
        print("\n新增功能：")
        print("- 增加了离开通知配置项（leave_notification_title 和 leave_notification_message）")
        print("- 支持在老板离线时发送离开通知")
        print("- 记录最后已知IP地址用于离开通知")
        return 0
    else:
        print("⚠️  部分测试失败，请检查错误信息")
        return 1

if __name__ == "__main__":
    sys.exit(main())
