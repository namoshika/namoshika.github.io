---
title: "Hugo"
date: 2020-08-21T08:52:02+09:00
tags: [Hugo]
draft: false
---

# 最初のサイト作成
## サイトを作成する

```bash
# サイトディレクトリを作成
$ mkdir HelloHugo
$ cd HelloHugo

# 中を初期化
$ hugo new site

# 好みのテーマファイルを取得 (ここでは ananke を指定)
$ cd theme
$ git clone https://github.com/budparr/gohugo-theme-ananke.git
$ vim ../config.toml
> ...
> theme = "ananke" ... テーマ指定して保存
> ...
```

## 記事を作成する
コンテンツは markdown ファイルとして `./content/` に格納します。

```bash
# 新たなページを追加
$ hugo new hello.md
content/hello.md created

# 動作確認用サーバーを起動 (memo -D はドラフト版も表示するという意味)
# ブラウザでアクセスして表示を確認 (http://localhost:1313/hello/)
# 表示しながら記事を編集するとホットリロードされ、表示が更新されます。
$ hugo server -D

# memo:
# content 直下のディレクトリ名はセクションとして Hugo 上で意味を持ちます。
# セクション毎にいくつかの要素を定義できます。
#  - layouts/post ... post タイプで使用する見掛けを格納可能
#  - archetypes/post.md ... markdown ファイル生成時の雛形を格納可能
$ hugo new post/article.md
content/post/article.md created
```

## 記事の構造
コンテンツは markdown ファイルとして記述していきます。

```markdown
---
title: "My First Post"
date: 2020-08-03T07:09:35+09:00
tags: [tag1, tag2]
categories: [cat1]
draft: true
custom_prop: [item1, item2, item3]
--- 

上部の構造はフロントマターと呼ばれる。複数のフォーマットで宣言可能だが、
`---` で区切られている場合は YAML として解釈される。

# セクション1
サンプルテキスト

YouTube 動画の貼付け可能。ショートコードという機能を活用する
{{ </*youtube id="OP6NxM6Al98"*/> }}

ショートコードは独自のものも作成可能
{{</*hogeshort color = "blue"*/>}}

# セクション2
ショートコードのエスケープは以下の通り  
{{</* youtube id="OP6NxM6Al98" */>}}
```

## ディレクトリの構造
各資材は以下の構成になっています。

```markdown
.
├── archetypes         ... 新しいコンテンツを追加した際の雛形を格納
│   └── default.md
├── config.toml
├── content            ... コンテンツの格納場所
│   ├── hello.md
│   └── post           ... 各ディレクトリをセクションと呼ぶ
│       └── article.md ... 先程作成した記事
├── data
├── layouts
├── resources
├── static             ... 静的ファイルの格納場所。ビルド先のルートに展開される
└── themes             ... テーマの格納場所
    └── ananke         ... インストールしたテーマ
```

# 更に深堀りする
## ショートコード
埋め込みコンテンツなどの html を書き込む必要のあるコンテンツは markdown 上では書き込めない (html タグは HUGO によって無効化される)。代わりにいくつかの web サービスの埋込みにはショートコードの仕組みが提供されています。

```html
<!-- Youtube 動画を埋め込む -->
{{ </*youtube id="OP6NxM6Al98"*/> }}
```

独自のショートコードも作成可能。

```bash
# ショートコードは Go の Template 形式で記述する
vim layouts/shortcodes/shortcode-name.html

# markdown ファイル内の使用したい箇所に以下を記述
{{</*shortcode-name*/>}}
```

## テンプレート
HUGO ではコンテンツの html 化は Go の Template 機能によって実装されています。 ファイル内に `{{expression}}` を仕込むことで動的要素を仕込めます。

```html
<!-- 動的要素の展開 -->
<p>{{ expression }}</p>
```

### 値の生成

```html
<!-- 値の代入・参照 -->
{{ $var_name := expression }}
{{ $var_name }}

<!-- 配列の生成 -->
{{ slice 100 200 300 }}
<!-- 配列の生成 (シーケンス) -->
{{ seq 1 5 }}

<!-- マップオブジェクトの生成 -->
{{ dict "key1" 100 "key2" 200 }}

<!-- ネスト -->
{{ $var_name := dict "key1" 100 "key2" (slice 200 300 400) }}

<!-- 配列・マップオブジェクトの対象要素へのアクセス -->
{{ index $var_name "key2" 1 }}
```

