FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用文件
COPY . .

# 创建必要的目录
RUN mkdir -p \
    /app/data/import \
    /app/data/out_text \
    /app/data/out_mp3 \
    /app/data/out_mp3_merge \
    /app/data/out_mp4 \
    /app/data/images \
    /app/data/tmp \
    /app/data/config

# 创建启动脚本
RUN echo '#!/bin/bash\n\
if [ ! -f /app/data/config/config.json ]; then\n\
    echo "{\n\
    \"chapter_patterns\": [\n\
        {\n\
            \"pattern\": \"第([0-9零一二三四五六七八九十百千万]+)章.*\",\n\
            \"description\": \"数字/中文数字\"\n\
        },\n\
        {\n\
            \"pattern\": \"第([壹贰叁肆伍陆柒捌玖拾佰仟萬]+)章.*\",\n\
            \"description\": \"繁体数字\"\n\
        }\n\
    ]\n\
}" > /app/data/config/config.json\n\
fi\n\
python app.py' > /app/start.sh && chmod +x /app/start.sh

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 设置数据卷
VOLUME ["/app/data/import", "/app/data/out_text", "/app/data/out_mp3", "/app/data/out_mp3_merge", "/app/data/out_mp4", "/app/data/images", "/app/data/tmp", "/app/data/config"]

# 暴露端口
EXPOSE 7860

# 启动命令
CMD ["/app/start.sh"]