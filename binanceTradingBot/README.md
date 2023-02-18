# こちらはMANAUSDT(USD Margined Perpetual)を自動売買するBotのサンプルです。
ロジックが簡単なため、例として公開しています。

### Dockerのビルド
```
bash
docker build . -t binanceTradingBot
```

### Dockerのコンテナを起動
```
bash
docker run -d -it --env-file=.env --name=binanceTradingBot binanceTradingBot
```

### Dockerの起動状況確認
```
bash
docker container logs -t binanceTradingBot
```

### Dockerのコンテナの停止
```
bash
docker stop binanceTradingBot
```

### Dockerのコンテナの削除
```
bash
docker container prune
```