### 条件分岐

```html
<!-- 条件分岐 -->
{{ $val := 2 }}
{{ if eq $val 1 }}
<p>テキストA</p>
{{ else if eq $val 2 }}
<p>テキストB</p>
{{ else }}
<p>テキストC</p>
{{ end }}

<!-- 演算子 -->
<!-- シェルスクリプト風だが、演算子ではなく関数として実装されている -->
{{ eq "text_a" "text_a" }}
{{ gt "text_a" "text_a" }} etc...
```

### ループ処理

```html
<!-- ループ1 (ループ内はカレントコンテキストが列挙中の要素になる) -->
<!-- 元のコンテキストを参照したい場合には $. と書く -->
{{ range slice "text_a" "text_b" "text_c" }}
<li>{{.}} {{ $.Page.Title }}</li>
{{ end }}

<!-- ループ1 (変数指定すると添字も取得できる。 -->
<!-- しかし、変数指定してもカレントコンテキストは切り替わる) -->
{{ range $idx, $item := slice "text_a" "text_b" "text_c" }}
<li>{{ $idx }}: {{ $item }}</li>
{{ end }}
```

### パイプライン

```html
<!-- パイプ文字で複数関数を繋ぐと、実行結果を左から右へ流せる -->
{{ seq 1 5 | shuffle }}

<!-- 複数引数の関数へも使用可能。関数はカリー化されている様子 -->
{{ "isn't it?" | printf "This is a %s, %s" "pen" }}
```

### テンプレート (Nested)
共通した構造はテンプレートを使うと使い回せます。

```html
<!-- ネステッドテンプレート定義 -->
{{ define "T1" }}
    <p>template body {{.Page.Date}}</p>
{{ end }}

<!-- テンプレート呼び出し -->
<!-- 第2引数で指定したものがテンプレート内でのカレントコンテキストになる -->
{{ template "T1" . }}

```

### テンプレート (Partial)
独立したファイルとして切出しも可能です。その場合は ./layouts/partials へ配置して使います。

```html
<!-- layouts/partials/subtemp.html を作成したとする -->
<p>Partial template body {{.Page.Date}}</p>

<!-- テンプレート呼び出し -->
<!-- パーシャルテンプレートを使う場合は partial 関数を使う -->
{{ partial "subtemp" . }}
```

### テンプレート (Base)
パーシャルテンプレートと似ているが、 `baseof.html` を使うと全てのページに対する共通構造を定義できます。独立ファイル内でネステッドテンプレート風に名前を定義し、共通構造内で `block "名前"` を使う事で個々の要素を定義します。

```html
<!-- baseof.html 内部では block でサブテンプレートを参照する -->
<!-- ./layouts/_default/baseof.html として配置する -->
{{ block "subtemp" . }}
```

```html
<!-- 第2引数が空文字やnilの場合に第1引数を出力 -->
{{ default "foo" nil }}
```

## セクション
`./content` の記事をディレクトリで整理した場合、ディレクトリは HUGO 上ではセクションとして認識され、各セクションを Page オブジェクトとして扱える。

```html
{{ .Page.CurrentSection }} ... 現在地のセクション
{{ .Page.Parent }} ... 親セクション
{{ .Page.Sections }} ... 現在地にぶら下がるサブセクション
```

パンくずリスト原型

```html
<ul>
    {{ template "breadcrumb" .Page.CurrentSection }}
    {{ define "breadcrumb" }}
        {{ with .Parent }}
            {{ template "breadcrumb" . }}
        {{ end }}
        {{ with . }}
            <li>{{- .Title -}}</li>
        {{ end }}
    {{ end }}
</ul>
```

## フロントマター
フロントマターの箇所に子要素へ継承されるプロパティを指定することも可能です ([Front Matter Cascade](https://gohugo.io/content-management/front-matter/#front-matter-cascade))。テンプレートからアクセスする際にカスケードかを意識する必要ありません。

```YAML
---
title: "My First Post"
cascade:
    - custom_prop: [item1, item2, item3]
---
```
