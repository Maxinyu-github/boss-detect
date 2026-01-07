# Boss Detect - 老板探测器 🔍

一个用于检测局域网中特定设备（老板的手机）并通过消息服务发送通知的工具。

## 功能特性

- ✅ **网络检测**: 通过ARP扫描检测局域网中的设备
- ✅ **MAC地址匹配**: 精确识别目标设备的MAC地址
- ✅ **多种通知方式**: 支持PushDeer、自定义Webhook等
- ✅ **智能防抖**: 支持确认检测和通知冷却时间，避免误报和重复通知
- ✅ **Docker支持**: 提供Docker和Docker Compose部署方式
- ✅ **跨平台**: 支持Windows、Linux等平台

## 快速开始

### 方式一：Docker Compose（推荐）

1. **克隆仓库**
```bash
git clone https://github.com/Maxinyu-github/boss-detect.git
cd boss-detect
```

2. **配置参数**
```bash
# 复制配置文件模板
cp config.ini.example config.ini

# 编辑配置文件，填写必要信息
vim config.ini
```

需要配置的关键参数：
- `boss_mac`: 老板手机的MAC地址（必填）
- `pushdeer_key`: PushDeer推送Key（从 https://www.pushdeer.com 获取）

3. **启动服务**
```bash
# 使用Docker Compose启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 方式二：直接运行Python脚本

1. **安装依赖**
```bash
# 安装Python依赖
pip install -r requirements.txt

# Linux需要安装libpcap
# Ubuntu/Debian:
sudo apt-get install libpcap-dev

# CentOS/RHEL:
sudo yum install libpcap-devel
```

2. **配置参数**
```bash
cp config.ini.example config.ini
vim config.ini
```

3. **运行程序**
```bash
# Linux需要root权限进行网络扫描
sudo python3 boss_detect.py

# Windows以管理员权限运行PowerShell
python boss_detect.py
```

## 配置说明

### 网络配置 `[network]`

| 参数 | 说明 | 示例 |
|------|------|------|
| `boss_mac` | 老板手机的MAC地址（必填） | `aa:bb:cc:dd:ee:ff` |
| `boss_ip` | 老板手机的IP地址（可选） | `192.168.1.100` |
| `scan_interval` | 扫描间隔（秒） | `30` |
| `network_interface` | 网络接口（可选，留空自动检测） | `eth0` 或 `wlan0` |

### 通知配置 `[notification]`

| 参数 | 说明 | 示例 |
|------|------|------|
| `service_type` | 通知服务类型 | `pushdeer` 或 `webhook` |
| `pushdeer_key` | PushDeer推送Key | 从官网获取 |
| `webhook_url` | 自定义Webhook URL | `https://your-webhook.com/api` |
| `notification_title` | 通知标题 | `🚨 老板来了！` |
| `notification_message` | 通知内容 | 自定义消息 |

### 高级配置 `[advanced]`

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `confirmation_count` | 连续检测确认次数 | `2` |
| `notification_cooldown` | 通知冷却时间（秒） | `300` |

## 如何获取手机MAC地址

### 方法一：通过手机设置查看

**iOS:**
1. 设置 → 通用 → 关于本机
2. 查看"Wi-Fi地址"

**Android:**
1. 设置 → 关于手机 → 状态
2. 查看"Wi-Fi MAC地址"

### 方法二：通过路由器查看

1. 登录路由器管理界面
2. 查看已连接设备列表
3. 找到目标设备的MAC地址

### 方法三：使用网络扫描工具

```bash
# Linux
sudo arp-scan --localnet

# 或使用nmap
sudo nmap -sn 192.168.1.0/24

# Windows
arp -a
```

## 通知服务配置

### PushDeer（推荐）

PushDeer是一个开源的消息推送服务，支持推送到微信。

1. 访问 https://www.pushdeer.com
2. 注册账号并登录
3. 获取推送Key
4. 在配置文件中填写`pushdeer_key`

### 自定义Webhook

如果使用自定义Webhook，程序会发送如下格式的JSON数据：

```json
{
  "title": "🚨 老板来了！",
  "message": "检测到老板的手机已连接到局域网，请注意！",
  "timestamp": 1234567890
}
```

