# syscall_dig

`dify-sandbox` の Python sandbox で必要になる syscall を洗い出すための Docker 実行環境です。

## 使い方

1. [test.py](./test.py) を、検証したい Dify Code ノードのコードに置き換えます。呼び出し可能な `main()` を定義してください。
2. [inputs.json](./inputs.json) に、`main()` へ渡す引数を JSON オブジェクトで設定します。
3. 外部パッケージを使う場合は [requirements.txt](./requirements.txt) に追加します。
4. 次のコマンドを実行します。

```bash
docker compose run --rm syscall-dig
```

成功すると、必要な syscall と、dify-sandbox のデフォルト許可リストに対して追加が必要な syscall が表示されます。

```text
Following syscalls are required: 0,1,3,...
...
Additional required (...): ...
```

入力の設定例、出力の確認方法、分岐のあるコードを検証するときの注意点、比較レポートの読み方、外部パッケージの管理方法は [詳細な使い方](./docs/detailed-usage.md) を参照してください。
