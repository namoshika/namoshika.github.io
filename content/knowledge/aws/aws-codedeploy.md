---
title: "Code Deploy"
date: 2021-12-16T08:19:46+09:00
tags: [DevOps]
draft: false
---
# この記事で扱う範囲
公式チュートリアルの Wordpress サーバーを作成する資料を実践。  
初学者過ぎてロールやエージェントインストールが辛かったので、現時点の理解を整理して出力。CodeDeployを使う際の用意する資材や、IAMの初歩的解説、デプロイ失敗時の原因調査で使えたログ場所をまとめました。

# CodeDeployで必要なもの
今回はS3のzipファイルをEC2インスタンスへデプロイする。次の要素を満たすことでデプロイが最後まで動く。

* S3: デプロイ資材 (zipでまとめておく)
* EC2 インスタンス
    - デプロイ先インスタンス:  
      適当なタグを設定しておくこと。CodeDeploy Agentをインストールしておくこと
* IAM ロール
    - Role1: CodeDeployからデプロイ先インスタンスがあるEC2へアクセスするロール
    - Role2: EC2からデプロイ資材のあるS3へアクセスするロール

# デプロイする際の手順
AWS CLIはできるだけ使わず、マネジメントコンソールからの操作で作業する。

## S3にデプロイ資材を用意
資材はzipでまとめておき、S3へアップする。  
資材はルート直下に appspec.yml が必要。このファイルでデプロイ資材の配置場所などを決める。

**appspec.yml の仕様**  
https://docs.aws.amazon.com/ja_jp/codedeploy/latest/userguide/reference-appspec-file-structure.html

```yml
# 必須
version: 0.0
os: linux
files:
# パスはappspec.ymlがある場所がルート & カレント ディレクトリになる
  - source: /
    destination: /var/www/html/WordPress
# オプション
# デプロイライフサイクルに基づいて、処理を挟める。
hooks:
  BeforeInstall:
    - location: scripts/install_dependencies.sh
      timeout: 300
      runas: root
  AfterInstall:
    - location: scripts/change_permissions.sh
      timeout: 300
      runas: root
  ApplicationStart:
    - location: scripts/start_server.sh
    - location: scripts/create_test_db.sh
      timeout: 300
      runas: root
  ApplicationStop:
    - location: scripts/stop_server.sh
      timeout: 300
      runas: root
```

## IAMロールを用意
サービス間は権限設定で疎通を許可する必要がある。  
今回は CodeDeploy/EC2/S3 間に許可設定が必要。IAMにはService, Role, Policyが登場し次の関係になる。

```
 ┌─────┐　┌───┐　　┌────┐  
 │ Service　├─┤ Role │◇─┤ Policy │
 └─────┘　└───┘　　└────┘  
```

次の2つのロール作成が必要。

* **CodeDeploy → EC2**  
  CodeDeployサービスにEC2サービスへのアクセス権限が必要。これには AWS管理ポリシーに AWSCodeDeployRole が用意されている。このポリシーを付与したロールを作成する。

* **EC2インスタンス → S3**  
  デプロイ資材の取得はデプロイ先にインストールされたcodedeploy-agentが行うため、EC2インスタンスからS3へのアクセス権限の付与が必要になる。AWS管理ポリシーに AmazonEC2RoleforAWSCodeDeploy が用意されている。このポリシーを付与したロールを作成する。

**権限設定に関する補足**  
PolicyはJSON形式で権限設定が定義されている。Actionで操作を指定、Effectで許可/拒否、Resourceで参照先を指定。次の例ではS3への読み取り系の許可を与える内容になっている。どの権限が必要になるかはサービスのドキュメントを読み漁るしか無い。一旦はAmazonがユースケース毎にAWS管理ポリシーをすでに登録済みなため、管理ポリシーを使うと良い。

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "s3:GetObject",
                "s3:GetObjectVersion",
                "s3:ListBucket"
            ],
            "Effect": "Allow",
            "Resource": "*"
        }
    ]
}
```

RoleにはPolicyが複数セットされる。また、Policyに似た「信頼関係」が設定でき、Roleの権限行使が許可される相手を定義する。今回は直接編集しないが、CodeDeployやEC2インスタンスへRoleを設定した際にRoleの信頼関係にPrincipalでCodeployやEC2へ「sts:AssumeRole」という権限委譲の機能が許可されることが確認できる。

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "codedeploy.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

## EC2インスタンスを用意する
デプロイ先となるインスタンスは起動しておく。

**EC2インスタンス → S3 用ロールを付与**
EC2の管理画面からデプロイ先インスタンスを右クリック。コンテキストメニューから \[インスタンスの設定\] - \[IAMロールの割り当て/解除\] を開く。デプロイ先EC2インスタンスに先の手順で定義した 「EC2インスタンス → S3」 用ロールを付与。

**CodeDeploy-Agentをインストール**
デプロイ先にエージェントをインストールする。エージェントはS3からDLして使う。rubyなども全てインストールすること。

```sh
# CodeDeploy-Agentをダウンロード
sudo yum update
sudo yum install ruby
sudo yum install wget
# 先のEC2インスタンスへのロール付与で認証が通っていることを確認
# access/secret key が表示され、type列が "iam-role" になっていること。
aws configure list
# 東京リュージョンからDL
aws s3 cp --recursive s3://aws-codedeploy-ap-northeast-1/latest .

# インストール
chmod +x ./install
sudo ./install auto

# 起動していることを確認
systemctl status codedeploy-agent

# 起動してないなら起動させる
systemctl start codedeploy-agent
```

## CodeDeployにアプリを登録する
マネジメントコンソールのサービス一覧から「CodeDeploy」を開く。デプロイグループを開き、「アプリケーション」を開く。「アプリケーションの作成」をクリックし、ウィザードに従って設定。画面を見れば設定箇所は埋められるが、アプリを登録してもボタン一発でデプロイできる状態にはならず、毎度デプロイ資材の選択などが生じる。

* アプリケーション:  
  アプリ名を設定。次の2つはアプリ毎に設定可能
* デプロイグループ:  
  デプロイ先 (EC2インスタンスのタグ名) とデプロイ用IAMロール (サービスロール) を設定
* リビジョン:  
  デプロイ資材はリビジョンとして扱われる

**追加のデプロイ動作設定**  
意味が分かりにくい設定として「追加のデプロイ動作設定」がある。旧リビジョンのappspec.ymlに記載された hock.ApplicationStop がエラーの際に「ライフサイクルイベントの障害で、デプロイを失敗させない」を指定すると強制的に新リビジョンのデプロイ処理を走らせられる。

# デプロイに失敗する場合
エラーが出た際にはマネジメントコンソールからライフライクルイベント毎のエラ出力を確認できる。EC2インスタンスの次のパスでもエージェントのログが格納されるため、エラー原因調査に使える。

* /var/log/aws/codedeploy-agent/
* /opt/codedeploy-agent/deployment-root/deployment-logs/  
  hookスクリプトのエラーなどはこちらで確認できる
