---
title: "Cloud Formation"
date: 2021-12-16T08:07:20+09:00
tags: [DevOps]
draft: false
---
# CloudFormationでEC2インスタンスを建てる
AWS上で構成ファイルによる構築をしてみた。これを使うとAWS サービスをJSON/YAMLで記述したテンプレートファイルによって定義できる。忘れないうちに備忘録としてまとめた。

以下の方針でまとめます。

* 目的は登場する諸要素の整理 (読み手は何度か試し構築済みを想定)
* 試行錯誤しやすい開発環境構築の記録 (CLIからの操作やエディタ設定)
* 毎度忘れてリファレンス漁りそうなルールや記述のまとめ

# 用語説明
CloudFormationで登場する用語

* リソース  
  EC2やVPCなどの部品。AWSでは部品を繋ぎ合わせるAttacheなど動詞的なものもリソースとして扱われる。
* テンプレート  
  リソースはテンプレートで定義される。JSON/YAMLで記述できるが、コメントや短縮記法ができる点でYAMLが良い。
* スタック  
  テンプレート1つはスタックを1つ生成し、生成されたリソースはスタックでひとまとめにされる。
* 変更セット  
  テンプレートを上書きすると新旧の差分が抽出され適用される。スタック更新する際、変更セットを生成し結果を確認後に適用すると手堅くスタック更新できる。

# 事前準備
テンプレートでリソースを扱う際、リソースを扱えるポリシーを持ったユーザでいる必要がある。エディタで入力補完できる状態にした方が良い。VS Codeでは次の記事が良かった。

