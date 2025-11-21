# Fetch TLS

## 簡介

首先，請透過 Docker build image 並啟動 container：

```bash
docker build -t fetch-tls .
docker run --name fetch-tls -p 8080:8080 fetch-tls
```

接著，請根據你的作業系統，選擇對應的指令來呼叫 API。

---

### Linux / macOS

在 Linux, macOS 或其他 Unix-like 環境中，請使用以下 `curl` 指令：

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"url": "https://www.ftvnews.com.tw/news/detail/2025B14W0369"}' \
  http://localhost:8080/
```

---

### Windows (PowerShell)

在 Windows PowerShell 環境中，最穩定的方法是使用 `Invoke-WebRequest` 指令：

```powershell
Invoke-WebRequest -Uri http://localhost:8080/ -Method POST -ContentType "application/json" -Body '{"url": "https://www.ftvnews.com.tw/news/detail/2025B14W0369"}'
```

---

## 發布 image 到 Docker Hub 並拉取

```bash
docker login
docker tag fetch-tls winstontang8864/fetch-tls
docker push winstontang8864/fetch-tls
docker pull winstontang8864/fetch-tls
docker run -p 8080:8080 winstontang8864/fetch-tls
```
