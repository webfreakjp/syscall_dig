# syscall_dig

`dify-sandbox` の Python sandbox で必要になる syscall をざっくり洗い出すための Docker 実行環境です。

```bash
docker compose run --rm syscall-dig
```

成功すると、最後に次のような形式で必要 syscall の番号が出力されます。

```text
Following syscalls are required: 0,1,3,...
```

## test.py を自分のコードに置き換える場所

基本的には [test.py](./test.py) の `User code starts here.` から `User code ends here.` の間を変更してください。DifySandbox の UI で入力されるコードは、sandbox 初期化用テンプレートの中に埋め込まれて実行される想定なので、この検証用 `test.py` でも同じ位置関係を保ちます。

変更してよい場所:

- `main()` の中身
- `main()` から呼ぶ補助関数の追加
- 自分のコードで必要な `import`

`main()` が引数を受け取る場合でも、`test.py` の実行ラッパーは変更しません。引数に渡すテスト値は [inputs.json](./inputs.json) で管理します。

## スクリプトを入れ替えて検証する手順

### 1. ユーザーコードを入れ替える

[test.py](./test.py) の次のマーカー間だけを、Dify Code ノードのコードに置き換えます。

```python
# User code starts here.

# Dify Code ノードのコード

# User code ends here.
```

マーカー外にはsandbox初期化、`inputs.json` の読み込み、`main()` の呼び出し、結果表示の処理があります。ここはスクリプトを入れ替えるたびに変更する必要はありません。

### 2. `main()` の引数に合わせて Inputs を設定する

[inputs.json](./inputs.json) は、`main()` にキーワード引数として渡すJSONオブジェクトです。トップレベルのキーを `main()` の引数名と完全に一致させます。

たとえば、対象コードが次の場合:

```python
def main(text: str, limit: int = 10) -> dict:
    return {
        "result": text[:limit],
    }
```

`inputs.json` は次のようにします。

```json
{
  "text": "syscall test",
  "limit": 10
}
```

内部では次と同じ形で呼び出されます。

```python
inputs = json.load(inputs_file)
output = main(**inputs)
```

デフォルト値のある引数は `inputs.json` から省略できます。必須引数の不足、存在しない引数名、型の不一致がある場合は、syscall探索前の事前実行でエラーになります。

文字列としてJSONを受け取る引数には、JSONオブジェクトではなくJSON文字列を設定します。

```python
def main(response_body: str) -> dict:
    data = json.loads(response_body)
    return {"id": data["id"]}
```

```json
{
  "response_body": "{\"id\":\"12345\"}"
}
```

実際の認証情報やアクセストークンはコミットせず、syscallの対象経路を通せるダミー値を使ってください。外部サービスへの接続自体を検証する必要がある場合は、別途ネットワークと秘密情報の扱いを設計してください。

### 3. Outputs を確認する

Dify の Code ノードでは、Inputs は `main()` の引数、Outputs は `main()` が返す辞書です。

```python
def main(input_name: str) -> dict:
    return {
        "output_name": input_name,
    }
```

Dify 側では、Input Variable に `input_name`、Output Variable に `output_name` を登録します。Input Variable名は `main()` の引数名、Output Variable名は返却辞書のキーと完全に一致させてください。型も実際に返す値に合わせます。詳しくは [Dify の Code ノード公式ドキュメント](https://docs.dify.ai/ja/cloud/use-dify/nodes/code) を参照してください。

syscall採取側ではOutputsの設定ファイルは不要です。返却辞書がJSONへ変換できることと、対象コードが最後まで正常終了することだけが必要です。

### 4. 外部パッケージを設定して実行する

対象コードが使う外部パッケージを [requirements.txt](./requirements.txt) に設定してから実行します。

```bash
docker compose run --rm syscall-dig
```

実行時は、最初に全syscallを許可した状態で対象コードを1回実行します。この事前実行に失敗した場合は、Pythonの例外を表示して非ゼロで終了し、500回のsyscall探索には進みません。

条件分岐によって使用するライブラリや処理が大きく変わるコードでは、代表的な `inputs.json` ごとにsyscall採取を実行し、得られたsyscallの和集合を使用してください。入力値が対象経路を通らない場合、その経路だけで必要になるsyscallは検出できません。

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
