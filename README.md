# syscall_dig

`dify-sandbox` の Python sandbox で必要になる syscall をざっくり洗い出すための Docker 実行環境です。

```bash
docker compose run --rm syscall-dig
```

成功すると、最後に次のような形式で必要 syscall の番号が出力されます。

```text
Following syscalls are required: 0,1,3,...
```

## Architecture

`docker-compose.yml` では `platform: linux/amd64` を指定しています。

syscall 番号は CPU architecture ごとに異なるため、Apple Silicon Mac でも amd64 の syscall 番号を調査できるように固定しています。これに合わせて Dockerfile も `build_amd64.sh` と `config_default_amd64.go` を使います。

arm64 の syscall 番号を調査したい場合は、`platform` を `linux/arm64` に変更し、Dockerfile 側も `build_arm64.sh` と `config_default_arm64.go` を使うように変更してください。

## test.py を自分のコードに置き換える場所

基本的には [test.py](./test.py) の `User code starts here.` から `User code ends here.` の間だけを変更してください。DifySandbox の UI で入力されるコードは、sandbox 初期化用テンプレートの中に埋め込まれて実行される想定なので、この検証用 `test.py` でも同じ位置関係を保ちます。

変更してよい場所:

- `main()` の中身
- `main()` から呼ぶ補助関数の追加
- 自分のコードで必要な `import`

## 外部パッケージを使う場合

このリポジトリでは、検証用に [requirements.txt](./requirements.txt) をコンテナ起動時にインストールする形にしています。外部パッケージを使う場合は `requirements.txt` に追記して、通常通り実行してください。

```txt
requests
numpy
```

```bash
docker compose run --rm syscall-dig
# or
docker compose run --rm syscall-dig install-python-deps # 依存関係だけインストール
```

`docker-compose.yml` では、`requirements.txt` を `/requirements.txt` にマウントし、起動時に `install-python-deps` を実行します。インストール先は chroot 後にも見える `/var/sandbox/sandbox-python/usr/local/lib/python3.11/dist-packages` です。

pip の download cache とインストール済みパッケージは Docker volume に残すため、毎回 image を rebuild する必要はありません。同じ依存関係であれば 2 回目以降は短時間で終わります。

インストール済みパッケージを消して入れ直したい場合は、volume を削除します。

```bash
docker compose down -v
```
