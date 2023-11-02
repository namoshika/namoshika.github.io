---
title: "DynamoDB"
date: 2020-08-24T19:39:09+09:00
tags: [Database]
draft: false
---

# データ型

* スカラー … 数値、文字列、バイナリ、ブール、null
* ドキュメント … リスト、マップ
* セット … 同一型のスカラー型を複数格納できるデータ型。文字セット、数値セット、バイナリセットの3種類がある

# テーブル操作

* テーブル
* 項目

# データ操作

```python
import boto3
import datetime

dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")
table = dynamodb.Table("Books")

# アイテム登録
item = table.put_item(Item = {
    "Author": "athr_1",
    "Title": "ttl_1",
    "Num": 123,
    "Obj": dict(),
    "Lst": list(),
    "Set": { "set_1", "set_2" },
})

# アイテム取得
item = table.get_item(Key = { "Author": "athr_1", "Title": "ttl_1" })
item_meta = item["ResponseMetadata"]
item_payload = item["Item"]
item_payload_author = item_payload["Author"]
item_payload_title = item_payload["Title"]
print(f"Author: {item_payload_author}, Title: {item_payload_title}")

# アイテム更新 (代入)
item = table.update_item(
    Key = { "Author": "athr_1", "Title": "ttl_1" },
    UpdateExpression = "set #key1 = :val1, Obj.item1 = :val2, Obj.item2 = :val3, Lst[0] = :val4",
    ExpressionAttributeNames = {
        "#key1": "nyao",
    },
    ExpressionAttributeValues = {
        ":val1": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ":val2": "obj_text_1",
        ":val3": "obj_text_2",
        ":val4": 123,
    }
)
item = table.get_item(Key = { "Author": "athr_1", "Title": "ttl_1" })
print(item)

# アイテム更新 (リスト追加)
item = table.update_item(
    Key = { "Author": "athr_1", "Title": "ttl_1" },
    UpdateExpression = "set Lst = list_append(Lst, :val3)",
    ExpressionAttributeValues = {
        ":val3": [456, 789],
    }
)
item = table.get_item(Key = { "Author": "athr_1", "Title": "ttl_1" })
print(item)

# アイテム更新 (要素削除)
item = table.update_item(
    Key = { "Author": "athr_1", "Title": "ttl_1" },
    UpdateExpression = "remove Obj.item1, Lst[2]"
)
item = table.get_item(Key = { "Author": "athr_1", "Title": "ttl_1" })
print(item)

# アイテム更新 (セット追加)
item = table.update_item(
    Key = { "Author": "athr_1", "Title": "ttl_1" },
    UpdateExpression = "add #key1 :val1",
    ExpressionAttributeNames = {
        "#key1": "Set",
    },
    ExpressionAttributeValues = {
        ":val1": { "four", "five" }
    }
)
item = table.get_item(Key = { "Author": "athr_1", "Title": "ttl_1" })
print(item)

# アイテム更新 (セット削除)
item = table.update_item(
    Key = { "Author": "athr_1", "Title": "ttl_1" },
    UpdateExpression = "delete #key1 :val1",
    ExpressionAttributeNames = {
        "#key1": "Set",
    },
    ExpressionAttributeValues = {
        ":val1": { "four" },
    }
)
item = table.get_item(Key = { "Author": "athr_1", "Title": "ttl_1" })
print(item)
```