## Docker部署详细说明

### 构建镜像
```bash
docker build -t boss-detect .
```

### 运行容器
```bash
docker run -d \
  --name boss-detect \
  --network host \
  --cap-add NET_ADMIN \
  --cap-add NET_RAW \
  --privileged \
  -v $(pwd)/config.ini:/app/config.ini:ro \
  -v $(pwd)/logs:/app/logs \
  -e TZ=Asia/Shanghai \
  --restart unless-stopped \
  boss-detect
```

### 查看日志
```bash
# 实时日志
docker logs -f boss-detect

# 查看日志文件
tail -f logs/boss-detect.log
```

### 停止服务
```bash
docker-compose down
# 或
docker stop boss-detect
```

## 工作原理

1. **多方法检测**: 程序采用三重检测策略确保可靠性
   - **ICMP Ping探测**: 如果配置了目标IP，优先使用ping主动探测设备
   - **ARP缓存检查**: 检查系统ARP缓存，可发现已连接但不活跃的设备
   - **ARP网络扫描**: 广播ARP请求扫描整个局域网段
2. **MAC地址匹配**: 将检测结果与配置的目标MAC地址进行比对
3. **确认检测**: 连续检测N次（默认2次）确认设备在线，避免误报
4. **发送通知**: 通过PushDeer或Webhook发送通知消息
5. **冷却机制**: 在冷却时间内（默认5分钟）不重复发送通知

### 检测策略详解

程序采用智能多层检测策略，大幅提升检测成功率：

- **场景1 - 已知IP地址**: 先ping目标IP确认在线，再通过ARP验证MAC地址
- **场景2 - 设备已连接**: 检查系统ARP缓存，即使设备不活跃也能被发现
- **场景3 - 主动发现**: 广播ARP扫描整个网段，发现新连接的设备

这种多层策略特别适用于移动设备（如手机）的检测，即使设备处于省电模式或待机状态，也能被有效检测到。

## 注意事项

1. **权限要求**: 网络扫描需要管理员/root权限
2. **网络要求**: 程序需要与目标设备在同一局域网内
3. **防火墙**: 确保防火墙允许ARP和ICMP数据包
4. **Docker网络**: 使用`host`网络模式以访问宿主机网络
5. **隐私提醒**: 请遵守相关法律法规，仅用于合法用途

## 故障排除

### 无法检测到设备

**常见原因及解决方案：**

1. **MAC地址配置错误**
   - 确认MAC地址格式正确（支持 `:` 或 `-` 分隔符）
   - 注意大小写（程序会自动转换，但建议使用小写）

2. **设备未连接到同一网络**
   - 确认目标设备已连接到Wi-Fi
   - 确认与运行程序的设备在同一局域网

3. **权限不足**
   - Linux/Mac: 使用 `sudo` 运行程序
   - Windows: 以管理员权限运行
   - Docker: 确保添加了 `--cap-add NET_ADMIN --cap-add NET_RAW`

4. **建议配置IP地址**
   - 如果知道目标设备的IP地址，强烈建议在配置文件中填写
   - 配置IP后会启用ping探测，大幅提升检测成功率
   - 可从路由器管理界面查看设备IP，或使用DHCP预留功能固定IP

5. **网络接口选择**
   - 如果有多个网络接口，尝试手动指定正确的接口
   - 使用 `ip addr` (Linux) 或 `ipconfig` (Windows) 查看可用接口

6. **移动设备省电模式**
   - 某些设备在息屏后会减少网络活动
   - 程序的ARP缓存检查功能可以检测到这类设备

### 通知发送失败

1. 检查网络连接
2. 验证PushDeer Key或Webhook URL是否正确
3. 查看日志文件了解详细错误信息

### Docker容器无法扫描网络

1. 确认使用了`--network host`模式
2. 确认添加了必要的网络权限（NET_ADMIN、NET_RAW）
3. 某些系统可能需要`--privileged`标志

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 免责声明

本工具仅供学习和研究使用，使用者需自行承担使用本工具的法律责任。请遵守当地法律法规，不得用于非法用途。