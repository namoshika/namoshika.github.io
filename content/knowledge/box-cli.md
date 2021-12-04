---
title: "Box"
date: 2020-09-03T18:00:26+09:00
tags: [Box]
draft: false
---

# Box を CLI ツールから使用する

```powershell
# 認証情報を構成
box configure:environments:add authinf.json

# ファイルをアップロード (既にファイルがある場合はエラーになる)
box files:upload SRC_FILE_PATH --parent-id DST_FOLDR_ID

# 新しいバージョンのファイルをアップロード
box files:versions:upload DST_FILE_ID SRC_FILE_PATH

# フォルダを作成
box folders:create PARENT_FOLDER_ID FOLDER_NAME

# ユーザ情報を取得. USER_ID 省略時にはカレントユーザの情報が取得される
box users:get USER_ID
```