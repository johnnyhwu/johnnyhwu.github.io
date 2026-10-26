# 小測試：Mini 文章

## 前言

這篇文章示範一個小例子。我們先給結論：方法 A 在 24 格中有 23 格為正。

## 問題

ReAct 每一步都在摸索，容易重複無效的動作。

![左邊是知識圖譜，右邊是流程圖。](img-001)
*圖 1 — 知識與流程。（來源：原始論文。）*

## 方法

圖的形式是 $G = (V, E)$，其中 $V$ 是節點集合。

驗證閘門的規則如下：

$$
S(G) \ge S(G')
$$

> 這裡有個漏洞：驗證器不檢查工具名稱，只靠 prompt 約束。

接下來看實驗。

```figure-map
[
  {"id": "img-001", "references_manifest_caption": "Figure 1 | From knowledge to procedure.", "why_used": "x", "agent_match_hint": "y"}
]
```
