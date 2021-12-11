---
title: "Hugo"
date: 2020-08-21T08:52:02+09:00
tags: [Hugo]
draft: false
---

# 基本操作
## サイトを作成する

```bash
# サイトディレクトリを作成
$ mkdir HelloHugo
$ cd HelloHugo

# 中を初期化
$ hugo new site

# 好みのテーマファイルを取得 (ここでは ananke を指定)
$ git submodule add https://github.com/theNewDynamic/gohugo-theme-ananke.git themes/ananke
$ git submodule update --init
$ vim ../config.toml
> ...
> theme = "ananke" ... テーマ指定して保存
> ...
```

## 記事を作成する
ページは `./content/` に markdown ファイルとして格納します。

```bash
# 新たなページを追加 その1
$ hugo new hello.md
content/hello.md created

# 新たなページを追加 その2
$ hugo new post/article.md
content/post/article.md created

# 動作確認用サーバーを起動 (memo: -D はドラフト版も表示するという意味)
# ブラウザでアクセスして表示を確認 (http://localhost:1313/hello/)
# 表示しながら記事を編集するとホットリロードされ、表示が更新されます。
$ hugo server -D
```

## ディレクトリの構造
各資材は以下の構成になっています。

```markdown
.
├ archetypes       ... 新しいページを追加した際の雛形を格納
│ └ default.md
├ config.toml
├ content          ... ページの格納場所
│ ├ hello.md
│ └ post           ... 各ディレクトリをセクションと呼ぶ。第1階層は ContentType とも呼ぶ
│ 　 └ article.md  ... 先程作成した記事
├ data
├ layouts
├ resources
├ static           ... 静的ファイルの格納場所。ビルド先のルートに展開される
└ themes           ... テーマの格納場所
　 └ ananke        ... インストールしたテーマ
```

## 記事のビルド
記事は html 化した上で Web サーバーにホストさせることで公開する。html 化はサブコマンドを指定せず、 `hugo` コマンドによって行える。

```bash
# ./public へ html ファイルを出力
$ hugo
```

# コンテンツの管理
## ページの種類
ページを大きく分けると以下の2種類がある。個々の記事は `Single Page` に属し、 `Index Page` はセクション下にある `Single Page` 一覧を表示するページとして使用される。

| Type        | Path                                 |
| :---------- | :----------------------------------- |
| Single Page | ./content/**/{ArticleName}.md        |
| Single Page | ./content/**/{ArticleName}/index.md  |
| Index Page  | ./content/**/{SectionName}/_index.md |

## ファイルの内容
ページはメタデータを記述するフロントマター箇所と、本文を記述する markdown の2箇所から成ります。メタデータは YAML として記述 (他形式も対応可能. 既定は YAML.) され、タイトルや分類用のタグ、ドラフト版か否か等を記載できます。

```yaml
---
title: "My First Post"
date: 2020-08-03T07:09:35+09:00
tags: [tag1, tag2]
categories: [cat1]
draft: true
custom_prop: [item1, item2, item3]
--- 

# セクション1
サンプルテキスト
```

