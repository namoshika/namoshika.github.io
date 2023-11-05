---
title: "Databricks を使ってみる"
date: 2023-10-23T00:45:39+09:00
tags: [DataEngineering]
draft: true
---

# DBFS
ストレージにはローカルとDBFSがある。
DBFSを挟むことで S3 を始めとするオブジェクトストレージへの読み書きを抽象化する。

```py
# ローカルファイルシステム
%fs ls file:/
dbutils.fs.ls("file:/")

# DBFS (スキーマ未指定時にはDBFSが参照される)
%fs ls dbfs:/
%fs ls /
dbutils.fs.ls("dbfs:/")

# ローカルに対してシェルスクリプト
%sh ls -Al /

# DBFS の中でファイルをコピー
# /FileStore へ保存するとブラウザからアクセス可能
dbutils.fs.cp("/databricks-datasets/README.md", "/FileStore/README.md")
displayHTML("<a href='files/README.md/'>aaa</a>")
```

# Unity Volume
外部ストレージへアクセスする

# Delta Lake
Databricks は Delta を推している。このフォーマットはデータ保存へは Parquet 形式を使いつつ、メタデータ管理などを追加することで ACID トランザクションやデータのバージョニングなど高度な機能を実現している。

```py
spark.write.format("delta").save(savePath)
```

# Auto Loader
format に cloudFiles を指定する事で Auto Loader が使えるようになる。

```py
from pyspark.sql.types import *

df = spark.readStream.format("cloudFiles") \
    .option("cloudFiles.format", "csv") \
    .schema(
        StructType([
            StructField('customer_id', IntegerType(), True),
            StructField('tax_id', DoubleType(), True),
            StructField('tax_code', StringType(), True),
            StructField('customer_name', StringType(), True),
            StructField('state', StringType(), True),
            StructField('city', StringType(), True),
            StructField('postcode', StringType(), True),
            StructField('street', StringType(), True),
            StructField('number', StringType(), True),
            StructField('unit', StringType(), True),
            StructField('region', StringType(), True),
            StructField('district', StringType(), True),
            StructField('lon', DoubleType(), True),
            StructField('lat', DoubleType(), True),
            StructField('ship_to_address', StringType(), True),
            StructField('valid_from', IntegerType(), True),
            StructField('valid_to', DoubleType(), True),
            StructField('units_purchased', DoubleType(), True),
            StructField('loyalty_segment', IntegerType(), True)
        ])
    ) \
    .load("/databricks-datasets/retail-org/customers/")
display(df)
```

# Delta Live Tables
データパイプラインを簡単に構築する仕組み。

宣言的にテーブルやビューを定義する事で依存関係からパイプラインを構築できる。宣言されたテーブルはパイプライン内のみで参照可能。外部からも参照したい場合はパイプラインを構成する際にターゲットスキーマを指定する。テーブルは実際にはマテリアライズド・ビューとして扱われる。

いくつか制約がある。
* `%pip` 以外のマジックコマンドは使用不可 ... 使ったセルは実行がスキップされる
* 共有コンピュートクラスターからのみ参照可能 ... [Databricks SQLでのマテリアライズドビューの使用](https://docs.databricks.com/ja/sql/user/materialized-views.html)  
  > Databricks SQL 具体化されたビューは、Databricks SQLウェアハウス、Delta Live Tables、および Databricks Runtime 11.3 以降を実行している共有クラスターからのみクエリできます。

```py
import dlt
from pyspark.sql.types import *

# ビューを定義 (パイプライン内でのみ参照可能)
@dlt.view
def customers_vw():
  return spark.read.format("csv") \
    .options(header=True, inferSchema=True) \
    .load("/databricks-datasets/retail-org/customers/")

# 通常テーブルを定義 (構成すれば外部から参照可能)
@dlt.table
def customers_tbl():
  return spark.read.format("csv") \
    .options(header=True, inferSchema=True) \
    .load("/databricks-datasets/retail-org/customers/")

# Streaming, Auto Loader でロードしてもテーブル生成可能
# Unity Volume から hive_metastore へのテーブル作成ではエラーが出る
@dlt.table
def speedtest_mat():
    return spark.read \
        .option("header", True) \
        .schema(StructType([
            StructField("ServerID", IntegerType(), False),
            StructField("Sponsor", StringType(), True),
            StructField("ServerName",StringType(), True),
            StructField("Timestamp", TimestampType(), False),
            StructField("Distance", IntegerType(), True),
            StructField("Ping", DoubleType(), True),
            StructField("Download", DoubleType(), True),
            StructField("Upload", DoubleType(), True),
            StructField("id", IntegerType(), True)
        ])) \
        .csv("dbfs:/Volumes/hellodatabricks/default/hello-extvol/data/if-crawler/speedtest")

@dlt.table
def speedtest_aut():
    return spark.readStream.format("cloudFiles") \
        .option("cloudFiles.format", "csv") \
        .option("header", True) \
        .schema(StructType([
            StructField("ServerID", IntegerType(), False),
            StructField("Sponsor", StringType(), True),
            StructField("ServerName",StringType(), True),
            StructField("Timestamp", TimestampType(), False),
            StructField("Distance", DoubleType(), True),
            StructField("Ping", DoubleType(), True),
            StructField("Download", DoubleType(), True),
            StructField("Upload", DoubleType(), True),
            StructField("id", IntegerType(), True)
        ])) \
        .load("dbfs:/Volumes/hellodatabricks/default/hello-extvol/data/if-crawler/speedtest")
```

```sql
-- ビューを定義 (パイプライン内でのみ参照可能)
CREATE LIVE VIEW airlines_vw AS
SELECT *
FROM csv.`dbfs:/databricks-datasets/airlines/`
LIMIT 20;

-- 通常テーブルを定義 (構成すれば外部から参照可能)
CREATE LIVE TABLE airlines_tbl AS
SELECT *
FROM csv.`dbfs:/databricks-datasets/airlines/`
LIMIT 20;

-- 一時テーブルを定義
CREATE TEMP LIVE TABLE airlines_tmp AS
SELECT *
FROM csv.`dbfs:/databricks-datasets/airlines/`
LIMIT 20;

```

# Job
使い道

* ワークフロー実行
* Delta Live Table のロード処理
