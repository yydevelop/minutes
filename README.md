# minutes

`minutes` は、音声ファイルから会議の議事録を自動生成する Python プロジェクトです。OpenAI の Whisper モデルと GPT-3.5 Turbo モデルを使用して、音声をテキストに変換し、そのテキストをもとに議事録を作成します。

## インストール

このプロジェクトは Python 3.9 以上を必要とします。依存関係のインストールには Poetry を使用します。

```sh
poetry install
```
## 使用方法
```
poetry run python minutes.py
```