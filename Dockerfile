FROM python:3.11-slim

# 安装必要的系统依赖
RUN apt-get update && apt-get install -y \
    net-tools \
    iputils-ping \
    tcpdump \
    libpcap-dev \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY boss_detect.py .
COPY network_detector.py .
COPY notification.py .

# 创建配置文件挂载点
VOLUME ["/app/config"]

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 运行应用
CMD ["python", "boss_detect.py"]
