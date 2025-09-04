---
# weight: 1
title: "FastAPI 的並行陷阱：從 Race Condition 到 Deadlock，徹底搞懂全域變數的正確用法"
date: 2025-08-31
lastmod: 2025-09-04
draft: False
description: "FastAPI 中共用全域變數會導致 Race Condition 嗎？本文深入探討 FastAPI 的多執行緒與 Async 機制，解析 Thread-Safe 與 Async-Safe 的關鍵差異，並教你如何避免死鎖、寫出真正安全的並行程式碼。"
featuredImage: "featured-image.jpg"

tags: ["Operating System", "Python Tip"]
categories: ["other"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "other/:contentbasename"
---

<!--more-->

## 前言

在做 AI 服務的 PoC 開發時，我們經常會透過 [FastAPI](https://fastapi.tiangolo.com/) 來建立一個 Server，讓 Client 端可以藉由一些 Endpoint 存取到 AI 服務以方便測試。

有些時候，由於 AI 服務的初始化 (將抽象的 AI 服務初始化程式中的實體物件) 需要時間，我們沒有辦法針對每個 Request 都重新初始化一個全新的 AI 服務 (物件)。在這樣的情況下，我們可能會事先將 AI 服務初始化為一個全域變數，讓所有的 Request 都可以透過 Endpoint 來存取同一個全域變數，藉此節省每次都需要重新初始化的時間。

> 然而，這時候所衍伸的問題是: 當所有 Request 同時存取相同的全域變數時，會因為 Race Condition 而造成非預期的結果嗎?

本篇文章以此情境作為出發點，透過多個問題來探討 FastAPI 的運作方式、Multi-Threading 與 Async 的差異以及撰寫出 Thread-Safe 與 Async-Safe Function 的黃金法則。

## FastAPI 如何處理同步 (def) 與非同步 (async def) Endpoint?

首先我們需要先理解我們所定義的 Endpoint，有沒有加上 `async` 對於 FastAPI 的影響。FastAPI (基於 Starlette) 內部有一個非常聰明的機制來處理請求：

- `async def` Endpoint：如果將 Endpoint 定義為 `async def`，那麼這個 Endpoint 就是一個 Asynchronous Endpoint，FastAPI 會在主事件迴圈 (Main Event Loop) 中直接執行它。這意味著多個請求會以 Cooperative Multitasking 的方式，在**同一個**執行緒中交錯執行
- `def` Endpoint：如果將 Endpoint 定義為 `def`，那麼這個 Endpoint 就是一個 Synchronous Endpoint。當 FastAPI 直接在主事件迴圈中執行它，將可能會阻塞整個服務 (e.g. 當這個 Endpoint 會進行 I/O Blocking 或是 CPU Intensive 的運算)，使其無法回應其他請求。為了避免這種情況，FastAPI 會將這些同步函式的執行，**委派給一個獨立的 Thread Pool**。
    
    舉例來說，假設我們定義了一個 Synchronous Endpoint `data_retrieval`:
    ```python
    def data_retrieval(...):
        ...
    ```
    當 10 個使用者同時發送請求時，FastAPI 會從 Threading Pool 中取出 10 個 Thread，透過 **Concurrent** 的方式執行 `data_retrieval` 函式。

## Request 之間的共享物件一定會發生 Race Condition 嗎?

假設我們定義了以下的 Endpoint:

```python
from src import Retiever

retriever = Retriever()
def data_retrieval(query: str) -> list[str]:
    results: list[str] = retriever(query)
    return results
```

由於我們是透過 `def` 定義，因此它是一個 Synchronous Function，FastAPI 會透過不同的 Thread 來處理不同的 Request 來執行這個 Function。如果我們在前面加上一個 `async`，它就成了一個 Asynchronous Function，FastAPI 會透過一個 Thread 來交錯處理不同的 Request 來執行這個 Function。

可以發現到，無論是 Synchonous 還是 Asynchronous，不同的 Request 都會存取到相同的全域變數 `retriever`。在 `retriever` 變數被所有 Request 共享的情況下，就一定會發生 Race Condition 嗎?

> 會不會發生 Race Condition 的關鍵在於: **`Retriever` Class 內部是否有 Shared Mutable State?**

### 安全情況: Stateless 或是只有 Read-only State 的 Retriever

如果 `Retriever` Class 的實作如下：

```python
class Retriever:
    def __init__(self):
        # 假設模型或設定在初始化後就不會再改變
        self._model = self._load_heavy_model()
        self._api_key = "SECRET_KEY"

    def _load_heavy_model(self):
        # 進行一些耗時的 I/O 或 CPU 操作來載入模型
        print("Model loaded!")
        return "This is a read-only model"

    def __call__(self, query: str) -> list[str]:
        # 這個方法中使用的都是區域變數 (local variables)
        # 或是唯讀的實例變數 (self._model)
        # 它沒有修改 self 的任何屬性
        results = f"Querying '{query}' using model '{self._model}'"
        print(f"Thread ID: {threading.get_ident()} processing query: {query}")
        return [results]
```

在這個例子中，`__call__` 方法執行的所有操作，要嘛是基於傳入的參數 (`query`)，要嘛是基於初始化後就不再改變的實例變數 (`self._model`)。它沒有修改任何 `self.xxx` 的屬性。因此，就算 100 個執行緒同時呼叫它，它們也只是在讀取共享資料，而不會互相干擾。這種情況是執行緒安全的 (Thread-Safe)，不會有 Race Condition。

### 危險情況: 有 Shared Mutable State 的 Retriever

現在，如果 `Retriever` 內部有這樣的邏輯：

```python
import time
import random
import threading

class Retriever:
    def __init__(self):
        self.cache = {}
        self.request_count = 0

    def __call__(self, query: str) -> list[str]:
        # ----- Race Condition 發生點 -----
        self.request_count += 1
        
        # 檢查快取 (Read)
        if query in self.cache:
            return self.cache[query]

        # 模擬耗時的資料庫或 API 查詢
        time.sleep(random.uniform(0.1, 0.5)) 
        results = [f"Result for {query}"]

        # 寫入快取 (Write)
        self.cache[query] = results
        # ----- Race Condition 發生點 -----
        
        print(f"Thread ID: {threading.get_ident()}, Count: {self.request_count}, Cache size: {len(self.cache)}")
        return results
```

在這個危險的例子中：

1. `self.request_count += 1`: 這是一個典型的 **Read-Modify-Write** 操作，它**不是**一個原子操作 (Atomic Operation)。兩個執行緒可能同時讀取到 `self.request_count` 的值是 5，然後各自加 1，最後都寫回 6。結果計數器就少算了一次。
2. `self.cache`: 兩個執行緒可能同時判斷 `query` 不在快取中，然後都去執行耗時的查詢，最後都嘗試寫入快取。這不僅會造成資源浪費，在更複雜的邏輯下還可能導致資料不一致。

## 如何避免共享物件在不同的 Request 間發生 Race Condition?

### 實作 Stateless Object

這是最乾淨、最推薦的架構。盡量讓 Class 本身 (e.g. `Retriever`) 變得 Stateless。舉以下三個例子:

- 移除快取：將快取邏輯移到專門的外部服務，如 Redis。Redis 本身是原子操作的，可以安全地處理並行存取。
- 移除計數器：將計數或監控邏輯交給專門的監控系統 (如 Prometheus)。
- 依賴注入：如果需要連線物件 (如資料庫連線)，不要在類別中長期持有，而是透過 FastAPI 的依賴注入系統，在每次請求時獲取一個連線。

### 使用 Threading Lock

如果必須在物件內部維護一個可變的狀態，那麼最直接的方法就是使用 Lock 來建立 Critical Section，來把對共享物件的存取的程式碼包在 Critical Section 當中:

```python
import threading

class ThreadSafeRetriever:
    def __init__(self):
        self.cache = {}
        self.request_count = 0
        self._lock = threading.Lock() # 建立一個鎖

    def __call__(self, query: str) -> list[str]:
        # 使用 'with' 陳述式來確保鎖會被自動獲取和釋放
        with self._lock:
            self.request_count += 1
            
            if query in self.cache:
                return self.cache[query]

        # 將耗時操作移出鎖的範圍，避免阻塞其他執行緒太久
        time.sleep(random.uniform(0.1, 0.5)) 
        results = [f"Result for {query}"]

        with self._lock:
            # 再次檢查，可能在我們查詢的期間，已有其他執行緒放入結果
            if query not in self.cache:
                self.cache[query] = results
            
            print(f"Thread ID: {threading.get_ident()}, Count: {self.request_count}, Cache size: {len(self.cache)}")
            return self.cache[query]
```

優點: 直接解決了 Race Condition

缺點:
  - 會降低並行效能，因為一次只有一個執行緒能進入臨界區
  - 如果鎖的範圍太大（例如鎖住了整個 I/O 操作），會使多執行緒失去意義
  - 可能會引入死鎖 (Deadlock) 的風險

### 為每個 Request 初始化新的 Object

也可以利用 `FastAPI` 的依賴注入系統 (Dependency Injection) 來為每一個請求建立一個全新的 `Retriever` 物件:

```python
# 將 retriever 的建立過程變成一個函式 (dependency)
def get_retriever():
    return Retriever()

@app.post("/data_retrieval/")
def data_retrieval(query: str, retriever: Retriever = Depends(get_retriever)) -> list[str]:
    results: list[str] = retriever(query)
    return results
```

優點: 完全隔離，絕對不會有 Race Condition，因為每個請求都有自己的 retriever 物件。

缺點: 效能問題：如果 `Retriever()` 的初始化過程非常耗時（例如需要載入一個幾 GB 的大模型），那麼為每個請求都重新建立一次物件將會是巨大的效能災難。這種方法只適用於物件建立成本極低的情況。

## (Multi-Thread 情況) 不同 Request 同時讀寫共享物件中的區域變數會有 Race Condition?

> **不會，Method 中的 Local Variable (區域變數) 本身絕對不會發生 Race Condition**

我們先假設目前的 Endpoint 是一個透過 `def` 所定義的 Synchronous Function，因此每當 FastAPI Server 接收到新的 Request 時，就會從 Thread Pool 中抓出一個 Thread 來處理這個 Request。

雖然多個 Thread 同時在執行同一份程式碼 (同一個 Method)，但它們的 Local Varaible 在記憶體中是**隔離**的，因此才不會發生 Race Condition。

### Stack Memory 與 Heap Memory

仔細理解背後的原因，我們需要了解到當作業系統把一個 Program 載入到 RAM 中成為一個 Process 時，這個 Process 的記憶體包含了 Stack 與 Heap 兩種記憶體:

- Stack
  - 特性：每個 Thread 在被作業系統建立時，都會被分配一塊自己專屬、獨立的記憶體空間，這就是該執行緒的 Stack
  - 用途：當一個函式或方法被呼叫時，會在該 Thread 的 Stack 上建立一個 **Stack Frame**。這個 Stack Frame 用來儲存所有屬於這個函式呼叫的資訊，包括：
    - Function Parameters
    - Function Local Variables
    - Return Address (函式執行完後要跳回哪裡)
    - Life Cycle：當函式執行完畢時，這個 Stack Frame 會被自動銷毀，其中的所有區域變數也隨之消失
- Heap
  - 特性：這是一塊由 Process 內的所有 Thread 共享的記憶體區域
  - 用途：用來儲存生命週期更長、需要被共享的資料。這包括：
    - Class Attributes
    - Global Variables

### 實際範例

我們來看看以下的例子。假設我們定義了以下的 Endpoint:

```python
from src import Retiever

retriever = Retriever()
def data_retrieval(query: str) -> list[str]:
    results: list[str] = retriever(query)
    return results
```

`retriever` Object 本身是一個 Global Variable`，因此會被存在 Heap Memory 中。而 `Retriever` Class 的實作如下:

```python
class Retriever:
    def __init__(self):
        # `self` (retriever 物件本身) 存在於 Heap 中 (共享)
        # `self._model` 這個屬性也跟著物件存在於 Heap 中 (共享)
        self._model = self._load_model() 

    def __call__(self, query: str) -> list[str]:
        # 當一個 Thread 呼叫這個方法時，
        # 會在 "它自己的 Stack" 上建立一個新的 Stack Frame

        # 1. `query` 參數存在於該 Thread 自己的 Stack 上
        
        # 2. `process_log` 是一個 Local Variable，也存在於該 Thread 自己的 Stack 上
        process_log = f"Processing query: {query}" 

        # 3. `results` 也是一個 Local Variable，同樣存在於該 Thread 自己的 Stack 上
        #    它讀取了共享的 self._model，但這是一個 Read-Only 操作，所以是安全的
        results = [f"Result for {query} using {self._model}"]
        
        return results # 方法返回，這個 Stack Frame 被銷毀
```

基於上述的程式碼，我們來模擬一個情境:

假設有兩個 Request 同時進來，FastAPI Server 指派了 Thread A 和 Thread B 來處理：

- Thread A 呼叫 `retriever(query="貓")`:
  - 在 Thread A 的 Stask 上建立一個 Stack Frame
  - 這個 Frame 裡面有 `query = "貓"`，`process_log = "Processing query: 貓"` 等變數。
- Thread B 同時呼叫 `retriever(query="狗")`:
  - 在 Thread B 的 Stack 上建立一個完全獨立的 Stack Frame
  - 這個 Frame 裡面有 `query = "狗"`，`process_log = "Processing query: 狗"` 等變數。

關鍵點：Thread A 完全無法存取 Thread B Stack 上的任何資料，反之亦然。它們各自操作自己的區域變數，就像在兩個完全隔離的房間裡工作一樣。雖然它們都讀取了位於共享 Heap 上的 `self._model`，但只要這個操作是 Read-Only 的，就不會產生任何衝突。

## (Single Thread 情況) 不同 Request 同時讀寫共享物件中的區域變數會有 Race Condition?

接著，讓我們來討論 Single Thread 的情況下: 假設目前的 Endpoint 是一個透過 `async def` 所定義的 Asynchronous Function，因此每當 FastAPI Server 接收到新的 Request 時，都是由同一個 Thread 在處理不同的 Request，那在這樣的情況下會發生 Race Condition 嗎?

> 不會，在 Async 的情況下，不同 Request 的區域變數依然不會發生 Race Condition

現在，讓我們更深入的來探討 `async/await` 底層的運作，理解單一 Thread (單一 Stack) 不會導致變數混亂而發生 Race Condition。

### Async 的核心：Coroutine 不是函式，而是物件

當我們呼叫一個 `def` 函式時，它會立即執行，並在 Stack 上建立一個 Stack Frame。

然而，當我們呼叫一個 `async def` 函式時，**它不會立即執行**。相反地，它會回傳一個 **Coroutine Object**。

這個 Coroutine Object，本質上是一個**Stateful Generator**。可以把它想像成一個「可暫停的函式」，它打包了執行該函式所需的一切資訊：
- 要執行的程式碼
- 它所有的 Local Variables
- 它執行到哪一行的指標 (Instruction Pointer)

這些 Coroutine Object 本身是存放在 **Heap** 記憶體中的，也就是所有 Thread 共享的那個區域。

### Event Loop 的角色：可以 Concurrently 下很多盤棋的棋藝大師

想像一下 Event Loop 是位棋藝大師，而每一個進來的 Request 都會產生一個 Coroutine Object，就像是一盤新的棋局。

1.  **Request A 進來**:
    *   FastAPI 呼叫 `async def` Endpoint，產生了 `Coroutine_A` 物件
    *   FastAPI 將 `Coroutine_A` 交給 Event Loop 說：「請執行這個任務」
    *   Event Loop (棋藝大師) 走到棋盤 A 前面，開始執行 `Coroutine_A`
    *   它將 `Coroutine_A` 的初始狀態（參數、區域變數）載入到**唯一的 Thread 的 Stack** 上，開始「下棋」

2.  **遇到 `await`**:
    *   `Coroutine_A` 的程式碼執行到 `await some_io_operation()`
    *   這就像棋藝大師下了一步棋後，發現需要等待對手思考（等待資料庫回應）
    *   `await` 的語意是：「**暫停我目前的執行，並將控制權交還給 Event Loop**」
    *   在暫停前，`Coroutine_A` 會將它**所有的當前狀態**（包括它所有區域變數的值、它停在哪一行）**完整地儲存回它自己的物件中** (那個在 Heap 裡的 `Coroutine_A` 物件)
    *   然後，它會從 Thread Stack 中被**移除**。此刻，Stack 又變得相對乾淨了

3.  **切換到 Request B**:
    *   此時，Request B 可能已經進來，產生了 `Coroutine_B` 物件
    *   Event Loop (棋藝大師) 發現棋盤 A 沒事做，就走到棋盤 B 前面。(這也就說明了棋藝大師是 **Concurrently** 而非 Parallely 的在多個棋盤之間下棋)
    *   它將 `Coroutine_B` 的狀態載入到**同一個 Thread Stack** 上，開始為 Request B 服務

4.  **I/O 操作完成**:
    *   過了一會兒，`some_io_operation()` 完成了（資料庫傳回了結果）。
    *   Event Loop 收到通知：「棋盤 A 的對手下完棋了！」。
    *   在下一個適當的時機 (例如 `Coroutine_B` 也遇到了 `await` 或執行完畢)，Event Loop 會再次回到棋盤 A。
    *   它會從 `Coroutine_A` 物件中，**將先前儲存的所有狀態（包括所有區域變數）完美地還原到 Thread Stack 上**，然後從 `await` 的下一行繼續執行。

所以，回答我們最核心的問題：

**原本 Stack 中的內容怎麼辦？**

在 `await` 發生時，當前 Coroutine 的狀態會被完整地「序列化」並儲存回它在 Heap 上的物件裡，然後它的 Stack Frame 會被**清出 (Popped)**出 Stack。Stack 接著就可以被下一個 Coroutine 安全地使用。

**這樣不同的 Request 的區域變數都會存在同一個 Stack 中, 而發生 Race Condition 嗎？**

不會。因為在任何一個時間點，**Stack 上只會有當前正在執行的那一個 Coroutine 的資料**。不同 Coroutine 的資料是透過在 Heap 上的物件進行隔離儲存的，它們永遠不會同時出現在堆疊上，因此不可能發生衝突或 Race Condition。

## 什麼情況下 Async 比 Multi-Thrading 更有效率?

>  在 I/O 密集型 (I/O-Bound) 的應用中，Async 的運作模式能以更低的成本實現更高的資源利用率

這是一個直擊要害的問題，也是非同步程式設計之所以如此流行的根本原因。您經常聽到 Async 比 Multi-threading 更有效率，是因為在**特定且非常常見**的場景下——也就是 **I/O 密集型 (I/O-Bound)** 的應用中——Async 的運作模式能以更低的成本實現更高的資源利用率。

效率的提升主要來自以下幾個關鍵因素：

### 上下文切換 (Context Switch) 的成本天差地遠

這是最核心、最重要的原因。

*   **Multi-threading 的上下文切換 (昂貴)**
    *   **由作業系統 (OS) 核心強制執行**：當作業系統決定要暫停一個 Thread，改為執行另一個 Thread 時，它需要介入
    *   **重量級操作**：這個過程需要儲存當前 Thread **所有**的 CPU 狀態，包括 CPU Register、Program Counter、Stask Pointer 等。然後，載入下一個 Thread 的完整狀態。這是一個牽涉到作業系統 Kernel Mode 與 User Mode 的切換，以電腦的尺度來看，是**非常耗時**的操作 (通常是微秒級，但累積起來非常可觀)
    *   **搶佔式 (Preemptive)**：作業系統會強制剝奪 Thread 的執行權，不管它自己願不願意，這可能發生在任何時間點

*   **Async 的上下文切換 (極度便宜)**
    *   **由應用程式的 Event Loop 執行**：切換完全發生在應用程式的 User Space，作業系統根本不知道也不關心這些 Coroutine 的存在
    *   **輕量級操作**：切換只在 `await` 關鍵字處發生。Event Loop 所做的僅僅是：保存當前 Coroutine 的狀態 (幾個變數和一個指標)，然後從 Queue 中取出下一個就緒的 Coroutine 來執行。這幾乎和**一次函式呼叫**一樣快 (奈秒級)
    *   **協作式 (Cooperative)**：切換只發生在程式設計師明確寫下 `await` 的地方，是 Coroutine「主動讓出」執行權

**結論**：處理 10,000 個並行請求，Multi-threading 可能需要作業系統進行數萬次昂貴的上下文切換；而 Async 只需要 Event Loop 進行數萬次極其廉價的內部狀態切換。

### 記憶體開銷 (Memory Overhead)

*   **Multi-threading**：每建立一個 Thread，作業系統都需要為其分配一塊**完整的 Thread Stack**。這個 Stack 的預設大小通常不小 (例如在 Linux 上可能是 8MB)。如果你要建立 1,000 個執行緒來處理 1,000 個並行請求，光是堆疊就會佔用 `1000 * 8MB = 8GB` 的記憶體！這使得系統無法擴展到非常高的並行數量

*   **Async**：只有一個 Thread，所以只有一個 Stack。所有的 Coroutine Object 雖然也佔用記憶體 (在 Heap 中)，但每個 Coroutine Object 的大小遠遠小於一個完整的 Thread Stack (通常只有幾 KB)。因此，用幾個 GB 的記憶體，你可以輕鬆地維持數萬甚至數十萬個處於「等待 I/O」狀態的 Coroutine。

這個差異是 Async 能夠輕鬆解決著名的 **C10k 問題** (單機同時處理一萬個連線) 的關鍵。

### Python 的全域直譯器鎖 (Global Interpreter Lock, GIL)

這一點在 Python 的世界中尤其重要。

*   CPython 直譯器中的 GIL 是一把大鎖，它確保了在任何時刻，**只有一個 Thread 能執行 Python 的位元組碼 (Bytecode)**
*   這意味著，即使在一個 8 核心的 CPU 上，一個 Python 程式的多個 Thread 也**無法真正地並行 (Parallel) 執行 CPU 密集型**的計算。它們實際上是在同一個 CPU 核心上快速輪流執行，看起來像並行，但總的計算量沒有增加
*   **但是，當一個 Thread 在等待 I/O (如網路、磁碟讀寫) 時，它會釋放 GIL**。這就是為什麼 Multi-threading 在 Python 中對 I/O-Bound 任務仍然有效的原因。
*   然而，既然 GIL 限制了真正的 CPU 並行，而 Async 又能在單一 Thread 上用更低的成本處理 I/O-Bound 任務，那麼在大多數 Web 服務場景下，Async 的模型就顯得更具吸引力。

### Multi-Threading 與 Async 比較

| 特性 | Multi-Threading (`def` 端點) | Async (`async def` 端點) |
| :--- | :--- | :--- |
| **執行單位** | Thread (執行緒) | Coroutine (協程/任務) |
| **排程者** | 作業系統 (OS) | Event Loop (應用程式層級) |
| **切換方式** | Preemptive (搶佔式，OS 強制切換) | Cooperative (協作式，`await` 主動讓出) |
| **Stack 管理** | **每個執行緒有各自獨立的 OS Stack**。 | **所有協程共享同一個 Thread 的 Stack**。 |
| **狀態儲存** | 狀態永遠存在於各自的 Stack 中。 | 當協程**暫停 (`await`)**時，其狀態 (包含區域變數) 會被打包儲存回**Heap 上的協程物件**中。 |
| **記憶體開銷** | 大 | 小 |
| **上下為切換成本** | 大 | 小 |

## Thread-Safe 與 Async-Safe 是等價的嗎?

這是一個極其重要的問題，也是許多同時使用同步和非同步程式碼的開發者會遇到的陷阱

> **不，Thread-Safe 和 Async-Safe 絕對不等價**

更重要的是，一個典型的 Thread-Safe 實作，如果直接用在 Async 的環境中，**不僅不是安全的，反而會造成 Deadlock**。

### Thread-Safe 與 Async-Safe 的敵人是誰?

首先，先讓我們理解 Thread-Safe 與 Async-Safe 的意義。我們透過反向的方式來思考，理解他們的敵人是誰，什麼情況下會造成 "Thread-Unsafe" 與 "Async-Unsafe":

*   **Thread-Safe**
    *   **敵人**：**Parallel Execution / Preemptive Multitasking**
    *   **原因**：當多個 Thread 由作業系統進行 Schedule 時，一個 Thread 在 CPU 上執行到一半時，可能在任何時間點、任何指令之間被打斷並切換為另外一個 Thread。此時，就有可能發生多個 Thread 對同一塊記憶體空間**同時讀寫**而發生 Race Condition
    *   **武器**：**Blocking Locks**，例如 `threading.Lock`

*   **Async-Safe**
    *   **敵人**：**Blocking the Event Loop**
    *   **原因**：在 Async 世界裡，只有一個 Thread。如果任何一段程式碼佔用 CPU 不放，或者進行了 Blocking I/O 操作，整個 Event Loop 就會被卡住，所有其他的並行任務都將停滯
    *   **武器**：**Non-blocking Operations** 和**Cooperative Yielding**，例如 `asyncio.Lock` 和 `await`

### `threading.Lock` vs. `asyncio.Lock` 的運作機制

這兩種 Lock 在行為上是天差地遠的:

*   **`threading.Lock.acquire()` 的行為**
    *   當一個執行緒呼叫 `acquire()` 時，如果 Lock 是可用的，它會立即獲得 Lock 並繼續執行
    *   如果 Lock 已經被其他 Thread 持有，**它會讓當前的 Thread 進入「睡眠」或「阻塞」狀態**。作業系統會將這個 Thread 掛起，直到 Lock 被釋放。它會**徹底交出 CPU 的控制權**。

*   **`await asyncio.Lock.acquire()` 的行為**
    *   當一個 Coroutine `await` 一個 `acquire()` 時，如果 Lock 是可用的，它會立即獲得鎖並繼續執行
    *   如果 Lock 已經被其他 Coroutine 持有，**它不會阻塞 Thread**。相反地，它會：
        1.  將自己註冊為在等待這個 Lock
        2.  **主動將控制權交還給 Event Loop**。
    *   Event Loop 在收到控制權後，會去執行其他已經就緒的 Coroutine

### Deadlock: 在 Async 程式碼中加入 `threading.Lock`

現在，讓我們把一個用 `threading.Lock` 實現的 Thread-Safe 物件放到 `async def` Endpoint 中，看看會發生什麼!

```python
import threading
import asyncio
import time

class DangerousRetriever:
    def __init__(self):
        # 這是為 Multi-Thread 設計的 Lock
        self._lock = threading.Lock()
        self.cache = {}

    # 假設我們為 async Endpoint 提供一個 async 方法
    async def process_query_async(self, query: str):
        print(f"Coroutine {query}: 準備獲取 threading.Lock")
        
        # 這裡是災難的開始！
        # acquire() 是一個阻塞呼叫，它會凍結整個 Thread！
        with self._lock:
            print(f"Coroutine {query}: 成功獲取 threading.Lock")
            
            if query in self.cache:
                return self.cache[query]

            # 模擬一個需要 await 的非同步 I/O 操作
            # 例如：await db.fetch(query)
            print(f"Coroutine {query}: 準備進行 await，但仍持有 lock")
            await asyncio.sleep(1) # <<--- 在持有 threading.Lock 的情況下 await
            
            result = f"Result for {query}"
            self.cache[query] = result
            print(f"Coroutine {query}: 釋放 threading.Lock")
            return result
```

**執行流程分析：**

1.  **Coroutine A** (`process_query_async("A")`) 開始執行
2.  它成功獲取了 `self._lock` (一個 `threading.Lock`)
3.  它執行到 `await asyncio.sleep(1)`。`await` 的語意是「暫停我，把控制權交還給 Event Loop」
4.  **Event Loop**收回控制權，發現**Coroutine B** (`process_query_async("B")`) 已經就緒，於是開始執行 Coroutine B
5.  Coroutine B 執行到 `with self._lock:`，它嘗試獲取同一個 `threading.Lock`
6.  因為 Coroutine A 仍然持有這個鎖，所以 Coroutine B 的 `acquire()` 呼叫**阻塞了**
7.  **關鍵點**：`threading.Lock` 的阻塞是**作業系統層級的執行緒阻塞**。它凍結了 Event Loop 所在的**唯一執行緒**。
8.  現在，整個應用程式被凍結了。事件迴圈無法再排程任何任務。它無法喚醒 `asyncio.sleep(1)` 結束後的 Coroutine A。
9.  Coroutine A 永遠無法執行到釋放 Lock 的那一行，因為 Event Loop 已經被 Coroutine B 阻塞了。Coroutine B 永遠無法獲得鎖，因為 Coroutine A 永遠無法釋放它。
10. **Deadlock**

### 最佳實踐

*   **隔離原則**：`threading` 模組中的同步原語（Lock, Event, Semaphore 等）是為 Multi-Thread 環境設計的；`asyncio` 模組中的同步原語是為 Single-Thread 的協程環境設計的。**絕對不要混用它們**。

總之，請務必記住：**Thread-Safe ≠ Async-Safe**。為非同步程式碼選擇非同步的工具，為同步程式碼選擇同步的工具，這是確保應用程式穩定運行的黃金法則。

## 讓一個 Function/Method 是 Thread-Safe 且 Async-Safe 的黃金守則?

> 要寫出同時 Thread-Safe 和 Async-Safe 的程式碼，你的心態應該從「我該用哪個鎖?」轉變為「**我如何才能完全避免用鎖?**」。答案幾乎總是：**消除 Shared Mutable State**。遵循這個核心原則，程式碼將會變得更簡單、更能適應各種並行模型

以下是實現這種 Universally Safe 程式碼的設計規範，按重要性排序：

#### 規範 1：追求純函式與無狀態 (Statelessness) - 黃金法則

這是最重要、最有效的一條。如果一個函式或方法沒有狀態，或者說它的輸出完全由其輸入決定，那麼它就沒有任何需要保護的東西。

*   **怎麼做**：
    *   函式不應讀取或寫入任何全域變數或其類別的實例屬性 (`self.xxx`)
    *   所有需要的資料都應該透過函式參數明確傳入
    *   函式不應有 Side Effects，例如修改傳入的物件（除非是返回一個新的物件）

*   **範例**：
    ```python
    # 通用安全的函式
    def process_data(data: dict, config: dict) -> dict:
        # 只依賴傳入的參數
        # 所有變數都是區域變數
        result = {}
        result['processed_key'] = data.get('key', '') + config.get('suffix', '')
        # 返回一個全新的物件，而不是修改原始的 data
        return result
    ```
    這個函式無論被 100 個 Thread 還是 100 個 Coroutine 同時呼叫，永遠都是安全的。

#### 規範 2：使用不可變狀態 (Immutability)

如果必須要有狀態，那就讓它成為不可變的。一旦建立，就不能修改。

*   **怎麼做**：
    *   使用元組 (`tuple`) 而不是列表 (`list`)
    *   使用 `frozenset` 而不是 `set`
    *   使用 `dataclasses` 並設定 `frozen=True`
    *   如果需要「修改」，那就建立一個新的物件而不是在原地修改。

*   **範例**：
    ```python
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class AppConfig:
        api_key: str
        timeout: int

    class Retriever:
        def __init__(self, config: AppConfig):
            # self._config 是一個不可變物件的參考
            # 雖然可以讓 self._config 指向另一個物件，但 AppConfig 本身是安全的
            self._config = config

        def get_timeout(self):
            # 唯讀操作，永遠是安全的
            return self._config.timeout
    ```

#### 規範 3：將狀態管理外部化 (Externalize State Management)

這是架構層面的關鍵。不要在你的應用程式記憶體中自己管理複雜的共享狀態，而是將這個責任交給專門為並行而設計的外部服務。

*   **怎麼做**：
    *   **快取 (Caching)**：不要用 `self.cache = {}`，改用 **Redis**。Redis 的操作（如 `SET`, `GET`）是原子性的，天生就是為高並行場景設計的。
    *   **任務佇列 (Task Queues)**：不要用 `self.tasks = []`，改用 **RabbitMQ** 或 **Celery**。
    *   **資料儲存 (Data Storage)**：使用資料庫，並依賴其提供的**交易 (Transactions)** 和**行級鎖 (Row-level Locking)** 來保證資料一致性。

*   **範例**：
    ```python
    import redis

    # 假設 r 是一個 Redis 連線物件
    r = redis.Redis(...)

    # 這個函式本身是無狀態的，它將狀態管理委託給了 Redis
    def get_data_with_cache(key: str):
        # GET 是原子操作，安全
        cached_result = r.get(key)
        if cached_result:
            return cached_result
        
        result = "expensive_db_call()"
        # SETEX (SET with Expiry) 也是原子操作，安全
        r.setex(key, 60, result) 
        return result
    ```

## 同一個類別被載入到不同的文件中並初始化為相同的全域變數

在前面的例子中, 我們聚焦在多個 Request 共用一個全域變數的情況:

```python
from src import Retiever

retriever = Retriever()
def data_retrieval(query: str) -> list[str]:
    results: list[str] = retriever(query)
    return results
```

現在，讓我們來思考以下情境: 多個 Python 文件共用一個類別並初始化出相同的全域變數:

```python {title="endpoint_a.py"}
from src import Retriever

retriever = Retriever()

def A(query):
    a = retriever(query)
    return a
```

```python {title="endpoint_b.py"}
from src import Retriever

retriever = Retriever()

def B(query):
    b = retriever(query)
    return b
```

當兩個 Request 同時分別的執行 (不管透過 Multi-Threading 或 Async) Endpoint A 與 B 此時會發生什麼事情嗎?

> 完全不會! 兩個 `retriever` Object 實際上是**完全獨立**的。一個在 `endpoint_a` 模組的全域範圍中，另一個在 `endpoint_b` 模組的全域範圍中。因此，對 A 的請求和對 B 的請求會使用**不同**的物件，它們之間的實例屬性 (`self.xxx`) 是**完全隔離**的。

### Python 的模組匯入與快取機制

要理解這個行為，關鍵其實不在 FastAPI，而在於 Python 本身的 `import` 的運作原理。

1.  **模組只會被執行一次**：
    當 FastAPI Server 啟動時 (e.g. `uvicorn main:app`)，它會開始匯入程式碼。Python 會維護著一個名為 `sys.modules` 的 Global Dictionary，它扮演著模組的快取角色。
    *   當第一次遇到 `import src` 或 `from src import Retriever` 時，Python 會：
        a. 檢查 `sys.modules` 中是否已經有 `'src'`
        b. 如果沒有，它會找到 `src.py` 檔案，**執行裡面的所有程式碼**，然後將建立的模組物件存入 `sys.modules['src']`
    *   當之後在另一個檔案中再次遇到 `import src` 或 `from src import Retriever` 時，Python 會發現 `'src'` 已經在 `sys.modules` 中了，於是它會**直接從快取中取出該模組物件**，而**不會**再次執行 `src.py` 檔案

2.  **情境分析**：
    假設我們的主應用程式 (`main.py`) 會匯入 `endpoint_a` 和 `endpoint_b`。

    *   **啟動流程 (簡化版)**：
        1.  Uvicorn 啟動，匯入您的主應用程式檔案
        2.  主應用程式 `import endpoint_a`
        3.  Python 開始執行 `endpoint_a.py` 的程式碼
        4.  遇到 `from src import Retriever`。因為是第一次，Python 執行 `src.py` 並快取 `src` 模組。`Retriever` 類別被載入記憶體
        5.  遇到 `retriever = Retriever()`。這行程式碼**被執行**，一個 `Retriever` 的**實例**被建立（我們稱之為 `instance_A`），並賦值給 `endpoint_a` 模組內的全域變數 `retriever`。
        6.  主應用程式接著 `import endpoint_b`。
        7.  Python 開始執行 `endpoint_b.py` 的程式碼。
        8.  遇到 `from src import Retriever`。這次 Python 在 `sys.modules` 中找到了 `src` 模組，直接從快取中取出 `Retriever` 類別。`src.py` **不會**再次執行。
        9.  遇到 `retriever = Retriever()`。這行程式碼**也被執行**，它呼叫了同一個 `Retriever` 類別的建構函式，建立了**一個全新的、獨立的 `Retriever` 實例**（我們稱之為 `instance_B`），並賦值給 `endpoint_b` 模組內的全域變數 `retriever`。

由此我們可以知道，如果現在同時有 2 個 Request:
- 一個發送到 `/A` 的請求，會使用 `retriever` 全域變數 (基於 `instance_A`)
- 一個發送到 `/B` 的請求，會使用 `retriever` 全域變數 (基於 `instance_B`)

因為它們是兩個**不同的**物件實例，所以它們各自的實例屬性 (`self.xxx`) 是完全隔離的。如果 `instance_A` 內部有一個計數器 `self.count`，它的改變完全不會影響到 `instance_B` 的 `self.count`。

我們之前討論的 Race Condition 問題依然存在，只是被侷限在了各自的 Endpoint 內:
*   多個**同時對 A 的 Request**，將會共享 `instance_A`，可能在 `instance_A` 內部產生 Race Condition
*   多個**同時對 B 的 Request**，將會共享 `instance_B`，可能在 `instance_B` 內部產生 Race Condition
*   但是，A 的 Request 和 B 的 Request 之間**不會**因為 `retriever` 物件而互相干擾

### 危險情況: 類別中定義了類別屬性 (Class Attributes)

雖然兩個實例是分開的，但它們是由**同一個類別**建立的。如果在 `Retriever` 類別中定義了**類別屬性**，那麼這個屬性將會被 `instance_A` 和 `instance_B` **共享**！

```python
# src.py
class Retriever:
    # 這是一個類別屬性，所有實例共享
    total_requests_processed = 0 

    def __init__(self):
        # 這是一個實例屬性，每個實例獨有
        self.instance_name = "instance_" + str(id(self))

    def __call__(self, query: str):
        Retriever.total_requests_processed += 1 # 修改共享的類別屬性！
        print(f"Processing in {self.instance_name}. Total processed: {Retriever.total_requests_processed}")
        return [query]
```
在這個例子中，不管是對 A 還是對 B 的 Request，都會修改**同一個** `Retriever.total_requests_processed` 變數，這將會導致跨端點的 Race Condition。

### 最佳實作方式

上述的架構模式（在每個 Endpoint 檔案中都自行初始化相同類別）雖然在技術上可行，但通常被認為是不良實踐，原因如下：

1.  **違反 DRY (Don't Repeat Yourself)**：在多個地方重複了物件的建立邏輯
2.  **資源浪費**：如果 `Retriever()` 的初始化是一個昂貴的操作（例如載入大模型），您現在等於是載入了兩次，佔用了雙倍的記憶體和啟動時間
3.  **狀態不一致**：可能期望 `retriever` 是一個全域單例 (Singleton)，但實際上卻建立了多個實例，這可能導致非預期的行為

#### 集中化依賴管理

更清晰、更健壯的做法是只建立一個共享的實例，然後讓所有需要它的地方都使用這一個實例。

```python
# src/dependencies.py

from .retriever_class import Retriever

# 在這裡建立唯一的、共享的實例
# 整個應用程式的生命週期中只會有這一個 retriever 物件
retriever = Retriever() 
```

```python
# endpoint_a.py
from srcencies import retriever # 直接匯入實例！

def A(query):
    a = retriever(query)
    return a.depend
```

```python
# endpoint_b.py
from src.dependencies import retriever # 匯入同一個實例！

def B(query):
    b = retriever(query)
    return b
```

這樣一來，所有 Request，無論是到 A 還是 B，都會共享 `dependencies.py` 中建立的**唯一實例**。這不僅節省了資源，也讓狀態管理變得清晰可控。

## 結語

在本篇文章中，我們從「多個 Request 同時存取 FastAPI Server 上的同一個全域變數」的情境出發，探討了 FastAPI 在 Synchronous (Multi-Thread) 與 Asynchronous (Async) 的運作方式、Race Condition 發生的情境以及避免 Race Condition 的黃金守則。在本文最後，我們還介紹到 Python 對於 Module 的快取與管理方式。
