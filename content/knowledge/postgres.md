---
title: "Postgres"
date: 2022-11-16T09:16:21+09:00
tags: [PostgreSQL]
draft: true
---

```sh
psql -h localhost -p 5432 -U postgres -d postgres
```

# Database
テンプレートを指定しない場合は template1 から作られる。

```sh
# create db
createdb {DB_NAME} -T template1

# modify db
# (empty)

# list db
psql -l

# switch db
psql -d {DB_NAME}

# drop db
dropdb {DB_NAME}
```

```sql
-- create db
create database {DB_NAME} with template template1

-- modify db
alter database {DB_NAME_OLD} rename to {DB_NAME_NEW}

-- list db
\l

-- switch db
\c {DB_NAME}

-- drop db
drop database {DB_NAME}
```

# Schema

```sql
-- create db
create schema {SCHEMA_NAME} 

-- modify db
alter schema {SCHEMA_OLD} rename to {SCHEMA_NEW}

-- list db
\dn

-- drop db
drop schema {SCHEMA_OLD}
```

# Table

```sql
-- create table
create table {TABLE_NAME} (column1 integer, column2 varchar(123))

-- modify table
alter table sample_table add col1 varchar(123)

-- list table
\d, \dt

-- drop table
drop table {TABLE_NAME}
```

# Role
データベースクラスタの中で同名ユーザの作成は不可。  
データベースクラスタを生成時のOSユーザ名でスーパーユーザが生成される

```sh
# create user
createuser {USER_NAME} -l -d -r -s -P
```

```sql
-- create user
create role {USERNAME} with LOGIN PASSWORD 'passwd'

--list user
\du
```

# Domain
制約などを付与した型として使用可能。

```sql
create domain {DOMAIN_NAME} as integer check (VALUE < 5)
```

# Database Cluster
postgre はサーバープロセス1つに対して `$PGDATA` のディレクトリを1つを持つ。  
データベースは `$PGDATA/base` の中にデータベースのOIDが名前となったディレクトリとして格納される。  
エンコーディング指定はデータベースとクライアントで異なる事に注意。

| Encoding | Database Encoding | Client Encoding |
| -------- | ----------------- | --------------- |
| UTF8     | OK                | OK              |
| EUC_JP   | OK                | OK              |
| SJIS     | NG                | OK              |

データベースクラスタは `initdb` で作る。特にソースコードからビルドした際には `initdb` で作る必要が有る。このコマンドはホストからのみ実行可能。

```bash
useradd -M pst
mkdir /var/dbcl
chown pst:pst /var/dbcl

# -D, --pgdata {DIRECTORY}
# -E, --encoding {ex: utf8, euc_jp}
# -U, --username {USERNAME}
# --no-locale
initdb -D /var/dbcl/ -E utf8 --no-locale -U pst
```

# Admin Tools
## pg_ctl

```bash
pg_ctl initdb -D|--pgdata {DB_CLUSTER_DIR}

pg_ctl start -D|--pgdata {DB_CLUSTER_DIR} -t {MAX_WAIT_TIME: 60sec}

# -m
#   * smart:     クライアントからの接続が全て切断されるまで待つ
#   * fast:      クライアントからの接続を即遮断. 実行中トランザクションは全てロールバック
#   * immediate: クリーンアップ処理を行わずに停止. クラッシュ相当の状態
# -t
#   待ち時間 (単位: 秒. 既定: 60sec)
# -W
#   待たずに制御を戻す
pg_ctl stop -D|--pgdata {DB_CLUSTER_DIR} -t -m s[mart]|f[ast]|i[mmediate] -W
pg_ctl restart (stop と同一)

# 設定ファイルの再読み込み
pg_ctl reload -D|--pgdata

# 起動状態
pg_ctl status

# プロセス終了
pg_ctl kill TERM|INT|QUIT|HUP {PID}
```

## psql

```bash
# 接続
psql -h|--host {HOST} -p|--port {PORT} -U|--user {USER}
```

# Setting file
設定値には型が有る (boolean, integer, floating point, string, enum)
boolean には on/off/true/false/yes/no/1/0 が指定可能
一部の設定値には単位を指定可能 (メモリ: kB/MB/GB, 時間: ms/s/min/h/d)

