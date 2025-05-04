---
# weight: 1
title: "LangMem 基本概念介紹"
date: 2025-05-04
lastmod: 2025-05-04
draft: true
description: ""
featuredImage: "featured-image.jpg"

tags: ["Large Language Model", "Agent Memory"]
categories: ["other"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "other/:contentbasename"
---

<!--more-->

## 前言

本篇文章為 DeepLearning.AI 所開設的 [Long-Term Agentic Memory with LangGraph](https://www.deeplearning.ai/short-courses/long-term-agentic-memory-with-langgraph/) 課程筆記。希望讀者能夠透過本篇文章，理解 Agent Memory 的基本概念，以及如何透過 [LangMem](https://github.com/langchain-ai/langmem) 實踐 Agent Memory！

## 為什麼 Agent 需要 Memory

了解 Agent 的 Memory 之前，我們先思考這個問題：
> 為什麼 Agent 需要 Memory ?

作者舉一個能夠自動回覆 Email 的 Agent 來說明。如下圖示，這個 LLM 需要在讀取信件內容後，透過 Tool Calling 查看收件者的行事曆 (Calendar Tool)，再透過 Tool Calling 進行 Email 內容的撰寫 (Email Writing Tool)：

{{< image src="email-agent.png" caption="一個能夠自動回覆 Email 的 Agent" >}}

在這個過程中，LLM 需要過去的經驗，幫助它克服一些挑戰。如下圖中的紅字所述：

{{< image src="email-agent-challenge.png" caption="Email Agent 會遇到的挑戰" >}}

如果 Agent 有記憶能力 (Memory)，就能夠參考過去的經驗來處理新的任務。如此一來，Agent 就能夠隨著處理的任務愈多，收集到愈多經驗，而變得更厲害。

## Memory 的類型以及運作時機

Agent 的 Memory 主要可以分為三種類型:

{{< image src="memory-type.png" caption="Agent Memory 的類型" >}}

- Semantic Memory: 存放與「事實」相關的內容（我覺得以廣義來說「文件」也可以當成這個類別）
- Episodic Memory: 存放與「經驗」相關的內容（Ex. 放在 Prompt 中的 Few-Shot Examples）
- Procedural Memory: 存放與「指令」相關的內容（Ex. 給 LLM 的 System Prompt）

而 Agent Memory 的運作時機主要有兩種：

{{< image src="memory-work.png" caption="Agent Memory 的類型" >}}

- In the hot path: 在收到 User 的每次 Query 時都會進行 Memory 的讀取與寫入
- In the background: 在 Agent 的運行過程中，會定期進行 Memory 的讀取與寫入

## Email Agent w/ & w/o Memory

理解了 Agent Memory 的基本概念後，我們來看看在 Email Agent 中，Memory 的運作方式。下圖為一個基本的 Email Agent，沒有使用 Memory 的情況下的 Worflow:

{{< image src="email-agent-wo-memory.png" caption="Email Agent 沒有 Memory" >}}

而下圖為一個使用 Memory 的 Email Agent 的 Workflow:

{{< image src="email-agent-w-memory.png" caption="Email Agent 有 Memory" >}}

可以發現到：
- Episodic Memory: 其實就是放在 Prompt 中的 Few-Shot Examples，幫助 LLM 判斷這個 Email 是否需要回覆
- Procedural Memory: 其實就是寫在 LLM 的 System Prompt 中的內容，告訴 LLM 如何使用 Calandar Tool 以及 Email Writing Tool
- Semantic Memory: 存放既定的事實 (Ex. Response Preference)

## Email Agent 的實做 (不具備 Memory)

接著，先實做一個基本的 Email Agent，這個 Agent 不具備 Memory 的功能:

{{< image src="email-agent-wo-memory.png" caption="Email Agent 沒有 Memory" >}}

### Triage 的實做

Triage 基本上就是透過 LLM 來對目前的郵件進行分類，分為三類：
- ignore: 忽略這封郵件
- notify: 這封郵件是重要的資訊，但不需要回覆
- respond: 這封郵件需要回覆

```python
from pydantic import BaseModel, Field
from typing_extensions import TypedDict, Literal, Annotated
from langchain.chat_models import init_chat_model

llm = init_chat_model("openai:gpt-4o-mini")

class Router(BaseModel):
    """Analyze the unread email and route it according to its content."""

    reasoning: str = Field(
        description="Step-by-step reasoning behind the classification."
    )
    classification: Literal["ignore", "respond", "notify"] = Field(
        description="The classification of an email: 'ignore' for irrelevant emails, "
        "'notify' for important information that doesn't need a response, "
        "'respond' for emails that need a reply",
    )

llm_router = llm.with_structured_output(Router)
```

{{< admonition tip >}}
比較有趣的是，作者這邊是透過 `pydantic` 來定義這個 Router 的結構化輸出，這樣的做法可以讓 LLM 的輸出更具結構性，並且能夠更方便地進行後續的處理。除了 LangChain 支援這樣的作法之外，[outlines](https://github.com/dottxt-ai/outlines) 也是一個讓 LLM 進行 Structured Text Generation 的選擇。
{{< /admonition >}}

`llm_router` 的實際使用方式如下：

```python
result = llm_router.invoke(
    [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
)
```

而 System Prompt 的內容如下：

```text
< Role >
You are John Doe's executive assistant. You are a top-notch executive assistant who cares about John performing as well as possible.
</ Role >

< Background >
Senior software engineer leading a team of 5 developers. 
</ Background >

< Instructions >

John gets lots of emails. Your job is to categorize each email into one of three categories:

1. IGNORE - Emails that are not worth responding to or tracking
2. NOTIFY - Important information that John should know about but doesn't require a response
3. RESPOND - Emails that need a direct response from John

Classify the below email into one of these categories.

</ Instructions >

< Rules >
Emails that are not worth responding to:
Marketing newsletters, spam emails, mass company announcements

There are also other things that John should know about, but don't require an email response. For these, you should notify John (using the `notify` response). Examples of this include:
Team member out sick, build system notifications, project status updates

Emails that are worth responding to:
Direct questions from team members, meeting requests, critical bug reports
</ Rules >

< Few shot examples >
None
</ Few shot examples >
```

而 User Prompt 的內容如下：

```text
Please determine how to handle the below email thread:

From: Alice Smith <alice.smith@company.com>
To: John Doe <john.doe@company.com>
Subject: Quick question about API documentation

Hi John,

I was reviewing the API documentation for the new authentication service and noticed a few endpoints seem to be missing from the specs. Could you help clarify if this was intentional or if we should update the docs?

Specifically, I'm looking at:
- /auth/refresh
- /auth/validate

Thanks!
Alice
```

### Tools 的實做

接著，作者定義了 3 種 Tool 讓 LLM 使用：

```python
from langchain_core.tools import tool

@tool
def write_email(to: str, subject: str, content: str) -> str:
    """Write and send an email."""
    # Placeholder response - in real app would send email
    return f"Email sent to {to} with subject '{subject}'"

@tool
def schedule_meeting(
    attendees: list[str], 
    subject: str, 
    duration_minutes: int, 
    preferred_day: str
) -> str:
    """Schedule a calendar meeting."""
    # Placeholder response - in real app would check calendar and schedule
    return f"Meeting '{subject}' scheduled for {preferred_day} with {len(attendees)} attendees"

@tool
def check_calendar_availability(day: str) -> str:
    """Check calendar availability for a given day."""
    # Placeholder response - in real app would check actual calendar
    return f"Available times on {day}: 9:00 AM, 2:00 PM, 4:00 PM"
```

### Main Agent 的實做

Main Agent 的任務是透過使用 Tools 來完成 Email 回覆的任務：

```python
from langgraph.prebuilt import create_react_agent

tools=[write_email, schedule_meeting, check_calendar_availability]
agent = create_react_agent(
    "openai:gpt-4o",
    tools=tools,
    prompt=create_prompt,
)
```

而這邊的 `create_prompt` 的內容如下：

```text
< Role >
You are John Doe's executive assistant. You are a top-notch executive assistant who cares about John performing as well as possible.
</ Role >

< Tools >
You have access to the following tools to help manage John's communications and schedule:

1. write_email(to, subject, content) - Send emails to specified recipients
2. schedule_meeting(attendees, subject, duration_minutes, preferred_day) - Schedule calendar meetings
3. check_calendar_availability(day) - Check available time slots for a given day
</ Tools >

< Instructions >
Use these tools when appropriate to help manage John's tasks efficiently.
</ Instructions >
```

而 Main Agent 的使用方式如下：

```python
response = agent.invoke(
    {"messages": [{
        "role": "user", 
        "content": "what is my availability for tuesday?"
    }]}
)
```

Main Agent 的輸出：
```text
================================== Ai Message ==================================

You have the following available times on Tuesday:

- 9:00 AM
- 2:00 PM
- 4:00 PM

If you need me to schedule anything or make any arrangements, just let me know!
```

### 透過 LangGraph 整合為一個 Workflow

最後，將上述的 Triage 與 Main Agent 整合為一個 Workflow。

```python
from langgraph.graph import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from typing import Literal

class State(TypedDict):
    email_input: dict
    messages: Annotated[list, add_messages]

def triage_router(state: State) -> Command[
    Literal["response_agent", "__end__"]
]:
    author = state['email_input']['author']
    to = state['email_input']['to']
    subject = state['email_input']['subject']
    email_thread = state['email_input']['email_thread']

    system_prompt = triage_system_prompt.format(
        full_name=profile["full_name"],
        name=profile["name"],
        user_profile_background=profile["user_profile_background"],
        triage_no=prompt_instructions["triage_rules"]["ignore"],
        triage_notify=prompt_instructions["triage_rules"]["notify"],
        triage_email=prompt_instructions["triage_rules"]["respond"],
        examples=None
    )
    user_prompt = triage_user_prompt.format(
        author=author, 
        to=to, 
        subject=subject, 
        email_thread=email_thread
    )
    result = llm_router.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    if result.classification == "respond":
        print("📧 Classification: RESPOND - This email requires a response")
        goto = "response_agent"
        update = {
            "messages": [
                {
                    "role": "user",
                    "content": f"Respond to the email {state['email_input']}",
                }
            ]
        }
    elif result.classification == "ignore":
        print("🚫 Classification: IGNORE - This email can be safely ignored")
        update = None
        goto = END
    elif result.classification == "notify":
        # If real life, this would do something else
        print("🔔 Classification: NOTIFY - This email contains important information")
        update = None
        goto = END
    else:
        raise ValueError(f"Invalid classification: {result.classification}")
    return Command(goto=goto, update=update)

email_agent = StateGraph(State)
email_agent = email_agent.add_node(triage_router)
email_agent = email_agent.add_node("response_agent", agent)
email_agent = email_agent.add_edge(START, "triage_router")
email_agent = email_agent.compile()
```

Email Agent 的整體 Workflow 如下圖所示：

{{< image src="email-agent-langgraph.png" caption="Email Agent 的整體 Workflow" >}}

### Email Agent 範例輸入與輸出
- 範例輸入 1: 不需要回覆的 Email
    ```python
    email_input = {
        "author": "Marketing Team <marketing@amazingdeals.com>",
        "to": "John Doe <john.doe@company.com>",
        "subject": "🔥 EXCLUSIVE OFFER: Limited Time Discount on Developer Tools! 🔥",
        "email_thread": """Dear Valued Developer,

    Don't miss out on this INCREDIBLE opportunity! 

    🚀 For a LIMITED TIME ONLY, get 80% OFF on our Premium Developer Suite! 

    ✨ FEATURES:
    - Revolutionary AI-powered code completion
    - Cloud-based development environment
    - 24/7 customer support
    - And much more!

    💰 Regular Price: $999/month
    🎉 YOUR SPECIAL PRICE: Just $199/month!

    🕒 Hurry! This offer expires in:
    24 HOURS ONLY!

    Click here to claim your discount: https://amazingdeals.com/special-offer

    Best regards,
    Marketing Team
    ---
    To unsubscribe, click here
    """,
    }

    response = email_agent.invoke({"email_input": email_input})
    ```

    ```text
    🚫 Classification: IGNORE - This email can be safely ignored
    ```
- 範例輸入 2: 需要回覆的 Email
    ```python
    email_input = {
        "author": "Alice Smith <alice.smith@company.com>",
        "to": "John Doe <john.doe@company.com>",
        "subject": "Quick question about API documentation",
        "email_thread": """Hi John,

    I was reviewing the API documentation for the new authentication service and noticed a few endpoints seem to be missing from the specs. Could you help clarify if this was intentional or if we should update the docs?

    Specifically, I'm looking at:
    - /auth/refresh
    - /auth/validate

    Thanks!
    Alice""",
    }

    response = email_agent.invoke({"email_input": email_input})
    ```

    ```text
    📧 Classification: RESPOND - This email requires a response
    ```

    ```python
    for m in response["messages"]:
        m.pretty_print()
    ```

    ```text
    ================================ Human Message =================================

    Respond to the email {'author': 'Alice Smith <alice.smith@company.com>', 'to': 'John Doe <john.doe@company.com>', 'subject': 'Quick question about API documentation', 'email_thread': "Hi John,\n\nI was reviewing the API documentation for the new authentication service and noticed a few endpoints seem to be missing from the specs. Could you help clarify if this was intentional or if we should update the docs?\n\nSpecifically, I'm looking at:\n- /auth/refresh\n- /auth/validate\n\nThanks!\nAlice"}
    ================================== Ai Message ==================================
    Tool Calls:
    write_email (call_1ndxzPIinVSvav1pBioakpQR)
    Call ID: call_1ndxzPIinVSvav1pBioakpQR
    Args:
        to: alice.smith@company.com
        subject: Re: Quick question about API documentation
        content: Hi Alice,

    Thank you for reaching out with your question about the API documentation. I can confirm that the endpoints /auth/refresh and /auth/validate should indeed be included in the documentation. It was an oversight, and the documentation needs to be updated.

    I'll ensure that the team updates the documentation to include these endpoints as soon as possible.

    Best regards,

    John Doe
    ================================= Tool Message =================================
    Name: write_email

    Email sent to alice.smith@company.com with subject 'Re: Quick question about API documentation'
    ================================== Ai Message ==================================

    I have responded to Alice's email, clarifying that the endpoints she mentioned should be included in the documentation and that the team will update the documentation accordingly.
    ```
