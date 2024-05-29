# 基础镜像
FROM ubuntu:22.04

# Set maintainer information
LABEL maintainer="your-email@example.com"

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive


# Install Python 3.11
RUN apt-get update && \
    apt-get install -y python3.11 python3.11-venv python3.11-dev --quiet && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    apt-get install -y python3-pip



# 设置工作目录
WORKDIR /app

# 复制应用程序代码到容器中
COPY . .

# 安装依赖包
RUN pip install -r requirements.txt

# 暴露两个端口
EXPOSE 8000
EXPOSE 8001

# 启动应用
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:8000 app:app1 --workers 4 --threads 4 --preload & gunicorn -b 0.0.0.0:8001 app:app2 --workers 4 --threads 4 --preload"]
