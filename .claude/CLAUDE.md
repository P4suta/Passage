# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Passage is a Python project (v0.1.0) managed with **uv**. Python >=3.12 required. Entry point: `main.py`.

## Common Commands

```bash
uv sync              # Install dependencies / create .venv
uv run main.py       # Run the application
uv add <package>     # Add a dependency
```

## 開発環境

- **すべての開発作業はWSL/Ubuntu内で行うこと。** Windowsホスト側のファイルシステムやシステム設定を直接変更してはならない。
- `/mnt/c/` 以下のWindows側ファイルへの書き込み・削除は禁止。読み取りのみ許可する。
- システムレベルのパッケージインストール(`apt install` 等)は、必ずユーザーに確認してから実行すること。
- 破壊的な操作（`rm -rf`、`git reset --hard`、`git push --force` 等）は、必ずユーザーに確認してから実行すること。

## GitHub認証 (1Password SSH Agent via WSL)

GitHubへのSSH認証およびGitコミット署名は、Windows側の1Passwordで管理されたSSH鍵を使用する。WSLから1PasswordのSSH Agentを利用するための設定は以下の通り。

### SSH接続

WSLからWindowsの1Password SSH Agentを経由してSSH接続を行う。

```bash
# ~/.bashrc または ~/.bash_aliases に追加済み
alias ssh='ssh.exe'
alias ssh-add='ssh-add.exe'
```

```bash
# Git の SSH コマンドとして Windows 側の ssh.exe を使用
git config --global core.sshCommand ssh.exe
```

- `ssh-add.exe -l` で1Passwordに登録された鍵が表示されることを確認できる。
- 接続に問題がある場合は `/mnt/c/Windows/System32/OpenSSH/ssh-add.exe` のフルパスを試すこと。

### Git コミット署名

1Password上のSSH鍵を使ってコミットに署名する。`~/.gitconfig` に以下が設定されている。

```gitconfig
[gpg]
    format = ssh
[commit]
    gpgsign = true
[user]
    signingkey = <1Passwordから取得した公開鍵>
```

- 署名鍵の設定は、1Passwordデスクトップアプリでキーを開き「Configure Commit Signing」→「Configure for Windows Subsystem for Linux (WSL)」を選択して取得する。
- GitHubにも同じ公開鍵を「Signing key」として登録する必要がある。

### トラブルシューティング

- WSLのinteroperabilityが有効であることを確認する（`/etc/wsl.conf` の `[interop]` セクション）。
- `ssh.exe` や `ssh-add.exe` が見つからない場合、Windows側のOpenSSHがインストールされているか確認する。
- Git 2.34.0以上が必要（SSH署名サポート）。

## Git運用規約

### ブランチ戦略（GitHub Flow ベース）

| ブランチ | 用途 | ルール |
|---|---|---|
| `main` | 常にデプロイ可能な安定版 | 直接コミット禁止。PRマージのみ |
| `feature/<name>` | 新機能の開発 | `main` から分岐し、`main` へPRでマージ |
| `fix/<name>` | バグ修正 | `main` から分岐し、`main` へPRでマージ |
| `refactor/<name>` | リファクタリング | `main` から分岐し、`main` へPRでマージ |
| `docs/<name>` | ドキュメント整備 | `main` から分岐し、`main` へPRでマージ |
| `chore/<name>` | CI・設定・依存関係等の雑務 | `main` から分岐し、`main` へPRでマージ |

- `<name>` は英語のケバブケース（例: `feature/user-authentication`, `fix/login-redirect`）。
- ブランチは短命に保つ。1つのブランチで複数の無関係な変更を混ぜない。
- マージ済みのブランチはリモート・ローカルともに速やかに削除する。

### コミットメッセージ規約（Conventional Commits）

```
<type>(<scope>): <subject>
```

