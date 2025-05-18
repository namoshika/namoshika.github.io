---
title: "Google Gen AI SDK"
date: 2025-05-18T21:23:51+09:00
tags: []
draft: false
---

# 概要
Gemini API を使用すると、Google の最新の生成モデルにアクセスできる。Python からは Google Gen AI SDK を通すことで簡単に使用できる。

Gemini の使用には API Key を要し、Google AI Studio から発行可能。  
https://aistudio.google.com/

```bash
$ pip install google-genai
```

```py
import os
from google import genai

GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)
```

※ 古い SDK に注意  
以下のような import がある場合、Gen AI SDK へ移行する前の Gemini SDK が使われている。
画像生成へ対応するなど、Gen AI SDK の方が適用範囲が広い。

```py
import google.generativeai as genai
```

# 1. 質問する
使用可能なモデル  
https://ai.google.dev/gemini-api/docs/models?hl=ja

## 基本的な使い方

```py
from IPython.display import  Markdown

response = client.models.generate_content(
  model="gemini-2.0-flash",
  contents="AI の仕組みを IT エンジニア向けに 400 文字前後で説明してください"
)
Markdown(response.text)
```

## ロールを指定

```py
from IPython.display import  Markdown

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="私は罪を犯しました。豆腐の角で隣人を殴ってしまいました",
    config={
        "system_instruction": "あなたは神です。質問に対して神らしく回答してください。"
    }
)
Markdown(response.text)
```

# 2. 画像を入力する
## 画像認識させる

```py
import PIL.Image
from IPython.display import  Markdown

img_sample = PIL.Image.open("sample.jpg")
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=["この画像には何が写っているのかを説明してください", img_sample]
)

Markdown(response.text)
```

## 物体検知させる

```py
import PIL.Image
from dataclasses import dataclass
from typing import TypedDict

class BoundingBox(TypedDict):
    ymin: int
    xmin: int
    ymax: int
    xmax: int

class DetectedObject(TypedDict):
    name: str
    boundingbox: BoundingBox

img_sample = PIL.Image.open("sample.jpg")
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[img_sample, '画像の中の物体をバウンディングボックスで囲ってください。結果は次の形式に沿ってJSON ({"name": "detected_object_name", "bounding_box": [ymin, xmin, ymax, xmax]}) で出力してください。JSONのみを出力してください'],
    config={ "response_mime_type": "application/json", "response_schema": list[DetectedObject] }
)
```

出力

```json
[{"name": "cat", "boundingbox": {"ymin": 176, "xmin": 100, "ymax": 620, "xmax": 795}}]
```

# 3. チャット形式
過去のやり取りの文脈を反映させたい場合にはセッションを作る。

コード

```py
sess = client.chats.create(model="gemini-2.0-flash")
res = sess.send_message("こんにちわ")
print(res.text)

res = sess.send_message("私はケビンです")
print(res.text)

res = sess.send_message("私の名前はなんでしょう")
print(res.text)
```

出力

> こんにちは！何かお手伝いできることはありますか？😊
> 
> ケビンさん、こんにちは！ どんなことに関心がありますか？ 何かお手伝いできることがあれば教えてくださいね。😊
> 
> あなたはケビンさんです。そう言いましたね。

# 4. コード実行
コード

```py
import  google.genai.types as typs
from IPython.display import  Markdown

response = client.models.generate_content(
    model="gemini-1.5-flash",
    contents="整数を1～40まで表示する python を生成し実行結果を出力してください。ただし 3の倍数と3のつく数字だけアホになります",
    config=typs.GenerateContentConfig(
        tools=[typs.Tool(code_execution=typs.ToolCodeExecution)],
    )
)
Markdown(response.text)
```

出力

````plain
```python
for i in range(1, 41):
    if i % 3 == 0 or '3' in str(i):
        print("アホ")
    else:
        print(i)
```

実行結果：

```
1
2
アホ
4
5
アホ
7
8
アホ
10
11
アホ
...
アホ
アホ
40
```
````

コードと実行結果は分けて扱うことも可能。

```py
print(response.executable_code)
print(response.code_execution_result)
```

# 5. 画像を生成

```py
from IPython.display import  display
from io import BytesIO
from PIL import Image

response = client.models.generate_content(
    model="gemini-2.0-flash-preview-image-generation",
    contents="Linus Torvalds playing PC games happily on Windows",
    config={ "response_modalities": ['TEXT', 'IMAGE']}
)

bytes_png = response.candidates[0].content.parts[1].inline_data.data
image = Image.open(BytesIO((bytes_png)))
display(image)
```

# 6. ツール呼び出し

```py
from google.genai.types import GenerateContentConfig, Tool

weather_func = {
    "name": "get_current_weather",
    "description": "現在地の天気を取得します",
    "parameters": {
        "type": "object",
        "properties": {
            "location": { "type": "string", "description": "都市名" }
        },
        "required": ["location"]
    },
}
tools = Tool(functionDeclarations=[weather_func])
conf = GenerateContentConfig(tools=[tools])
res = client.models.generate_content(
    model="gemini-2.0-flash", contents="東京の天気", config=conf
)
res
```

ツールが呼び出されると以下のようになる。

```py
res.function_calls
> [FunctionCall(id=None, args={'location': '東京'}, name='get_current_weather')]
```

# 7. 埋め込み表現を取得する
参考: https://ai.google.dev/gemini-api/docs/embeddings?hl=ja

```py
result = client.models.embed_content(
    model="gemini-embedding-exp-03-07",
    contents=["わっしょいわっしょい", "あばばば"],
    config={ "task_type": "SEMANTIC_SIMILARITY" }
)
print(result.embeddings)
```

```Py
len(result.embeddings)
> 2

result.embeddings[0].values[:10]
> 
[-0.016820915,
 -0.0012726645,
  0.01619753,
 -0.07796676,
 -0.033992294,
  0.00074800395,
  0.0039061843,
  0.004672302,
  0.016051557,
  0.019814486
]
```