[VSCodeでAWS CloudFormation をYAMLで書くための個人的ベスト設定 - Qiita](https://qiita.com/yoskeoka/items/6528571a45cd69f93deb)

```bash
code --install-extension redhat.vscode-yaml
```

settings.jsonでスキーマ指定する事でIntelliSenseが効くようになる。  
スキーマは [AWS CloudFormation リソース仕様](https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/cfn-resource-specification.html) で配布されている。

```json
"yaml.schemas": {
    "https://d33vqc0rt9ld30.cloudfront.net/latest/gzip/CloudFormationResourceSpecification.json": [
        "*.cf.yaml",
        "*.cf.yml",
        "cloud*formation/*.yaml",
        "cloud*formation/*.yml"
    ]
},
"yaml.customTags": [
    "!Ref",
    "!Sub",
    "!Join sequence",
    "!FindInMap sequence",
    "!GetAtt scalar sequence",
    "!Base64 mapping",
    "!GetAZs",
    "!Select sequence",
    "!Split sequence",
    "!ImportValue",
    "!Condition",
    "!Equals sequence",
    "!And",
    "!If",
    "!Not",
    "!Or"
],
```

# テンプレートの書き方
ファイルの構造はAWSドキュメントの [テンプレートの分析 - AWS CloudFormation](https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/template-anatomy.html) に書かれている。

テンプレートにコメント以外で日本語を入れるとエラー多発するので指定不可と思っておいたほうが良い。また、後述する組み込み関数やYAMLの1行で書く記法がエラーになったりと、形式に融通は効かない。

最小構成は以下の形になる。ここではInternet Gatewayを定義している。

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  InternetGW:
    Type: AWS::EC2::InternetGateway
```

宣言できる要素は以下の通り。

```yaml
# 形式バージョン。現在は固定値 (必須)
AWSTemplateFormatVersion: "2010-09-09"
# スタックの説明 (オプション)
Description: String
# 用途不明。一旦スルー (オプション)
Metadata:
  template metadata
# スタック生成時に決めたい要素を定義する場所 (オプション)
Parameters:
  set of parameters
# 各所で使う共通の値を定義しておく場所 (オプション)
# [Name] - [Key] - [List or Map of Attribute] の3階層で宣言する
Mappings:
  MappingName1:
    Key1:
      Attribute1: obj hoge
      Attribute2: obj foo
    Key2:
      - list hoge
      - list foo
# 用途不明。一旦スルー (オプション)
Conditions:
  set of conditions
# 用途不明。一旦スルー (オプション)
Transform:
  set of transforms
# リソース定義する場所 (必須)
Resources:
  LogicalID:
    Type: "定義するリソースの種類 (必須) ex: AWS::EC2::VPC"
    Properties:
        settings...
    Metadata:
        EC2インスタンス生成後の初期化処理などを書く際に登場
# 自身の戻り値を定義する場所 (オプション)
Outputs:
  LogicalID:
    Description: オプション
    Value: 必須
    Export: オプション。一旦スルー
```

## パラメータの使い方
Parametersを使うとスタック生成時に決める要素を定義できる。

**パラメータ**  
https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/parameters-section-structure.html

使用時は以下のように定義する (Typeのみが必須)。マネジメントコンソール上でスタック生成する場合、Typeへは固有パラメータ型 (AWS::EC2::KeyPair::KeyName etc...) を使うと使える値を一覧から選べて使い勝手が良い。適切な固有パラメータ型が無いものへは AllowedValues にリストを入れると一覧から値を選べるようになる。

```yaml
Parameters:
  LogicalID:
    Type: String
    AllowedValues:
      - item1
      - item2
      - ...
```

## 組み込み関数の使い方
幾つか関数を使用可能。普段、テンプレート内でVPCを定義する際にルーティングやゲートウェイも定義する事が多いが、これらのリソースはテンプレート作成時点では各自のIDが定まっておらず互いを指定できない。そこでスタック生成時のID解決に関数が使える。

**組み込み関数リファレンス**  
https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference.html

関数は関数名をキー、引数を値としたオブジェクトとして記述する。

```yaml
Routes:
  Type: AWS::EC2::RouteTable
  Properties:
    # テンプレート内で定義されたVPCのIDを取得する
    VpcId: {Ref: VPC}
```

## 省略記法
YAMLでは関数の省略記法が可能。しかし、省略記法は連続記述はできないため、連続する場合には完全名と交互に使う。

```yaml
Routes:
  Type: AWS::EC2::RouteTable
  Properties:
    # 上記の定義と同じ意味になる
    VpcId: !Ref VPC
```

# 様々な組み込み関数
色々な関数がある。よく使いそうなのをピックアップする。

**組み込み関数リファレンス**  
https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference.html

## Ref
指定したパラメータやリソースを取得するのに使う。パラメータでは設定された値が、リソースではリソース宣言の戻り値を返す (大抵はリソースの物理ID)

```yaml
Routes:
  Type: AWS::EC2::RouteTable
  Properties:
    VpcId: !Ref VPC
```

## Fn::FindInMap
Mappingsで定義された内容を取得する。次の書き方になる。

```yaml
!FindInMap [ MapName, Key, Attribute ]
```

例: VPCへタグを付与する

```yaml
Mappings:
  Common:
    ServiceTag: {Key: service, Value: helloCF}
Resources:
  VPC:
  Type: AWS::EC2::VPC
  Properties:
    CidrBlock: 172.16.0.0/16
    Tags:
      - {
          Key: !FindInMap [Common, ServiceTag, Key],
          Value: !FindInMap [Common, ServiceTag, Value]
        }
```

## Fn:GetAtt
リソースの戻り値を取得するためRefと似ている。こちらはリソースのみを対象とする他、Refは大抵が物理IDだが、こちらの関数で何が返ってくるかは各リソースで違うためドキュメントの戻り値の部分を読むこと。

以下の例ではEC2インスタンスのセキュリティグループにVPCのデフォルトセキュリティグループを指定している。

```yaml
WebSrv:
  Type: AWS::EC2::Instance
  Properties:
    ImageId: ami-097473abce069b8e9 # Amazon Linux 2
    InstanceType: t2.micro
    KeyName: id_rsa
    SubnetId: !Ref Subnet
    SecurityGroups:
      - !GetAtt [VPC, DefaultSecurityGroup]
      - !Ref SecGrp
```

## Fn::Sub
内部に変数を仕込んだ文字列をスタック生成時に変数の値を解決する。複雑な文字列を組む際に使う。  
変数には次が使用可能

* パラメータ: ${LogicalID} ... !Ref LogicalID と同じ
* リソースID: ${LogicalID} ... !Ref LogicalID と同じ
* リソース属性: ${LogicalID.Attr} ... !GetAtt [LogicalID, Attr] と同じ
* キー/値マップ: 詳細不明

## Fn::Base64
入力文字列をBase64表現に変換する。主にEC2リソースを定義する際のUserData用。Fn::Subと組み合わせて以下のように使うと便利。

```yaml
UserData:
  Fn::Base64:
    !Sub |
      #!/bin/bash -xe
      rpm -Uvh https://packages.microsoft.com/config/rhel/7/packages-microsoft-prod.rpm
      yum -y update
      yum -y install aws-cfn-bootstrap
      /opt/aws/bin/cfn-init -v --stack ${AWS::StackName} --resource WebSrv --region ${AWS::Region} 
```

## Fn::Select
配列から指定したインデックスの要素を取得する。!GetAZsと組み合わせると便利。

## Fn::GetAZs
指定リュージョンで利用可能なAzの配列を返す。以下の例ではサブネットをどのAzへ配置するかを作業中リュージョンから動的に取得している。ちなみにAvailabilityZone部分を1行にしたいが、するとエラーになるため現在の書き方に落ち着いた。

```yaml
Subnet:
  Type: AWS::EC2::Subnet
  Properties:
    CidrBlock: 172.16.0.0/20
    VpcId: !Ref VPC
    MapPublicIpOnLaunch: True
    AvailabilityZone: !Select
      - 0
      - Fn::GetAZs: !Ref AWS::Region
```

# 様々な疑似パラメータ
事前定義されたパラメータが幾つかある。

**擬似パラメーター参照**  
https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/pseudo-parameter-reference.html

以下の ${AWS::～} が該当する。テンプレートから固有要素を排除し汎用性をあげることに使える。

```yaml
Subnet:
  Type: AWS::EC2::Subnet
  Properties:
    CidrBlock: 172.16.0.0/20
    VpcId: !Ref VPC
    Tag:
      - {Key: Name, Value: !Sub "subnet-${AWS::StackName}"}
```

# 使ってみる (aws-shell)
EC2でインスタンスを建ててみる。以下のテンプレートを作成。

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Parameters:
  EC2InstanceType:
    Type: String
    Description: Instance type of WebSrv
    Default: t2.micro
    AllowedValues: ["t2.nano", "t2.micro", "t2.small", "t2.medium", "t2.large", "t2.xlarge", "t2.2xlarge"]
  EC2KeyName:
    Type: AWS::EC2::KeyPair::KeyName
    Description: SSH public key
    Default: id_rsa
Mappings:
  Common:
    ServiceTag: {Key: service, Value: helloCF}
Resources:
  # ---------------------------
  # VPC
  # ---------------------------
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 172.16.0.0/16
      Tags:
        - {Key: !FindInMap [Common, ServiceTag, Key], Value: !FindInMap [Common, ServiceTag, Value]}
  InternetGWAttacher:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId: !Ref InternetGW

  # ---------------------------
  # Route
  # ---------------------------
  Router:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
  InternetGWRoute:
    Type: AWS::EC2::Route
    DependsOn: InternetGWAttacher
    Properties:
      RouteTableId: !Ref Router
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGW

  # ---------------------------
  # Security Group
  # ---------------------------
  SecGrp:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Web Server Rule
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - { IpProtocol: tcp, FromPort: 80, ToPort: 80, CidrIp: 0.0.0.0/0 }
        - { IpProtocol: tcp, FromPort: 22, ToPort: 22, CidrIp: 0.0.0.0/0 }

  # ---------------------------
  # Subnet
  # ---------------------------
  Subnet:
    Type: AWS::EC2::Subnet
    Properties:
      CidrBlock: 172.16.0.0/20
      VpcId: !Ref VPC
      MapPublicIpOnLaunch: True
      AvailabilityZone: !Select
        - 0
        - Fn::GetAZs: !Ref AWS::Region
  SubnetRouting:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: !Ref Router
      SubnetId: !Ref Subnet

  # ---------------------------
  # InternetGW
  # ---------------------------
  InternetGW:
    Type: AWS::EC2::InternetGateway

  # ---------------------------
  # EC2
  # ---------------------------
  WebSrv:
    Type: AWS::EC2::Instance
    Properties:
      ImageId: ami-097473abce069b8e9 # Amazon Linux 2
      InstanceType: !Ref EC2InstanceType
      KeyName: !Ref EC2KeyName
      SubnetId: !Ref Subnet
      SecurityGroupIds:
        - !GetAtt [VPC, DefaultSecurityGroup]
        - !Ref SecGrp

Outputs:
  Region:
    Description: Output Description.
    Value: !Ref AWS::Region
```

## スタック一覧

```bash
cloudformation describe-stacks
```

## スタック生成

```bash
cloudformation create-stack --stack-name helloCF --template-body file://hello.cf.yml

# パラメータは --parameters の後に ParameterKey=Key,ParameterValue=Value と続ける
# 他コマンドでもパラメータは同じ感じ
cloudformation create-stack \
    --stack-name helloCF \
    --template-body file://hello.cf.yml \
    --parameters \
        ParameterKey=EC2InstanceType,ParameterValue=t2.nano \
        ParameterKey=EC2KeyName,ParameterValue=id_rsa
```

## スタック表示

```bash
# スタック状態の取得
cloudformation describe-stacks --stack-name helloCF

# テンプレート本体を取得
cloudformation get-template --stack-name helloCF | jq .TemplateBody -r
```

## スタック更新

```bash
cloudformation update-stack --stack-name helloCF --template-body file://hello.cf.yml
```

## 変更セット生成
スタック更新は変更セットを経由すると何が変わるのかが事前に把握できて良い。

```bash
cloudformation create-change-set --stack-name helloCF --change-set-name fixup2 --template-body file://hello.cf.yml
```

## 保留中の変更セット取得

```bash
cloudformation list-change-sets --stack-name helloCF
```

## 保留中の変更セット適用
変更セットは複数保留されている状態にできるが、1つ適用すれば他は削除される。

```bash
cloudformation execute-change-set --change-set-name fixup2 --stack-name helloCF
```

## スタック消去

```bash
cloudformation delete-stack --stack-name helloCF
```

# 各種リソースの定義
使った時のコケた部分や使いまわしそうな記述をまとめる。

## VPC
IPアドレスのCIDRは 16～28まで。ドキュメントに172.16.0.0/12 が目に付くが12は無理。

**VPC とサブネット**  
https://docs.aws.amazon.com/ja_jp/vpc/latest/userguide/VPC_Subnets.html

## Subnet
Azの指定を省く。作業リージョンで使用可能なAzを出せる。1行にしようとするとエラーになるのが謎。

```yaml
AvailabilityZone: !Select
  - 0
  - Fn::GetAZs: !Ref AWS::Region
```

## Route

インターネットGWを定義する場合、VPCとGWをAttacherリソースで紐付けし、Routeで経路設定をする。その際、RouteにはAttacherへの依存 (DependOn) を明示的に記述する必要がある。

```yaml
InternetGWRoute:
  Type: AWS::EC2::Route
  DependsOn: InternetGWAttacher
  Properties: ...
```

## EC2

インスタンスタイプは次のリンク先に一覧がある。

**インスタンスタイプ**  
https://docs.aws.amazon.com/ja_jp/AWSEC2/latest/UserGuide/instance-types.html

AMIのIDはマネジメントコンソールでインスタンス作成する際のAMI検索画面に載っている  
セキュリティグループにVPCのデフォルトSGを指定する際は !GetAttr を使う。

```yaml
SecurityGroupIds:
  - !GetAtt [VPC, DefaultSecurityGroup]
  - !Ref SecGrp
```