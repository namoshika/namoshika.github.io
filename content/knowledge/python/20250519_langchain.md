---
title: "LangChain"
date: 2025-05-19T21:23:05+09:00
tags: []
draft: false
---
# 概要
LangChain は LLM を活用したアプリケーションの開発を支援するフレームワークである。これを使うことで、 LLM を活用したシステムへ以下のような機能を持たせる事ができる。

* データ接続: ドキュメントやAPIから情報を取得し、コンテキストに沿った応答を生成
* エージェント機能: 外部ツール呼び出しを委譲し、自律的なタスク実行を実現
* チェーン: 複数のLLM呼び出しと処理を直列・並列に組み合わせるワークフロー
* RAG: ベクトルストア検索と生成を組み合わせ、高精度な情報提供

# 1. 使う準備
pip で導入できる。
Gemini で使うために langchain-google-genai もインストールする

```bash
pip install langchain langchain-google-genai
```

Gemini の使用には API Key を要する。  
https://aistudio.google.com/

使用可能なモデル  
https://ai.google.dev/gemini-api/docs/models

```py
import os
from langchain_google_genai import ChatGoogleGenerativeAI

GEMINI_API_KEY=os.environ.get("GEMINI_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=GEMINI_API_KEY)
```

# 2. 基本的な使い方
現状の LangChain は言語モデルの入出力を以下のように扱う。

* 入力 ... 複数メッセージ
* 出力 ... 単一メッセージ

```py
from langchain_core.messages import HumanMessage, SystemMessage

# Type.1
res = llm.invoke([
    SystemMessage("アクシス教の信者として振舞ってください"),
    HumanMessage("働きたくないでござる")
])
res.pretty_print()

# Type.2
res = llm.invoke([
    { "role": "system", "content": "アクシス教の信者として振舞ってください"},
    { "role": "human", "content": "働きたくないでござる"}    
])
res.pretty_print()
```

# 3. プロンプトの組み立て
## StringPrompt
文字列の組み立て

```py
from langchain_core.prompts import PromptTemplate

tmpl = PromptTemplate.from_template("hello {name}")
print(tmpl.__repr__())

prompt = tmpl.invoke({ "name": "world" })
print(prompt.__repr__())
```

出力

```
PromptTemplate(input_variables=['name'], input_types={}, partial_variables={}, template='hello {name}')
StringPromptValue(text='hello world')
```

## MessagePrompt
文字列に加え、ロールを付与できる。
与えるプロンプトを言語モデルが開発者とユーザで区別する必要が有る場合 (チャットボットなど) に使用する。

```py
from langchain_core.prompts import (
    AIMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
)

# 入力用テンプレート (人用)
tmpl = HumanMessagePromptTemplate.from_template("hello {name}")
print(tmpl.__repr__())

prompt = tmpl.format_messages(name="world")
print(prompt.__repr__())

tmpl = ChatPromptTemplate.from_messages([tmpl, tmpl])
# メッセージのリストを作る
print(tmpl.format_messages(name="world").__repr__())

# メッセージを内包した PromptValue を作る
# to_string() で文字列に変換できる
prompt = tmpl.format_prompt(name="world")
print(prompt.__repr__())
print(prompt.to_string())
```

出力

```
HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=['name'], input_types={}, partial_variables={}, template='hello {name}'), additional_kwargs={})
[HumanMessage(content='hello world', additional_kwargs={}, response_metadata={})]
[HumanMessage(content='hello world', additional_kwargs={}, response_metadata={}), HumanMessage(content='hello world', additional_kwargs={}, response_metadata={})]
ChatPromptValue(messages=[HumanMessage(content='hello world', additional_kwargs={}, response_metadata={}), HumanMessage(content='hello world', additional_kwargs={}, response_metadata={})])
Human: hello world
Human: hello world
```

カスタムロールを使える場合も有る。

```py
from langchain_core.prompts import ChatMessagePromptTemplate

# 入力用テンプレート (カスタムロール)
tmpl = ChatMessagePromptTemplate.from_template("hello {name}", role="cutom_role")
tmpl = ChatPromptTemplate.from_messages([tmpl, tmpl])

prompt = tmpl.format_prompt(name="world")
print(prompt.to_string())
```

出力

```
cutom_role: hello world
cutom_role: hello world
```

# 4. 出力を構造化する
LLM の出力をプログラムから扱いたい場合、オブジェクトとして構造化すると扱いやすい。

```py
# from typing import TypedDict, Annotated
from enum import Enum
from pydantic import BaseModel, Field

class Hand(Enum):
    Gu: str = "グー"
    Choki: str = "チョキ"
    Pa: str = "パー"

class ModelResponse(BaseModel):
    """じゃんけんで出す手を格納"""
    result:Hand = Field(description="グー、チョキ、パーの中から出した手")

# TypedDict 非対応っぽい。 Pydantic が必要そう
# 参考: https://github.com/langchain-ai/langchain/issues/24225
llm.with_structured_output(ModelResponse).invoke([
  { "role": "user", "content": "最初はグー！じゃ～んけ～んぽん！"}
])
```

出力

```
ModelResponse(result=<Hand.Gu: 'グー'>)
```

# 5. ツールの呼び出し
使用できるツールの情報を与える事で LLM からツールを呼び出させる事ができる。呼び出し自体はコードを書く

```py
from enum import Enum
from typing import Annotated
from langchain.tools import Tool, tool

@tool
def get_weather(location: str) -> str:
    """天気を取得する"""
    return "晴れ"

@tool
def get_jancken() -> str:
    """じゃんけんの出す手を取得する"""
    import random
    return random.choice(["グー", "チョキ", "パー"])

tool_list = [get_weather, get_jancken]
tool_dict = {item.name: item for item in tool_list}
llm_binded_tools = llm.bind_tools(tool_list)
res = llm_binded_tools.invoke("天気を教えて。それからじゃんけんしよ！最初はグー！じゃんけんっ！")
res.tool_calls

tool_messages = [tool_dict[item["name"]].invoke(item) for item in res.tool_calls]
print(tool_messages)
```

出力

```
[ToolMessage(content='晴れ', name='get_weather', tool_call_id='fe818fad-abf3-452e-9a25-53b7f766e4d4'),
 ToolMessage(content='グー', name='get_jancken', tool_call_id='03a3e350-0401-43bc-840b-117a89c2720a')]
```

# 6. 埋め込み表現を取得する
AWS Bedrock で提供されている多言語埋め込みモデルを使う。

```bash
# Gemini Embedding はまだプレビューであるため、 AWS Bedrock を使う。
pip install langchain-aws
```

```py
import os
from langchain_aws.embeddings import BedrockEmbeddings

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION")

embmodel = BedrockEmbeddings(
    model_id="amazon.titan-embed-text-v2:0",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION
)
res = embmodel.embed_query("hoge")
res[:5]
```
