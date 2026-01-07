#!/usr/bin/env python3
"""
测试脚本 - 验证各模块功能
"""
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    print("测试模块导入...")
    try:
        import network_detector
        import notification
        import boss_detect
        print("✅ 所有模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_network_detector():
    """测试网络检测器"""
    print("\n测试网络检测器...")
    try:
        from network_detector import NetworkDetector
        
        # 创建检测器实例
        detector = NetworkDetector("aa:bb:cc:dd:ee:ff", "192.168.1.1")
        print(f"✅ 网络检测器创建成功")
        
        # 测试网络范围获取
        network_range = detector._get_local_network_range()
        print(f"✅ 检测到网络范围: {network_range}")
        
        return True
    except Exception as e:
        print(f"❌ 网络检测器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_notification():
    """测试通知服务"""
    print("\n测试通知服务...")
    try:
        from notification import create_notification_service, PushDeerNotification, WebhookNotification
        
        # 测试PushDeer创建
        pushdeer = PushDeerNotification("test_key")
        print("✅ PushDeer服务创建成功")
        
        # 测试Webhook创建
        webhook = WebhookNotification("https://example.com/webhook")
        print("✅ Webhook服务创建成功")
        
        # 测试工厂方法
        service = create_notification_service("pushdeer", pushdeer_key="test")
        print("✅ 通知服务工厂方法正常")
        
        return True
    except Exception as e:
        print(f"❌ 通知服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_example():
    """测试配置文件示例"""
    print("\n测试配置文件...")
    try:
        import configparser
        config = configparser.ConfigParser()
        config.read('config.ini.example', encoding='utf-8')
        
        # 检查必要的配置项
        assert config.has_section('network'), "缺少 [network] 节"
        assert config.has_section('notification'), "缺少 [notification] 节"
        assert config.has_section('advanced'), "缺少 [advanced] 节"
        
        assert config.has_option('network', 'boss_mac'), "缺少 boss_mac 配置"
        assert config.has_option('notification', 'service_type'), "缺少 service_type 配置"
        
        print("✅ 配置文件结构正确")
        return True
    except Exception as e:
        print(f"❌ 配置文件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    print("=" * 60)
    print("Boss Detect - 模块测试")
    print("=" * 60)
    
    results = []
    
    results.append(("模块导入", test_imports()))
    results.append(("网络检测器", test_network_detector()))
    results.append(("通知服务", test_notification()))
    results.append(("配置文件", test_config_example()))
    
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
        print("🎉 所有测试通过！")
        return 0
    else:
        print("⚠️  部分测试失败，请检查错误信息")
        return 1

if __name__ == "__main__":
    sys.exit(main())
