# 使用官方 curl-impersonate image
FROM lwthiker/curl-impersonate:0.6-chrome

# 安裝 Python + Flask + Functions Framework
RUN apt-get update && apt-get install -y python3 python3-pip && \
    pip3 install flask functions-framework && \
    rm -rf /var/lib/apt/lists/*

# 拷貝 Flask app
COPY app.py /app/app.py
WORKDIR /app

# Cloud Run 預設 PORT
ENV PORT 8080

# 啟動 Functions Framework，target 指向 fetch_url
CMD ["functions-framework", "--target", "fetch_url", "--port", "8080"]