## 設定反映のタイミング

| 種別                       | restart | pg_ctl reload | suset | set |
| -------------------------- | ------- | ------------- | ----- | --- |
| 不可                       | x       | x             | x     | x   |
| 起動 (postmaster)          | o       | x             | x     | x   |
| 再読み込み (sighup)        | o       | o             | x     | x   |
| スーパーユーザのみ (suset) | o       | o             | o     | x   |
| いつでも (user)            | o       | o             | o     | o   |

## listen_address
サーバー側の ip アドレス (カンマで複数指定可能)。クライアントから宛先未設定の接続を試みられても応答はしない。

* デフォルト値: localhost
* 反映: 起動時

## port
受け付けるポート番号

* デフォルト値: 5432
* 反映: 起動

## max_connections
最大同時接続数

* デフォルト値: 100
* 反映: 起動

## search_path
スキーマ検索パス

* デフォルト値: "$user".public
* 反映: 何時でも誰でも

## default_transaction_isolation
トランザクションの分離レベル

* 型: read uncommitted, read committed, repeatable read, serializable
* デフォルト値: read committed
* 反映: 何時でも誰でも

## client_encoding
クライアントエンコーディングを指定

* デフォルト値: SQL_ASCII
* 反映: 何時でも誰でも

## log_destination
ログの保存先。カンマで複数指定可能

* 型: stderr, csvlog, syslog, eventlog
* デフォルト値: stderr
* 反映: reload

出力先

* stderr: 標準エラー出力
* csvlog: CSV形式で stderr へ出力。設定の logging_collector を on にする必要有り
* syslog: syslog へ出力
* eventlog: イベントログへ出力 (windows 用)

## logging_collector
ログをファイルに出力する

* デフォルト値: off
* 反映: 起動時

## log_directory
ログ出力ディレクトリを指定。絶対パスか `$PGDATA` からの相対パスで指定。

* デフォルト値: log (`$PGDATA/log`)
* 反映: reload

## log_filename
ログファイル名を指定

* デフォルト値: postgresql-%Y-%m-%d_%H%M%S.log
* 反映: reload

## log_min_message
ログレベルの指定

* 型: PANIC, FATAL, LOG, ERROR, WARNING etc
* デフォルト値: WARNING
* 反映: suset

ログレベル

* PANIC: 致命的。全てのセッションが強制切断。PostgreSQL 停止。
* FATAL: 特定のセッションで問題発生。対象セッションのみ切断
* LOG: 管理者が着目すべき動作ログ
* ERROR: 特定のトランザクションで問題発生。対象トランザクションのみロールバック
* WARNING: 想定外の動作に対する警告メッセージ

## log_line_prefix
ログの行頭を指定

* デフォルト値: `%m [%p]`
* 反映: reload

使用可能な変数

* %u: データベースユーザ名
* %d: データベース名
* %p: プロセス名
* %t: タイムスタンプ
* %m: ミリ秒タイムスタンプ
* %%: %文字そのもの

# SQL (DML)
## 各構文

```sql
-- 基本クエリ
select distinct on ({column_name}) {column_name} [as] {alternative_column_name} ...
from  {table_name}
where {condition}
group by {column_name}
having {column_name}
order by {column_name} {asc|desc}
offset {num}
limit {num}

-- 結合
[inner] join {table_name} on {expression}
[inner] join {table_name} using {column}
natural [inner] join {table_name}
cross join {table_name}
{left|right|full} [outer] join {table_name} on {expression}

-- 条件
where {column_name} [not] in ({value})
where {column_name} = any (query)
where {column_name} between {from} and {to}
where {column_name} is not null
where [not] exists (query)

-- 集合演算
-- 優先度は通常の論理演算と同じ
query
[union|except|intersect][all]
query

-- 更新
insert into {table_name}({column1}, {column2}) values
  ({value1}, {value1}),
  ({value2}, {value2})
;
update {table_name} set {column_name1}={value1}, {column_name2}={value2} where {expression}
delete {table_name} where {expression}

-- 配列
create table array_table (c1 text[], c2 int[])
insert into array_table(c1) values('(1, 2, 3)')
select c1[2] from array_table; -- インデックスは1始まり
select c1[2] from array_table where '1' = any(c1);

-- キャスト
'{table_name}'::regclass
cast({column_name} as integer)
{column_name}::int

```

