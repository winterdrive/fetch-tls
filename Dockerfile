# 使用官方 curl-impersonate image
FROM lwthiker/curl-impersonate:0.6-chrome

# 安裝 Python + Flask
RUN apk update && apk add --no-cache python3 py3-pip && \
    pip3 install flask

# 拷貝 Flask app
COPY app.py /app/app.py
WORKDIR /app

# Cloud Run 預設 PORT
ENV PORT=8080

# 啟動 Flask app
CMD ["python3", "app.py"]
