---
title: "Snowflake"
date: 2024-03-19T00:43:57+09:00
tags: [Database]
draft: false
---

# 管理ツール
[SnowSQL](https://docs.snowflake.com/ja/user-guide/snowsql-install-config) が提供されている。

```bash
# ログイン
$ snowsql -a {アカウント名} -u {ユーザ名}
Password: ...

# ログインすると SQL を実行できる
SHOW DATABASES;
...
```

# 基本的なクエリ
よくある構文が使用可能。

データベース操作

```sql
-- DB一覧
SHOW DATABASES;

-- DBを作成
CREATE DATABASE HELLO_SNOWFLAKE;

-- DBを選択
USE DATABASE HELLO_SNOWFLAKE;

-- DBを削除
-- DROP DATABASE HELLO_SNOWFLAKE;
```

スキーマ操作

```sql
-- Schema一覧
SHOW SCHEMAS IN HELLO_SNOWFLAKE;

-- Schemaを作成
CREATE SCHEMA HELLO_SNOWFLAKE.SAMPLE_SCHEMA;

-- Schemaを選択
USE SCHEMA HELLO_SNOWFLAKE.SAMPLE_SCHEMA;

-- Schemaを削除
-- DROP SCHEMA HELLO_SNOWFLAKE.SAMPLE_SCHEMA;
```

テーブル操作

```sql
-- Table一覧
SHOW TABLES IN HELLO_SNOWFLAKE.SAMPLE_SCHEMA;

-- Tableを作成
CREATE OR REPLACE TABLE HELLO_SNOWFLAKE.SAMPLE_SCHEMA.SAMPLE_TBL (
  "ymd" VARCHAR(10),
  "area_1" STRING,
  "area_2" STRING,
  "天気概況（昼：06時～18時）品質情報" STRING,
  "天気概況（昼：06時～18時）均質番号" STRING,
  "天気概況（昼：06時～18時）計測値" STRING,
  "平均気温（℃）品質情報" STRING,
  "平均気温（℃）均質番号" STRING,
  "平均気温（℃）計測値" FLOAT,
  "最低気温（℃）品質情報" STRING,
  "最低気温（℃）均質番号" STRING,
  "最低気温（℃）計測値" FLOAT,
  "最深積雪（cm）品質情報" STRING,
  "最深積雪（cm）均質番号" STRING,
  "最深積雪（cm）現象なし情報" STRING,
  "最深積雪（cm）計測値" FLOAT,
  "最高気温（℃）品質情報" STRING,
  "最高気温（℃）均質番号" STRING,
  "最高気温（℃）計測値" FLOAT,
  "降水量の合計（mm）品質情報" STRING,
  "降水量の合計（mm）均質番号" STRING,
  "降水量の合計（mm）現象なし情報" STRING,
  "降水量の合計（mm）計測値" FLOAT
);

-- Tableを削除
DROP TABLE HELLO_SNOWFLAKE.SAMPLE_SCHEMA.SAMPLE_TBL;
```

インサートクエリ

```sql
INSERT INTO HELLO_SNOWFLAKE.SAMPLE_SCHEMA.SAMPLE_TBL VALUES
  ('2019/01/01','石狩','札幌',8,1,'雪時々曇',8,1,-1.9,8,1,-3.1,8,1,0,33,8,1,-0.5,8,1,0,1.0),
  ('2019/01/01','大阪','大阪',8,1,'晴後曇',8,1,5.7 ,8,1,1.0 ,8,1,1,0 ,8,1,10.0,8,1,0,1.5),
  ('2019/01/01','熊本','南阿蘇',0,1,NULL,8,1,1.5,8,1,-3.7,8,1,NULL,0,8,1,4.8,8,1,NULL,0.0)
;
```

セレクトクエリ

```sql
SELECT * FROM HELLO_SNOWFLAKE.SAMPLE_SCHEMA.SAMPLE_TBL LIMIT 10;
```

# バルクロード
Snowflake のテーブルへファイルをロードする場合はステージング領域へ PUT し、アップしたファイルを COPY コマンドを用いて取り込む。  
参考: https://docs.snowflake.com/ja/user-guide/data-load-local-file-system

## 内部ステージ経由
内部ステージング領域は3種類存在する。  

* 名前付き
* テーブル
* ユーザー

テーブルに付属する内部ステージング領域を通して一括ロードを行ってみる。

```sql
-- ステージング領域へファイルをアップ
PUT 'file://data/*.csv' '@HELLO_SNOWFLAKE.SAMPLE_SCHEMA.%SAMPLE_TBL';

-- ステージング領域のファイルを列挙
LIST '@HELLO_SNOWFLAKE.SAMPLE_SCHEMA.%SAMPLE_TBL';

-- ステージング領域のファイルを列挙
GET '@HELLO_SNOWFLAKE.SAMPLE_SCHEMA.%SAMPLE_TBL' 'file://data_dl/';

-- ステージング領域のファイルを削除 (1ファイル)
-- REMOVE '@HELLO_SNOWFLAKE.SAMPLE_SCHEMA.%SAMPLE_TBL/{ファイル名}.csv.gz';

-- ステージング領域のファイルを削除 (一括)
-- REMOVE '@HELLO_SNOWFLAKE.SAMPLE_SCHEMA.%SAMPLE_TBL';

-- ステージング領域のファイルを取り込み
COPY INTO HELLO_SNOWFLAKE.SAMPLE_SCHEMA.SAMPLE_TBL
    FROM @HELLO_SNOWFLAKE.SAMPLE_SCHEMA.%SAMPLE_TBL
    FILE_FORMAT = (TYPE = CSV, FIELD_DELIMITER = ',', SKIP_HEADER = 1)
    PATTERN = '.*.csv.gz'
;
```

## 外部ステージ経由 (S3)
参考: https://docs.snowflake.com/ja/user-guide/data-load-s3

クラウドストレージ統合

```sql
-- 事前に Snowflake から S3 へアクセスする事を許可する IAM ロールを作成する。  
-- https://docs.snowflake.com/ja/user-guide/data-load-s3-config-storage-integration
-- 
-- Step.1
-- - Trusted Entity Type: AWS Account
-- - RoleName: {snowflake-sample-s3integration}
-- - Allow
--   - s3:GetBucketLocation
--   - s3:GetObject
--   - s3:GetObjectVersion
--   - s3:ListBucket
--   - s3:PutObject
--   - s3:DeleteObject

-- ストレージ統合を作成
CREATE STORAGE INTEGRATION integration_s3
    TYPE = EXTERNAL_STAGE
    ENABLED = TRUE
    STORAGE_PROVIDER = 'S3'
    STORAGE_AWS_ROLE_ARN = '{snowflake-sample-s3integration}'
    STORAGE_ALLOWED_LOCATIONS = ('s3://{BUCKETNAME_AND_PREFIX}')
;

-- ストレージ統合を列挙
SHOW STORAGE INTEGRATIONS;

-- ストレージ統合を確認
DESCRIBE INTEGRATION integration_s3;
-- Step.2: 以下をメモする
-- - STORAGE_AWS_IAM_USER_ARN
-- - STORAGE_AWS_EXTERNAL_ID
-- Step.3: IAM Role {snowflake-sample-s3integration} の信頼関係を修正
-- - Principal.AWS: メモした {STORAGE_AWS_IAM_USER_ARN} を指定
-- - Condition.StringEquals.sts:ExternalId: メモした {STORAGE_AWS_EXTERNAL_ID} を指定

-- 外部ステージを作成
CREATE STAGE HELLO_SNOWFLAKE.SAMPLE_SCHEMA.stage_s3
  STORAGE_INTEGRATION = integration_s3
  URL = 's3://{BUCKETNAME_AND_PREFIX}'
;

-- 外部ステージを列挙
SHOW STAGES IN HELLO_SNOWFLAKE.SAMPLE_SCHEMA;

-- 外部ステージの中のファイルを列挙
LIST @HELLO_SNOWFLAKE.SAMPLE_SCHEMA.stage_s3;
LIST @HELLO_SNOWFLAKE.SAMPLE_SCHEMA.stage_s3/{PREFIX};

-- 外部ステージから取り込み
COPY INTO HELLO_SNOWFLAKE.SAMPLE_SCHEMA.SAMPLE_TBL
    FROM 's3://{BUCKETNAME_AND_PREFIX}'
    FILE_FORMAT = (TYPE = CSV, FIELD_DELIMITER = ',', SKIP_HEADER = 1)
    PATTERN = '.*.csv.gz'
;
```

# 外部テーブル

```sql

-- 外部テーブルを作成
-- 作成後、メタデータの自動更新のために追加作業として SNS を構成する.
-- 参考: https://docs.snowflake.com/ja/user-guide/tables-external-s3#determining-the-correct-option
CREATE OR REPLACE EXTERNAL TABLE HELLO_SNOWFLAKE.SAMPLE_SCHEMA.SAMPLE_EXT (
  "ymd" VARCHAR(10) AS (value:c1::STRING),
  "area_1" STRING AS (value:c2::STRING),
  "area_2" STRING AS (value:c3::STRING),
  "天気概況（昼：06時～18時）品質情報" STRING AS (value:c4::STRING),
  "天気概況（昼：06時～18時）均質番号" STRING AS (value:c5::STRING),
  "天気概況（昼：06時～18時）計測値" STRING AS (value:c6::STRING),
  "平均気温（℃）品質情報" STRING AS (value:c7::STRING),
  "平均気温（℃）均質番号" STRING AS (value:c8::STRING),
  "平均気温（℃）計測値" FLOAT AS (value:c9::FLOAT),
  "最低気温（℃）品質情報" STRING AS (value:c10::STRING),
  "最低気温（℃）均質番号" STRING AS (value:c11::STRING),
  "最低気温（℃）計測値" FLOAT AS (value:c12::FLOAT),
  "最深積雪（cm）品質情報" STRING AS (value:c13::STRING),
  "最深積雪（cm）均質番号" STRING AS (value:c14::STRING),
  "最深積雪（cm）現象なし情報" STRING AS (value:c15::STRING),
  "最深積雪（cm）計測値" FLOAT AS (value:c16::FLOAT),
  "最高気温（℃）品質情報" STRING AS (value:c17::STRING),
  "最高気温（℃）均質番号" STRING AS (value:c18::STRING),
  "最高気温（℃）計測値" FLOAT AS (value:c19::FLOAT),
  "降水量の合計（mm）品質情報" STRING AS (value:c20::STRING),
  "降水量の合計（mm）均質番号" STRING AS (value:c21::STRING),
  "降水量の合計（mm）現象なし情報" STRING AS (value:c22::STRING),
  "降水量の合計（mm）計測値" FLOAT AS (value:c23::FLOAT)
)
WITH LOCATION = @stage_s3/{PREFIX}
FILE_FORMAT = (TYPE = CSV, SKIP_HEADER = 1);

-- 外部テーブルの一覧を列挙
SHOW EXTERNAL TABLES IN HELLO_SNOWFLAKE.SAMPLE_SCHEMA;

-- メタデータ更新を手動更新 (自動更新を設定していない場合には必要)
ALTER EXTERNAL TABLE HELLO_SNOWFLAKE.SAMPLE_SCHEMA.SAMPLE_EXT REFRESH;
```

# ドライバー
プログラムからクエリを実行する。

## Python

```python
import snowflake.connector

# https://docs.snowflake.com/ja/developer-guide/python-connector/python-connector
with snowflake.connector.connect(user="{ユーザ名}", password="{パスワード}", account="{アカウント名}") as conn:
    with conn.cursor() as cur:
        hoge = cur.execute('SELECT "ymd", "area_1", "平均気温（℃）計測値" FROM HELLO_SNOWFLAKE.SAMPLE_SCHEMA.SAMPLE_TBL LIMIT 10;')
        for item in hoge:
            print(item)
        pass
```

レスポンスの有るクエリはタプルとして結果が帰ってくる。

```
('2019/1/1', '石狩', -1.9)
('2019/1/1', '大阪', 5.7)
('2019/1/1', '熊本', 1.5)
```