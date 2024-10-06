---
title: "CloudWatch Agent"
date: 2024-10-06T12:03:16+09:00
tags: [Infrastructure]
draft: false
---
# 概要
EC2 インスタンスのメモリやディスクの使用率を CloudWatch からモニタしたい場合、EC2 インスタンスに CloudWatch Agent をインストールし設定してやることでメトリクスとして採取できる。この記事ではエージェントのインストールを設定についてまとめる。

# 1. セットアップ
## IAMロールの作成 & 割当て
EC2 インスタンスから CloudWatch へメトリクスを送信するためのロールを作成する ([参考資料](https://docs.aws.amazon.com/ja_jp/AmazonCloudWatch/latest/monitoring/create-iam-roles-for-cloudwatch-agent.html))。作成したら CloudWatch Agent を動かす EC2 インスタンスの IAM ロールに指定する。

* 信頼されたエンティティタイプ: **AWS のサービス**
* ユースケース: **EC2**
* 許可ポリシーから以下のポリシーをアタッチする
  * **AmazonSSMManagedInstanceCore**
  * **CloudWatchAgentServerPolicy**
* ロール名: 適当な名前を付ける (例: sample-iamrole-instance)

## エージェントをインストール
EC2 インスタンスへ SSH で入り、以下コマンドを実行しエージェントをインストールする ([参考資料](https://docs.aws.amazon.com/ja_jp/AmazonCloudWatch/latest/monitoring/install-CloudWatch-Agent-on-EC2-Instance.html))。ここではカスタムメトリクスも収集できるよう collectd もインストールする。

```bash
sudo yum install amazon-cloudwatch-agent collectd
```

# 2. 設定ファイルを作成
## 1. ウィザードで作成
コンソール上で確認される事柄へ答えていくことで設定ファイルを作成できる ([参考資料](https://docs.aws.amazon.com/ja_jp/AmazonCloudWatch/latest/monitoring/create-cloudwatch-agent-configuration-file-wizard.html))。細かい設定は出来ないため、ウィザードで作成してから手動でカスタマイズすると良い。

```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
# ウィザードに従い設定値を入力すると設定ファイルに作成される。採取可能なメトリクスは (参考資料3) を参照。
# 途中でパラメータストアへ設定を保存するか聞かれるが、ここではローカルへ保存する。
```

作成するとファイル (/opt/aws/amazon-cloudwatch-agent/bin/config.json) が作成される。

```json
{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "cwagent"
  },
  "metrics": {
    "aggregation_dimensions": [
      [
        "InstanceId"
      ]
    ],
    "append_dimensions": {
      "AutoScalingGroupName": "${aws:AutoScalingGroupName}",
      "ImageId": "${aws:ImageId}",
      "InstanceId": "${aws:InstanceId}",
      "InstanceType": "${aws:InstanceType}"
    },
    "metrics_collected": {
      "collectd": {
        "metrics_aggregation_interval": 60
      },
      "disk": {
        "measurement": [
          "used_percent"
        ],
        "metrics_collection_interval": 60,
        "resources": [
          "*"
        ]
      },
      "mem": {
        "measurement": [
          "mem_used_percent"
        ],
        "metrics_collection_interval": 60
      },
      "statsd": {
        "metrics_aggregation_interval": 60,
        "metrics_collection_interval": 10,
        "service_address": ":8125"
      }
    }
  }
}
```

## 2. 手動で作成
細かい設定は設定ファイルを編集する事で可能。フォーマットや設定値は ([参考資料](https://docs.aws.amazon.com/ja_jp/AmazonCloudWatch/latest/monitoring/CloudWatch-Agent-Configuration-File-Details.html)) を参照。なお、ウィザードで作成すると mem の measurement のメトリクスに `mem_` プレフィックスが付くが、省略しても問題無い。なぜ付くのかは不明。

## 3. エージェントを起動
([参考資料](https://docs.aws.amazon.com/ja_jp/AmazonCloudWatch/latest/monitoring/install-CloudWatch-Agent-commandline-fleet.html#start-CloudWatch-Agent-EC2-commands-fleet))。フェッチするコンフィグに指定する `-c` オプションには相対パスも指定できた。

```bash
# 設定をフェッチ
sudo amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/bin/config.json
# エージェントの状態を取得
amazon-cloudwatch-agent-ctl -a status 
# エージェントを停止
sudo amazon-cloudwatch-agent-ctl -a stop
# エージェントを起動
sudo amazon-cloudwatch-agent-ctl -a start
```

# SSM から制御する
## 設定をパラメータストアへアップ
コンフィグをパラメータストアに保管して使用する事も可能。

```bash
# 設定ファイルをパラメータストアへアップ
aws ssm put-parameter --overwrite \
  --name "AmazonCloudWatch-linux" --type "String" \
  --value file:///opt/aws/amazon-cloudwatch-agent/bin/config.json

# エージェントからフェッチ
sudo amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c ssm:AmazonCloudWatch-linux 
```

## エージェントを制御
System Manager の Run Command を使用すると AWS マネジメントコンソールから CloudWatch Agent の設定ファイルをリロードできる。以下の設定で Run Command する。

* コマンドドキュメント: **AmazonCloudWatch-ManageAgent**
* コマンドのパラメータ
  * Action: **configure**
  * Mode: **ec2**
  * Optional Configuration Source: **ssm**
  * Optional Configuration Location: **ssm:AmazonCloudWatch-linux**
  * Optional Restart: **yes**
* ターゲット: (設定対象の EC2 インスタンスを指定)
* 出力オプション: (適当に設定)

# 使えるメトリクス
CloudWatch のメトリクスから見ることができる ([参考資料](https://docs.aws.amazon.com/ja_jp/AmazonCloudWatch/latest/monitoring/metrics-collected-by-CloudWatch-agent.html))。名前空間は既定で CWAgent が使用される。
