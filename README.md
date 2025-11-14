# Fetch TLS

## 簡介

   ```bash
   docker build -t fetch-tls .
   docker run --name fetch-tls -p 8080:8080 fetch-tls
   curl "http://localhost:8080/?url=https://www.ftvnews.com.tw/news/detail/2025B14W0369" -o fetched_content.html
   ```

## 發布 image 到 Docker Hub 並拉取

   ```bash
   docker login
   docker tag fetch-tls winstontang8864/fetch-tls
   docker push winstontang8864/fetch-tls
   docker pull winstontang8864/fetch-tls
   docker run -p 8080:8080 winstontang8864/fetch-tls
   ```
