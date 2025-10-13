步驟 1: 建立和推送新映像

# 建立新版本的 Docker 映像
    docker build -f Dockerfile.prod -t ***REMOVED_ACR_URL***/videoqna-ltw:101301 .

# 登入 ACR
  az login
  az acr login --name ***REMOVED_ACR_NAME***

# 推送映像
  docker push ***REMOVED_ACR_URL***/videoqna-ltw:101301