## データ型
interval で複数形するか否かは自由。

| type                                              | size     | range                                    |
| ------------------------------------------------- | -------- | ---------------------------------------- |
| smallint                                          | 2 byte   | -3万～3万                                |
| integer, int                                      | 4 byte   | -2億～2億                                |
| bigint                                            | 8 byte   | デカい                                   |
| decimal, numeric                                  | variable | そこそこ                                 |
| real                                              | variable | そこそこ                                 |
| double precision                                  | 8 byte   | 15桁                                     |
| smallserial                                       | 2 byte   | 1～3万                                   |
| serial                                            | 4 byte   | 1～2億                                   |
| bigserial                                         | 8 byte   | デカい                                   |
| char(n), character(n)                             | variable | 空白で埋められた固定長                   |
| varchar(n), character varying(n)                  | variable | 可変長文字列                             |
| text                                              | variable | 可変長文字列                             |
| bytea                                             | variable | バイナリ                                 |
| timestamp [without time zone]                     | 8 byte   |                                          |
| timestamp with timezone                           | 8 byte   |                                          |
| date                                              | 4 byte   |                                          |
| time [without time zone]                          | 8 byte   |                                          |
| time with time zone                               | 12 byte  |                                          |
| interval '{num} {year\|month\|day\|hour\|minute}' | 16 byte  | e.g. '1 hours 30 minutes'                |
| boolean                                           | 1 byte   | {t\|'true'\|'y'\|'yes'\|'on'\|'1'\|TRUE} |

# SQL (DDL)

```sql
-- 基本操作
create table sample_table3 (
  id int primary key,
  c1 int unique,
  c2 text not null,
  c3 text default 'abc',
  c4 timestamp default now()
)
alter table {old_table_name} rename to {new_table_name}
alter table {table_name} owner to {new_role}
alter table {table_name} rename column {old_column_name} to {new_column_name}
alter table {table_name} add column {DEFINE}
alter table {table_name} drop column {DEFINE}

-- 主キー
-- 制約名: {table_name}_pkey
create table {table_name} (c1 int primary key)
alter table {table_name} add primary key (c1)
alter table {table_name} add constraint {pri_keyname} primary key (c1)
alter table {table_name} drop constraint {table_name}_pkey

-- ユニーク
create table {table_name} (c1 int unique)
alter table {table_name} add unique (c1)
alter table {table_name} add constraint {table_name}_c1_key unique (c1)
alter table {table_name} drop constraint {table_name}_c1_key

-- not null
create table {table_name} (c1 int not null)
alter table {table_name} alter column c1 set not null
alter table {table_name} alter column c1 drop not null

-- foreign key
create table {table_name} (c1 int references {ref_table_name}({ref_column_name}) on delete cascade on update cascade)
create table {table_name} (c1 int foreign key (c1) references {ref_table_name}({ref_column_name}) on delete cascade on update cascade)
alter table {table_name} add constraint {table_name}_fkey foreign key (column_name) references {ref_table_name}({ref_column_name}) on delete cascade on update cascade

-- check
alter table {table_name} add constraint {table_name}_{column_name}_check check({expr})

-- parition
-- from 以上 to 未満
create table tbl (c1 serial, c2 text, c3 date) partition by range(c3);
create table tbl_y2011m10 partition of tbl for values from ('2011-10-01') to ('2019-10-01');
create table tbl_y2019m10 partition of tbl for values from ('2019-10-01') to ('2020-10-01');
create table tbl_y2020m10 partition of tbl for values from ('2020-10-01') to ('2022-10-01');
insert into tbl(c2, c3) values ('message', '2011-10-01');
insert into tbl(c2, c3) values ('message', '2019-10-01');
insert into tbl(c2, c3) values ('message', '2019-10-02');

alter table tbl attach partition {partition_name} for values {condition}
alter table tbl detach partition {partition_name}
```