フロントマターの箇所に子セクションの記事へ継承されるプロパティを指定することも可能です ([Front Matter Cascade](https://gohugo.io/content-management/front-matter/#front-matter-cascade))。これは `Index Page` で配下の `Single Page` のメタデータを指定する場合に使用できます。

```yaml
---
title: "My First Post"
cascade:
 - custom_prop: [item1, item2, item3]
---
```

## ファイルの雛形
新たなページを作成する際、 content 直下のディレクトリ名を Hugo は ContentType として認識します。 ContentType は `./archetypes/{ContentType}.md` としてタイプごとのページ雛形に使用できる他、 html を生成する際のテンプレート指定の制御で使用可能です。

雛形は以下のような形で定義できます。各タイプに対する雛形はタイプ名の markdown ファイルを作成する事で定義できます。全タイプに対する既定雛形を `default.md` として定義する事も可能です。

ファイル名  
* `./content/post/article.md` ⇒ `./archetypes/post.md`
* `./content/anyfile` ⇒ `./archetypes/default.md`

雛形内容  
```yaml
---
title: "{{ replace .Name "-" " " | title }}" 
date: {{ .Date }}
draft: true
---
{{ expression }} で動的要素を定義可能
```


## リソースの配置
ページから画像等のリソースを参照したい場合は `./static/**/{file}` へ格納します。格納するとビルド時に `./**/{file}` として出力される形で生成ファイルから参照可能です。ただ、ページとの結び付きが強いリソースの場合は static フォルダに置くよりもページと同ディレクトリ以下に置いた方が扱いやすくなります。Hugo ではこれを実現する為にページバンドルの仕組みがあります。

この仕組みを使用する場合はページ名でディレクトリを設置します。記事本体はその中にインデックスファイルとして格納し、関連するリソースはディレクトリ配下に設置する事で使用可能です。ページバンドルは2種類あり、テンプレート (後述) で扱う際に参照可能なリソースの種類や範囲で違いがあるため、用途に応じて使い分ける必要があります。

|                          | Leaf Bundle                      | Branch Bundle                |
| :----------------------- | :------------------------------- | :--------------------------- |
| インデックスファイル     | `index.md`                       | `_index.md`                  |
| 使用可能リソースのタイプ | 制限無し                         | ページファイル以外           |
| リソースの配置先         | リソースディレクトリの任意の階層 | リソースディレクトリのみ     |
| テンプレートタイプ       | single                           | list                         |
| バンドルを入れ子         | 不可                             | 可能                         |
| 非インデックスファイル   | リソースとしてのみ参照可能       | 通常ページとしてのみ参照可能 |

Leaf と Branch の例を以下に記載します。

```
# Leaf Bundle
content/posts/my-post
┣ content/posts/my-post/index.md ... index file
┣ subdir
┃ ┗ image1.jpg ... リソース(テンプレート内からの参照時: .Resource.Match "/subdir/image1.jpg")
┣ image2.jpg   ... リソース(テンプレート内からの参照時: .Resource.Match "/subdir/image2.jpg")
┗ page.md      ... リソース(テンプレート内からの参照時: .Resource.Match "/page.md")

# Branch Bundle
content/posts/my-post
┣ content/posts/my-post/_index.md ... index file
┣ subdir
┃ ┗ image1.jpg ... リソース(テンプレート内からの参照時: .Resource.Match "/subdir/image1.jpg")
┣ image2.jpg   ... リソース(テンプレート内からの参照時: .Resource.Match "/subdir/image2.jpg")
┗ page.md      ... ページ (テンプレート内からの参照時: .GetPage "/page.md")
```

## ショートコード
埋め込みコンテンツなどの html を書き込む必要のあるコンテンツは markdown 上では書き込めません (html タグは HUGO によって無効化される)。代わりにいくつかの web サービスの埋込みにはショートコードの仕組みが提供されています。また、ショートコードはテンプレート機能を用いる事で自作も可能です。

```markdown
YouTube 動画の貼付け可能。ショートコードという機能を活用する
{{</* youtube id="OP6NxM6Al98" */>}}

ショートコードは独自のものも作成可能
{{</* hogeshort color = "blue" */>}}
```

# テンプレートの導入
## 描画用テンプレート
HUGO は保有するページを `./layouts/` にあるテンプレートを使用し描画します。 ページの html 化は Go の Template 機能によって実装されており、テンプレートファイル内では `{{expression}}` を仕込むことで動的要素を仕込めます。

```html
<!-- 動的要素の展開 -->
<p>{{ expression }}</p>
```

各ページの描画に使用されるテンプレートは `./layout/{type or kind}/{layout}.html` という形で決定されます。`type` や `kind` 、 `layout` は ./content 下のページのパスから暗黙的に指定されるほか、各ページのフロントマターで明示する事も可能です。 `type` は ContentType とも呼ばれ、フロントマターで未指定の場合には ./content 直下のディレクトリ名が使用されます。

 テンプレートのファイルパスは複数種類が使用可能です。ページパスからの暗黙指定ルールを表形式で記載すると以下のようになります。表中の kind, type では type が優先され、適合するテンプレートが無い場合には `_default` のディレクトリが参照されます。各項目内の複数ワードは先頭ほど優先されて使用されます。

一部の仕様 (2重拡張子の箇所) は記載を割愛してます。詳しくは本家資料を参照してください。  
**Hugo's Lookup Order** (https://gohugo.io/templates/lookup-order/)

| path                    | kind     | type *2                                 | layout *2                               | description                |
| :---------------------- | :------- | :-------------------------------------- | :-------------------------------------- | :------------------------- |
| /_index.md              | home *1  | -                                       | index, home, list                       | トップページ               |
| /something.md           | page     | -                                       | single                                  | 通常ページ                 |
| /{type}/**/_index.md    | section  | {type}                                  | {type}, section, list                   | セクション内の目次ページ   |
| /{type}/**/something.md | page     | {type}                                  | single                                  | 通常ページ                 |
| (/{taxonomy})           | taxonomy | {taxonomy}s, {taxonomy}                 | {taxonomy}.terms, terms, taxonomy, list | タグ一覧ページ             |
| (/{taxonomy}/{term})    | term     | {taxonomy}s, term, taxonomy, {taxonomy} | term, {tag_name}, taxonomy, list        | 個々のタグの記事一覧ページ |

※1 パス的には空相当  
※2 優先度の高い順に記載

## 描画用テンプレート (Partial)
部品化し、独立したファイルにする事も可能です。その場合は ./layouts/partials へ配置して使います。テンプレートへの引数はカレントコンテキストを渡すのに使用される為、オプション指定は .Scratch をまたいで行います。

```html
<!-- layouts/partials/subtemp.html を作成したとする -->
<!-- .Scratch.Get で値を取得する -->
<p>Partial template body {{.Page.Date}}</p>
<p>{{ $param := .Scratch.Get "Param1"}}</p>
```

```html
<!-- パーシャルテンプレートを使う場合は partial 関数を使う -->
<!-- .Scratch.Set を使って値を入れる -->
<p>{{ $param := .Scratch.Set "Param1" "Value" }}</p>
{{ partial "subtemp" . }}
```

## 描画用テンプレート (Block))
block はページの外枠を定義する機構を提供します。 partial との違いは partial が呼び出し元テンプレートの中へ別ファイルとして定義したテンプレートを埋め込みますが、 block は別ファイルとして定義したテンプレートへ呼び出し元のテンプレートが埋め込まれる挙動をします。

使用する際はベーステンプレートとして `baseof.html` を作成し、内部には `block "名前" .` を定義しておきます。各テンプレート内では `define "名前"` を定義して使う事で、 `baseof.html` をベースに `block "名前" .` へ `define "名前"` を入れた状態で描画されます。

```html
<!-- テンプレート呼び出し -->
<!-- 第2引数で指定したものがテンプレート内でのカレントコンテキストになる -->
{{ define "subtemp" }}
    <p>テンプレート内容をここへ定義する</p>
{{ end }}
```

以下のファイルを `./layouts/_default/baseof.html` として作成

```html
<!-- baseof.html 内部では block でサブテンプレートを参照する -->
{{ block "subtemp" . }}
    <p>テンプレートが存在しなかった場合には、ここの定義が使用される</p>
{{ end }}
```

## 独自ショートコードの作成
`./layouts/shortcodes` 内で作成したテンプレートは markdown から呼び出せます。

```bash
# ショートコードは Go の Template 形式で記述する
vim layouts/shortcodes/shortcode-name.html

# markdown ファイル内の使用したい箇所に以下を記述
# 起動時のオプションも attr="value" の形式で記述可能
{{</*shortcode-name attr_name="value" */>}}
```

```go
{{/* ショートコード使用時のオプションは以下の記述で取得可能 */}}
{{ .Get "attr_name" }}
{{/* 未指定時に既定値を使用 */}}
{{ .Get "attr_name" | default "default value" }}
{{/* 未指定時にスコープ内の処理をスキップ */}}
{{ with .Get "attr_name" }}{{ . }}{{ end }}
```

# テンプレートの活用
テンプレートは go 標準の text/template で記述します。

## 値の生成
配列やマップオブジェクトを定義する際は以下の通り。

```go
{{/* 値の代入・参照 */}}
{{ $var_name := expression }}
{{ $var_name }}

{{/* 配列の生成 */}}
{{ slice 100 200 300 }}
{{/* 配列の生成 (シーケンス) */}}
{{ seq 1 5 }}

{{/* マップオブジェクトの生成 */}}
{{ dict "key1" 100 "key2" 200 }}

{{/* ネスト */}}
{{ $var_name := dict "key1" 100 "key2" (slice 200 300 400) }}

{{/* 配列・マップオブジェクトの対象要素へのアクセス */}}
{{ index $var_name "key2" 1 }}
```

## 値の出力
文字列の結合などを行う場合は `printf` を使います。文字列の結合演算子などはありません。

```go
{{ $val = . }}
{{ printf "value: %s, type_info: %T" $val $val }}
```

## コンテキスト
テンプレートは実行される際にコンテキストを持ちます。コンテキストは `"."` で参照でき、大抵のテンプレートは描画中の Page オブジェクトをコンテキストに起動します。Page オブジェクトからはページのタイトルやURL、親ページなどを取得できます。

また、`$.` を使うとグローバルコンテキストを参照できます。これは for 句などで `"."` から参照できるコンテキストが変化した状態で Page オブジェクトを参照しようとした際に使用できます。

参照可能な変数に関する詳細は本家資料を参照してください。  
**Variables and Params** (https://gohugo.io/variables/)

```go
{{/* 描画中のページのタイトルを取得 */}}
{{ $title := .Title }}
{{/* 描画中のページのタイトルを取得 ($を使うとグローバルコンテキストを参照する) */}}
{{ $title := $.Title }}

{{/* 親ページのオブジェクトを取得 */}}
{{ $parent_page_obj := .Parent }}

{{/* 任意のページのオブジェクトを取得 */}}
{{ $other_page_obj := .GetPage "/other" }}
{{ $other_page_url := $other_page_obj.RelPermalink }}
```

## 条件分岐

```go
{{/* 条件分岐 */}}
{{ $val := 2 }}
{{ if eq $val 1 }}
    <p>テキストA</p>
{{ else if eq $val 2 }}
    <p>テキストB</p>
{{ else }}
    <p>テキストC</p>
{{ end }}

{{/* 演算子 */}}
{{/* シェルスクリプト風だが、演算子ではなく関数として実装されている */}}
{{- eq "text_a" "text_a" -}} {{/* == ... true  */}}
{{- ne "text_a" "text_a" -}} {{/* != ... false */}}
{{- not 100 200 -}}          {{/* !  ... false */}}
{{- lt 100 200 -}}           {{/* <  ... true  */}}
{{- le 100 200 -}}           {{/* <= ... true  */}}
{{- gt 100 200 -}}           {{/* >  ... false */}}
{{- ge 100 200 -}}           {{/* >= ... false */}}
```

## ループ処理

```go
{{/* ループ1 (ループ内はカレントコンテキストが列挙中の要素になる) */}}
{{/* 元のコンテキストを参照したい場合には . と書く */}}
{{ range slice "text_a" "text_b" "text_c" }}
    <li>{{.}} {{ $.Page.Title }}</li>
{{ end }}

{{/* ループ1 (変数指定すると添字も取得できる。 */}}
{{/* しかし、変数指定してもカレントコンテキストは切り替わる) */}}
{{ range $idx, $item := slice "text_a" "text_b" "text_c" }}
    <li>{{ $idx }}: {{ $item }}</li>
{{ end }}
```

## パイプライン

```go
{{/* パイプ文字で複数関数を繋ぐと、実行結果を左から右へ流せる */}}
{{ seq 1 5 | shuffle }}

{{/* 複数引数の関数へも使用可能。関数はカリー化されている様子 */}}
{{ "isn't it?" | printf "This is a %s, %s" "pen" }}
```

## セクション
`./content` の記事をディレクトリで整理した場合、ディレクトリは HUGO 上ではセクションとして認識され、各セクションを Page オブジェクトとして扱えます。

```go
{{ .CurrentSection }} ... 現在地のセクション
{{ .Parent }} ... 親セクション
{{ .Sections }} ... 現在地にぶら下がるサブセクション
```

## アセット処理
`./assets` に格納されたリソースは、テンプレートで使用する前に何かしらの処理を加えるといったことが可能です。

```go
{{/* asset/style からCSSファイルを2本取得 */}}
{{ $css_1 := resources.Get "style/1.css" |  }}
{{ $css_2 := resources.Get "style/2.css" |  }}

{{/* CSSファイル2本を結合し、新たなファイル名を main.css と命名 */}}
{{ $css_file := slice $css_1 $css_2 | resources.Concat "style/main.css" }}

{{/* RelPermalink などで処理結果を使用可能 */}}
<link rel="stylesheet" href="{{ $css_file.RelPermalink }}">
```