- **type**: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `style`, `perf`, `ci`
- **scope**: 変更対象のモジュールや機能（省略可。例: `auth`, `api`, `db`）
- **subject**: 英語・小文字始まり・末尾ピリオドなし・命令形（例: `add user login endpoint`）

例:
```
feat(auth): add JWT token validation
fix(api): handle empty response from external service
refactor(db): extract connection pool into separate module
docs: update README with setup instructions
chore: upgrade dependencies
test(auth): add unit tests for password hashing
```

### コミット粒度

- **1コミット = 1つの論理的変更。** 「なぜこの変更をしたか」が1文で説明できる単位。
- 以下を別々のコミットに分ける：
  - 機能追加とそのテスト（同一コミットでもよいが、テストが大きい場合は分離）
  - リファクタリングと機能変更（混ぜない）
  - フォーマット修正・import整理と実質的なコード変更
  - 依存関係の追加と、その依存を使うコード
- WIP（作業途中）コミットは作業ブランチ内では許容するが、PR前に `git rebase -i` で整理すること。

### PRとマージ

- PRのタイトルはコミットメッセージと同じ Conventional Commits 形式にする。
- マージ方法は **squash merge** を基本とする（PRの粒度が適切であれば履歴が最もきれいになる）。ただし、コミット履歴自体に意味がある場合は通常のmerge commitも可。
- マージ前にローカルで `main` の最新を取り込み、コンフリクトを解消しておく。

### タグとバージョニング

- リリース時に `v<major>.<minor>.<patch>` 形式のタグを打つ（Semantic Versioning）。
- `pyproject.toml` の `version` フィールドとタグを一致させる。

## 機密情報の取り扱い（ポートフォリオ公開リポジトリ）

このリポジトリはGitHubで公開される。以下を厳守すること：

- **APIキー・トークン・パスワード等の秘密情報をコードやコミットに含めない。** 環境変数（`.env`）経由で注入し、`.env.example` のみコミットする。
- **技術設計書の原本**（`docs/design/`、`docs/internal/`、`*.draft.md`）はGitで追跡しない。`.gitignore` で除外済み。
- 新しいファイル種別や機密情報を扱う場面では、`.gitignore` への追加を検討し、必要に応じてユーザーに確認すること。
- `git add` 前に、ステージ対象に機密ファイルが含まれていないか注意すること。

## 前処理パイプライン

### 構成

```
src/passage_pipeline/
├── models.py     # Chapter, ExtractedBook, TextChunk dataclasses
├── acquire.py    # OPDS catalog fetch + EPUB download
├── extract.py    # EPUB → ExtractedBook (ebooklib + BeautifulSoup/lxml)
├── chunk.py      # ExtractedBook → TextChunk[] (paragraph-based splitting)
├── embed.py      # Cloudflare Workers AI embedding generation
├── ingest.py     # Vectorize NDJSON batch upload
└── main.py       # Pipeline orchestrator (CLI)
```

### 実行方法

```bash
uv run main.py                    # 全書籍を処理
uv run main.py --max-books 5      # 最大5冊のみ処理
uv run main.py --dry-run          # embedding/ingest をスキップ
```

### テスト

```bash
uv run pytest                     # 全テスト実行
uv run pytest tests/test_chunk.py # 個別テスト
```

### 環境変数

`.env.example` を参照。`CF_ACCOUNT_ID` と `CF_API_TOKEN` が必要（embed/ingest時）。

### 設計方針

- **src-layout**: `src/passage_pipeline/` に配置（PEP 517/621準拠）
- **models集約**: データクラスは `models.py` に集約（循環import防止）
- **TDD**: 全モジュールにテストあり。HTTPモジュールは `respx` でモック
- **バッチ処理**: embed=50件/batch、ingest=1000件/batch、リトライ付き

## その他の方針

- Claude Codeには最大限の自律性を与える。ただし上記の安全ガードレールは常に遵守すること。
- 不明点がある場合は推測せず、ユーザーに質問すること。
