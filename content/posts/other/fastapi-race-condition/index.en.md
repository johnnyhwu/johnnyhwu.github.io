---
# weight: 1
title: "The Concurrency Trap in FastAPI: From Race Conditions to Deadlocks with Global Variables"
date: 2025-08-31
lastmod: 2025-09-04
draft: False
description: "Avoid race conditions in FastAPI. This guide explains how FastAPI handles multi-threading vs. async, why thread-safe code isn't always async-safe, and the golden rules for writing robust, concurrent Python applications by eliminating shared mutable state."
featuredImage: "featured-image.jpg"

tags: ["Operating System", "Python Tip"]
categories: ["other"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true
license: '<a rel="license external nofollow noopener noreffer" href="https://creativecommons.org/licenses/by-nc/4.0/" target="_blank">CC BY-NC 4.0</a>'

url: "other/:contentbasename"
---

<!--more-->

## Introduction

When developing a Proof of Concept (PoC) for an AI service, we often use [FastAPI](https://fastapi.tiangolo.com/) to build a server. This allows the client-side to access the AI service through various endpoints for convenient testing.

Sometimes, the initialization of the AI service (instantiating the service object from its abstract class) can be time-consuming. This makes it impractical to re-initialize a new AI service for every single request. In such cases, we might pre-initialize the AI service as a global variable, allowing all requests to access the same instance through their endpoints, thereby saving initialization time.

> However, a problem arises from this approach: When all requests access the same global variable simultaneously, could it lead to unexpected results due to a Race Condition?

This article uses this scenario as a starting point to explore several key questions: how FastAPI works, the differences between Multi-Threading and Async, and the golden rules for writing Thread-Safe and Async-Safe functions.

## How Does FastAPI Handle Synchronous (def) vs. Asynchronous (async def) Endpoints?

First, we need to understand the impact of adding `async` to our endpoint definitions in FastAPI. FastAPI (which is built on Starlette) has a very clever internal mechanism for handling requests:

- **`async def` Endpoints**: If you define an endpoint with `async def`, it's an Asynchronous Endpoint. FastAPI will run it directly within the Main Event Loop. This means multiple requests will be executed concurrently in a **single** thread using Cooperative Multitasking.
- **`def` Endpoints**: If you define an endpoint with `def`, it's a Synchronous Endpoint. If FastAPI were to run this directly in the main event loop, it could block the entire service (e.g., if the endpoint performs I/O blocking or CPU-intensive computations), preventing it from responding to other requests. To avoid this, FastAPI **delegates the execution of these synchronous functions to a separate Thread Pool**.

For example, let's say we define a synchronous endpoint `data_retrieval`:
```python
def data_retrieval(...):
    ...
```
If 10 users send requests simultaneously, FastAPI will take 10 threads from its thread pool and execute the `data_retrieval` function **concurrently**.

## Do Shared Objects Between Requests Always Cause Race Conditions?

Suppose we have the following endpoint:

```python
from src import Retriever

retriever = Retriever()
def data_retrieval(query: str) -> list[str]:
    results: list[str] = retriever(query)
    return results
```

Since we defined this with `def`, it's a synchronous function, and FastAPI will use different threads to handle different requests. If we added `async` to it, it would become an asynchronous function, and FastAPI would use a single thread to handle different requests concurrently.

You can see that regardless of whether it's synchronous or asynchronous, different requests will access the same global variable `retriever`. Does sharing the `retriever` variable across all requests guarantee a race condition?

> The key to whether a race condition occurs is: **Does the `Retriever` class have a Shared Mutable State?**

### Safe Case: Stateless or Read-only State Retriever

If the `Retriever` class is implemented as follows:

```python
class Retriever:
    def __init__(self):
        # Assume the model or settings don't change after initialization
        self._model = self._load_heavy_model()
        self._api_key = "SECRET_KEY"

    def _load_heavy_model(self):
        # Simulates a time-consuming I/O or CPU operation to load the model
        print("Model loaded!")
        return "This is a read-only model"

    def __call__(self, query: str) -> list[str]:
        # This method only uses local variables
        # or read-only instance variables (self._model).
        # It does not modify any attributes of self.
        results = f"Querying '{query}' using model '{self._model}'"
        print(f"Thread ID: {threading.get_ident()} processing query: {query}")
        return [results]
```

In this example, all operations within the `__call__` method are based either on the input parameters (`query`) or on instance variables (`self._model`) that do not change after initialization. It doesn't modify any `self.xxx` attributes. Therefore, even if 100 threads call it simultaneously, they are only reading shared data and will not interfere with each other. This situation is thread-safe, and no race condition will occur.

### Dangerous Case: Retriever with Shared Mutable State

Now, consider if the `Retriever` has logic like this:

```python
import time
import random
import threading

class Retriever:
    def __init__(self):
        self.cache = {}
        self.request_count = 0

    def __call__(self, query: str) -> list[str]:
        # ----- Race Condition Hotspot -----
        self.request_count += 1
        
        # Check cache (Read)
        if query in self.cache:
            return self.cache[query]

        # Simulate a time-consuming database or API query
        time.sleep(random.uniform(0.1, 0.5)) 
        results = [f"Result for {query}"]

        # Write to cache (Write)
        self.cache[query] = results
        # ----- Race Condition Hotspot -----
        
        print(f"Thread ID: {threading.get_ident()}, Count: {self.request_count}, Cache size: {len(self.cache)}")
        return results
```

In this dangerous example:

1.  `self.request_count += 1`: This is a classic **Read-Modify-Write** operation, which is **not** an atomic operation. Two threads might simultaneously read the value of `self.request_count` as 5, each adds 1, and both write back 6. The counter ends up missing an increment.
2.  `self.cache`: Two threads might simultaneously find that `query` is not in the cache, both proceed to execute the time-consuming query, and both then attempt to write to the cache. This not only wastes resources but can also lead to data inconsistency in more complex scenarios.

## How to Prevent Race Conditions with Shared Objects Between Requests?

### Implement Stateless Objects

This is the cleanest and most recommended architecture. Strive to make your classes (e.g., `Retriever`) stateless. Here are three examples:

-   **Remove the Cache**: Move the caching logic to a dedicated external service like Redis. Redis itself provides atomic operations and can safely handle concurrent access.
-   **Remove the Counter**: Delegate counting or monitoring logic to a dedicated monitoring system (like Prometheus).
-   **Dependency Injection**: If you need connection objects (like database connections), don't hold them long-term within the class. Instead, use FastAPI's dependency injection system to acquire a connection for each request.

### Use a Threading Lock

If you must maintain a mutable state within the object, the most direct method is to use a Lock to create a Critical Section, wrapping the code that accesses the shared object.

```python
import threading

class ThreadSafeRetriever:
    def __init__(self):
        self.cache = {}
        self.request_count = 0
        self._lock = threading.Lock() # Create a lock

    def __call__(self, query: str) -> list[str]:
        # Use a 'with' statement to ensure the lock is automatically acquired and released
        with self._lock:
            self.request_count += 1
            
            if query in self.cache:
                return self.cache[query]

        # Move the time-consuming operation outside the lock to avoid blocking other threads for too long
        time.sleep(random.uniform(0.1, 0.5)) 
        results = [f"Result for {query}"]

        with self._lock:
            # Check again, as another thread might have inserted the result while we were querying
            if query not in self.cache:
                self.cache[query] = results
            
            print(f"Thread ID: {threading.get_ident()}, Count: {self.request_count}, Cache size: {len(self.cache)}")
            return self.cache[query]
```

**Pros**: Directly solves the race condition.

**Cons**:
-   Reduces concurrency performance, as only one thread can enter the critical section at a time.
-   If the lock scope is too large (e.g., locking the entire I/O operation), it negates the benefits of multi-threading.
-   Can introduce the risk of Deadlocks.

### Initialize a New Object for Each Request

You can also leverage FastAPI's Dependency Injection system to create a brand new `Retriever` object for every request:

```python
# Turn the retriever creation process into a function (a dependency)
def get_retriever():
    return Retriever()

@app.post("/data_retrieval/")
def data_retrieval(query: str, retriever: Retriever = Depends(get_retriever)) -> list[str]:
    results: list[str] = retriever(query)
    return results
```

**Pros**: Complete isolation. Absolutely no chance of race conditions because each request has its own `retriever` object.

**Cons**: Performance issues. If the `Retriever()` initialization process is very time-consuming (e.g., loading a multi-gigabyte model), creating a new object for every request would be a performance disaster. This approach is only suitable for cases where object creation cost is extremely low.

## (Multi-Thread Case) Do Race Conditions Occur with Local Variables in a Shared Object?

> **No, Local Variables within a method are inherently safe from race conditions.**

Let's assume our endpoint is a synchronous function defined with `def`. When the FastAPI server receives a new request, it grabs a thread from the thread pool to handle it.

Even though multiple threads are executing the same code (the same method) simultaneously, their local variables are **isolated** in memory, which is why race conditions do not occur between them.

### Stack Memory vs. Heap Memory

To understand the underlying reason, we need to know that when an operating system loads a program into RAM as a process, its memory includes both Stack and Heap memory:

-   **Stack**
    -   **Characteristics**: When the OS creates a thread, it allocates a private, independent memory space for it. This is the thread's Stack.
    -   **Purpose**: When a function or method is called, a **Stack Frame** is created on that thread's stack. This frame stores all information related to that function call, including:
        -   Function Parameters
        -   Function Local Variables
        -   Return Address (where to jump back to after the function finishes)
    -   **Lifecycle**: When the function completes, its stack frame is automatically destroyed, and all local variables within it vanish.
-   **Heap**
    -   **Characteristics**: A region of memory shared by all threads within a process.
    -   **Purpose**: Used to store data that has a longer lifecycle or needs to be shared. This includes:
        -   Class Attributes
        -   Global Variables

### A Practical Example

Let's look at the following example. Suppose we have this endpoint:

```python
from src import Retriever

retriever = Retriever()
def data_retrieval(query: str) -> list[str]:
    results: list[str] = retriever(query)
    return results
```

The `retriever` object itself is a global variable, so it's stored in Heap Memory. And the `Retriever` class is implemented as follows:

```python
class Retriever:
    def __init__(self):
        # `self` (the retriever object itself) exists on the Heap (shared)
        # The `self._model` attribute also exists on the Heap with the object (shared)
        self._model = self._load_model() 

    def __call__(self, query: str) -> list[str]:
        # When a thread calls this method,
        # a new Stack Frame is created on "its own Stack"

        # 1. The `query` parameter exists on the thread's own Stack.
        
        # 2. `process_log` is a local variable, also on the thread's own Stack.
        process_log = f"Processing query: {query}" 

        # 3. `results` is also a local variable, on the thread's own Stack.
        #    It reads the shared self._model, but this is a read-only operation, so it's safe.
        results = [f"Result for {query} using {self._model}"]
        
        return results # The method returns, and this Stack Frame is destroyed.
```

Based on the code above, let's simulate a scenario:

Two requests come in at the same time, and the FastAPI server assigns Thread A and Thread B to handle them:

-   **Thread A calls `retriever(query="cat")`**:
    -   A Stack Frame is created on Thread A's Stack.
    -   This frame contains variables like `query = "cat"` and `process_log = "Processing query: cat"`.
-   **Thread B simultaneously calls `retriever(query="dog")`**:
    -   A completely separate Stack Frame is created on Thread B's Stack.
    -   This frame contains variables like `query = "dog"` and `process_log = "Processing query: dog"`.

The key point is: Thread A cannot access any data on Thread B's stack, and vice versa. They operate on their own local variables as if they were in completely separate rooms. Although both read the shared `self._model` from the Heap, as long as this is a read-only operation, no conflict will arise.

## (Single-Thread Case) Do Race Conditions Occur with Local Variables in a Shared Object?

Next, let's discuss the single-thread case. Suppose our endpoint is an asynchronous function defined with `async def`. Now, the same thread handles different requests. Will a race condition occur in this scenario?

> No, even in an async context, race conditions do not occur with local variables from different requests.

Let's dive deeper into how `async/await` works under the hood to understand why a single thread (and a single stack) doesn't cause variables to get mixed up and create race conditions.

### The Core of Async: Coroutines are Objects, Not Functions

When we call a `def` function, it executes immediately, and a stack frame is created on the stack.

However, when we call an `async def` function, **it does not execute immediately**. Instead, it returns a **Coroutine Object**.

This Coroutine Object is essentially a **Stateful Generator**. You can think of it as a "pausable function" that packages everything needed for its execution:
-   The code to be executed.
-   All of its Local Variables.
-   A pointer to the line of code where it last left off (Instruction Pointer).

These Coroutine Objects themselves are stored in **Heap** memory, the same area shared by all threads.

### The Role of the Event Loop: The Chess Master Who Can Play Many Games Concurrently

Imagine the Event Loop as a chess master, and each incoming request creates a Coroutine Object, which is like a new game of chess.

1.  **Request A arrives**:
    *   FastAPI calls the `async def` endpoint, creating the `Coroutine_A` object.
    *   FastAPI hands `Coroutine_A` to the Event Loop and says, "Please run this task."
    *   The Event Loop (the chess master) walks over to board A and starts executing `Coroutine_A`.
    *   It loads the initial state of `Coroutine_A` (parameters, local variables) onto the **single thread's Stack** and starts "making a move."

2.  **Encountering `await`**:
    *   The code in `Coroutine_A` reaches `await some_io_operation()`.
    *   This is like the chess master making a move and then having to wait for the opponent to think (waiting for a database response).
    *   The semantics of `await` are: "**Pause my current execution and give control back to the Event Loop.**"
    *   Before pausing, `Coroutine_A` **saves its entire current state** (including the values of all its local variables and the line number it's on) **back into its own object** (the `Coroutine_A` object on the Heap).
    *   Then, it is **removed** from the thread's stack. At this moment, the stack is relatively clean again.

3.  **Switching to Request B**:
    *   Meanwhile, Request B may have arrived, creating the `Coroutine_B` object.
    *   The Event Loop (the chess master) sees that there's nothing to do at board A, so it walks over to board B. (This illustrates that the master plays **concurrently**, not in parallel.)
    *   It loads the state of `Coroutine_B` onto the **same thread stack** and starts servicing Request B.

4.  **I/O Operation Completes**:
    *   After a while, `some_io_operation()` finishes (the database returns a result).
    *   The Event Loop is notified: "The opponent at board A has made their move!"
    *   At the next appropriate moment (e.g., when `Coroutine_B` also hits an `await` or finishes), the Event Loop returns to board A.
    *   It **perfectly restores all the previously saved state (including all local variables) from the `Coroutine_A` object back onto the thread stack** and continues execution from the line right after the `await`.

So, to answer our core question:

**What happens to the content on the stack?**

When an `await` occurs, the current coroutine's state is fully "serialized" and saved back into its object on the Heap, and its stack frame is **popped off** the stack. The stack is then free to be used safely by the next coroutine.

**Will local variables from different requests exist on the same stack and cause a race condition?**

No. Because at any given moment, **the stack only contains the data for the one coroutine that is currently executing**. The data for different coroutines is kept isolated in their respective objects on the Heap. They never appear on the stack at the same time, so it's impossible for them to conflict or cause a race condition.

## When is Async More Efficient Than Multi-Threading?

> In I/O-bound applications, the async model achieves higher resource utilization at a lower cost.

This is a critical question and the fundamental reason for the popularity of asynchronous programming. You often hear that async is more efficient than multi-threading because, in a **specific and very common** scenario—**I/O-bound** applications—the async model achieves higher resource utilization at a lower cost.

The efficiency gains come from several key factors:

### The Vastly Different Cost of Context Switching

This is the most central and important reason.

*   **Multi-threading Context Switching (Expensive)**
    *   **Enforced by the Operating System (OS) Kernel**: When the OS decides to pause one thread and run another, it needs to intervene.
    *   **Heavyweight Operation**: This process requires saving the **entire** CPU state of the current thread, including CPU registers, the Program Counter, the Stack Pointer, etc. Then, it loads the complete state of the next thread. This involves switching between the OS Kernel Mode and User Mode, which is a **very time-consuming** operation on a computer's scale (often in microseconds, but it adds up significantly).
    *   **Preemptive**: The OS forcibly takes away the thread's execution right, regardless of whether the thread is willing. This can happen at any moment.

*   **Async Context Switching (Extremely Cheap)**
    *   **Managed by the Application's Event Loop**: The switching happens entirely within the application's user space. The OS is completely unaware of and doesn't care about these coroutines.
    *   **Lightweight Operation**: A switch only happens at an `await` keyword. All the Event Loop does is save the current coroutine's state (a few variables and a pointer) and then pick up the next ready coroutine from a queue. This is almost as fast as a **single function call** (nanoseconds).
    *   **Cooperative**: The switch only occurs where the programmer explicitly writes `await`. The coroutine "voluntarily yields" control.

**Conclusion**: To handle 10,000 concurrent requests, multi-threading might require the OS to perform tens of thousands of expensive context switches. Async only requires the Event Loop to perform tens of thousands of extremely cheap internal state switches.

### Memory Overhead

*   **Multi-threading**: For every thread created, the OS must allocate a **full thread stack**. The default size of this stack is usually not small (e.g., it could be 8MB on Linux). If you need to create 1,000 threads to handle 1,000 concurrent requests, the stacks alone would consume `1000 * 8MB = 8GB` of memory! This makes it difficult for the system to scale to a very high number of concurrent connections.

*   **Async**: There is only one thread, so there is only one stack. Although all the Coroutine Objects also consume memory (on the Heap), the size of each coroutine object is far smaller than a full thread stack (usually just a few KB). Therefore, with a few gigabytes of memory, you can easily maintain tens or even hundreds of thousands of coroutines in a "waiting for I/O" state.

This difference is key to why async can easily solve the famous **C10k problem** (handling ten thousand concurrent connections on a single machine).

### Python's Global Interpreter Lock (GIL)

This point is particularly important in the world of Python.

*   The GIL in the CPython interpreter is a master lock that ensures that at any given moment, **only one thread can execute Python bytecode**.
*   This means that even on an 8-core CPU, multiple threads in a Python program **cannot achieve true parallelism for CPU-intensive** computations. They are actually taking turns running quickly on the same CPU core, giving the illusion of parallelism, but the total computational throughput does not increase.
*   **However, when a thread is waiting for I/O (like network or disk access), it releases the GIL**. This is why multi-threading is still effective for I/O-bound tasks in Python.
*   Nevertheless, since the GIL restricts true CPU parallelism, and async can handle I/O-bound tasks on a single thread with much lower overhead, the async model becomes more attractive for most web service scenarios.

### Multi-Threading vs. Async Comparison

| Feature | Multi-Threading (`def` endpoint) | Async (`async def` endpoint) |
| :--- | :--- | :--- |
| **Execution Unit** | Thread | Coroutine/Task |
| **Scheduler** | Operating System (OS) | Event Loop (Application Level) |
| **Switching Method** | Preemptive (OS forces switches) | Cooperative (`await` voluntarily yields) |
| **Stack Management** | **Each thread has its own separate OS stack.** | **All coroutines share the same thread's stack.** |
| **State Storage** | State always resides on the respective stack. | When a coroutine **pauses (`await`)**, its state (including local variables) is packed and saved back to the **coroutine object on the Heap**. |
| **Memory Overhead**| High | Low |
| **Context Switch Cost** | High | Low |

## Are Thread-Safe and Async-Safe Equivalent?

This is an extremely important question and a common pitfall for developers who work with both synchronous and asynchronous code.

> **No, Thread-Safe and Async-Safe are absolutely not equivalent.**

More importantly, a typical thread-safe implementation, when used directly in an async environment, is **not only unsafe but will likely cause a deadlock**.

### Who is the Enemy of Thread-Safe and Async-Safe?

First, let's understand what "Thread-Safe" and "Async-Safe" mean by thinking in reverse. Who are their enemies? What situations cause code to be "Thread-Unsafe" or "Async-Unsafe"?

*   **Thread-Safe**
    *   **Enemy**: **Parallel Execution / Preemptive Multitasking**
    *   **Reason**: When multiple threads are scheduled by the OS, a thread running on a CPU can be interrupted at any point, between any two instructions, and switched out for another thread. This can lead to multiple threads **simultaneously reading and writing** to the same memory location, causing a race condition.
    *   **Weapon**: **Blocking Locks**, such as `threading.Lock`.

*   **Async-Safe**
    *   **Enemy**: **Blocking the Event Loop**
    *   **Reason**: In the async world, there is only one thread. If any piece of code hogs the CPU or performs a blocking I/O operation, the entire Event Loop gets stuck, and all other concurrent tasks will grind to a halt.
    *   **Weapon**: **Non-blocking Operations** and **Cooperative Yielding**, such as `asyncio.Lock` and `await`.

### How `threading.Lock` vs. `asyncio.Lock` Work

The behavior of these two locks is worlds apart:

*   **Behavior of `threading.Lock.acquire()`**
    *   When a thread calls `acquire()`, if the lock is available, it immediately acquires it and continues execution.
    *   If the lock is held by another thread, **it puts the current thread into a "sleep" or "blocked" state**. The OS will suspend this thread until the lock is released. It **completely relinquishes control of the CPU**.

*   **Behavior of `await asyncio.Lock.acquire()`**
    *   When a coroutine `await`s an `acquire()` call, if the lock is available, it immediately acquires it and continues execution.
    *   If the lock is held by another coroutine, **it does not block the thread**. Instead, it:
        1.  Registers itself as waiting for this lock.
        2.  **Voluntarily gives control back to the Event Loop**.
    *   The Event Loop, upon regaining control, proceeds to run other ready coroutines.

### Deadlock: Adding `threading.Lock` to Async Code

Now, let's place a thread-safe object implemented with `threading.Lock` into an `async def` endpoint and see what happens!

```python
import threading
import asyncio
import time

class DangerousRetriever:
    def __init__(self):
        # This is a lock designed for multi-threading
        self._lock = threading.Lock()
        self.cache = {}

    # Let's assume we provide an async method for our async endpoint
    async def process_query_async(self, query: str):
        print(f"Coroutine {query}: Preparing to acquire threading.Lock")
        
        # Here's where the disaster begins!
        # acquire() is a blocking call that will freeze the entire thread!
        with self._lock:
            print(f"Coroutine {query}: Successfully acquired threading.Lock")
            
            if query in self.cache:
                return self.cache[query]

            # Simulate an async I/O operation that needs `await`
            # e.g., await db.fetch(query)
            print(f"Coroutine {query}: About to await, but still holding the lock")
            await asyncio.sleep(1) # <<--- Awaiting while holding a threading.Lock
            
            result = f"Result for {query}"
            self.cache[query] = result
            print(f"Coroutine {query}: Releasing threading.Lock")
            return result
```

**Execution Flow Analysis:**

1.  **Coroutine A** (`process_query_async("A")`) starts running.
2.  It successfully acquires `self._lock` (a `threading.Lock`).
3.  It reaches `await asyncio.sleep(1)`. The meaning of `await` is "pause me and give control back to the Event Loop."
4.  The **Event Loop** regains control, sees that **Coroutine B** (`process_query_async("B")`) is ready, and starts executing Coroutine B.
5.  Coroutine B reaches `with self._lock:` and tries to acquire the same `threading.Lock`.
6.  Because Coroutine A still holds this lock, Coroutine B's `acquire()` call **blocks**.
7.  **The Critical Point**: The blocking from `threading.Lock` is an **OS-level thread block**. It freezes the **one and only thread** that the Event Loop is running on.
8.  Now, the entire application is frozen. The event loop can no longer schedule any tasks. It can't wake up Coroutine A after its `asyncio.sleep(1)` is over.
9.  Coroutine A can never reach the line that releases the lock because the Event Loop has been blocked by Coroutine B. Coroutine B can never acquire the lock because Coroutine A can never release it.
10. **Deadlock.**

### Best Practices

*   **The Isolation Principle**: Synchronization primitives in the `threading` module (Lock, Event, Semaphore, etc.) are designed for multi-threaded environments. Primitives in the `asyncio` module are designed for single-threaded coroutine environments. **Never mix them**.

In short, always remember: **Thread-Safe ≠ Async-Safe**. Choosing async-native tools for asynchronous code and sync-native tools for synchronous code is the golden rule for ensuring your application's stability.

## The Golden Rule for Making a Function/Method Both Thread-Safe and Async-Safe?

> To write code that is simultaneously Thread-Safe and Async-Safe, you should shift your mindset from "Which lock should I use?" to "**How can I avoid using locks altogether?**". The answer is almost always: **Eliminate Shared Mutable State**. By following this core principle, your code will become simpler and more adaptable to various concurrency models.

Here are the design guidelines for creating such universally safe code, ordered by importance:

#### Rule 1: Pursue Pure Functions and Statelessness (The Golden Rule)

This is the most important and effective rule. If a function or method has no state, or if its output is determined entirely by its input, then there is nothing to protect.

*   **How to do it**:
    *   The function should not read or write any global variables or instance attributes (`self.xxx`) of its class.
    *   All necessary data should be passed in explicitly through function parameters.
    *   The function should not have side effects, such as modifying the objects passed into it (unless it's returning a new object).

*   **Example**:
    ```python
    # A universally safe function
    def process_data(data: dict, config: dict) -> dict:
        # Only depends on the input parameters
        # All variables are local
        result = {}
        result['processed_key'] = data.get('key', '') + config.get('suffix', '')
        # Returns a new object instead of modifying the original `data`
        return result
    ```
    This function will always be safe, whether it's called by 100 threads or 100 coroutines simultaneously.

#### Rule 2: Use Immutability

If you must have state, make it immutable. Once created, it cannot be changed.

*   **How to do it**:
    *   Use tuples (`tuple`) instead of lists (`list`).
    *   Use `frozenset` instead of `set`.
    *   Use `dataclasses` with `frozen=True`.
    *   If you need to "modify" something, create a new object instead of modifying it in place.

*   **Example**:
    ```python
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class AppConfig:
        api_key: str
        timeout: int

    class Retriever:
        def __init__(self, config: AppConfig):
            # self._config is a reference to an immutable object.
            # While self._config could be pointed to another object,
            # the AppConfig object itself is safe.
            self._config = config

        def get_timeout(self):
            # A read-only operation is always safe.
            return self._config.timeout
    ```

#### Rule 3: Externalize State Management

This is a key architectural principle. Don't manage complex shared state within your application's memory. Instead, delegate this responsibility to external services designed specifically for concurrency.

*   **How to do it**:
    *   **Caching**: Instead of `self.cache = {}`, use **Redis**. Redis operations (like `SET`, `GET`) are atomic and inherently designed for high-concurrency scenarios.
    *   **Task Queues**: Instead of `self.tasks = []`, use **RabbitMQ** or **Celery**.
    *   **Data Storage**: Use a database and rely on its **transactions** and **row-level locking** to ensure data consistency.

*   **Example**:
    ```python
    import redis

    # Assume r is a Redis connection object
    r = redis.Redis(...)

    # This function is stateless itself; it delegates state management to Redis
    def get_data_with_cache(key: str):
        # GET is an atomic operation, so it's safe
        cached_result = r.get(key)
        if cached_result:
            return cached_result
        
        result = "expensive_db_call()"
        # SETEX (SET with Expiry) is also an atomic operation, so it's safe
        r.setex(key, 60, result) 
        return result
    ```

## The Same Class Loaded in Different Files and Initialized as a Global Variable

In our previous examples, we focused on multiple requests sharing a single global variable:

```python
from src import Retriever

retriever = Retriever()
def data_retrieval(query: str) -> list[str]:
    results: list[str] = retriever(query)
    return results
```

Now, let's consider this scenario: multiple Python files import the same class and initialize it as a global variable:

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

What happens when two requests execute endpoints A and B simultaneously (whether via multi-threading or async)?

> Nothing at all! The two `retriever` objects are actually **completely separate**. One exists in the global scope of the `endpoint_a` module, and the other exists in the global scope of the `endpoint_b` module. Therefore, requests to A and requests to B will use **different** objects, and their instance attributes (`self.xxx`) are **completely isolated** from each other.

### Python's Module Import and Caching Mechanism

To understand this behavior, the key lies not in FastAPI, but in how Python's `import` system works.

1.  **Modules are Only Executed Once**:
    When the FastAPI server starts (e.g., `uvicorn main:app`), it begins importing your code. Python maintains a global dictionary named `sys.modules`, which acts as a cache for modules.
    *   The first time Python encounters `import src` or `from src import Retriever`, it will:
        a. Check if `'src'` is already in `sys.modules`.
        b. If not, it finds the `src.py` file, **executes all the code inside it**, and then stores the created module object in `sys.modules['src']`.
    *   When it later encounters `import src` or `from src import Retriever` in another file, Python finds that `'src'` is already in `sys.modules`. It will **directly retrieve the module object from the cache** and **will not** execute the `src.py` file again.

2.  **Scenario Analysis**:
    Let's assume your main application file (`main.py`) imports both `endpoint_a` and `endpoint_b`.

    *   **Startup Flow (Simplified)**:
        1.  Uvicorn starts and imports your main application file.
        2.  The main app `import endpoint_a`.
        3.  Python begins executing the code in `endpoint_a.py`.
        4.  It encounters `from src import Retriever`. Since this is the first time, Python executes `src.py` and caches the `src` module. The `Retriever` class is loaded into memory.
        5.  It encounters `retriever = Retriever()`. This line of code **is executed**, and an **instance** of `Retriever` is created (let's call it `instance_A`) and assigned to the global variable `retriever` within the `endpoint_a` module.
        6.  The main app then `import endpoint_b`.
        7.  Python begins executing the code in `endpoint_b.py`.
        8.  It encounters `from src import Retriever`. This time, Python finds the `src` module in `sys.modules` and directly retrieves the `Retriever` class from the cache. `src.py` **is not** executed again.
        9.  It encounters `retriever = Retriever()`. This line of code **is also executed**. It calls the constructor of the same `Retriever` class, creating a **brand new, independent `Retriever` instance** (let's call it `instance_B`) and assigns it to the global variable `retriever` within the `endpoint_b` module.

From this, we know that if two requests arrive simultaneously:
- A request to `/A` will use the `retriever` global variable (which is `instance_A`).
- A request to `/B` will use its `retriever` global variable (which is `instance_B`).

Because they are two **different** object instances, their respective instance attributes (`self.xxx`) are completely isolated. If `instance_A` has an internal counter `self.count`, changes to it will not affect the `self.count` in `instance_B` at all.

The race condition problem we discussed earlier still exists, but it's now confined within each respective endpoint:
*   Multiple **simultaneous requests to A** will share `instance_A`, potentially causing a race condition within `instance_A`.
*   Multiple **simultaneous requests to B** will share `instance_B`, potentially causing a race condition within `instance_B`.
*   However, requests to A and requests to B **will not** interfere with each other through the `retriever` object.

### Dangerous Case: Class Attributes

Although the two instances are separate, they are created from the **same class**. If you define **class attributes** in the `Retriever` class, those attributes will be **shared** by both `instance_A` and `instance_B`!

```python
# src.py
class Retriever:
    # This is a class attribute, shared by all instances
    total_requests_processed = 0 

    def __init__(self):
        # This is an instance attribute, unique to each instance
        self.instance_name = "instance_" + str(id(self))

    def __call__(self, query: str):
        Retriever.total_requests_processed += 1 # Modifying a shared class attribute!
        print(f"Processing in {self.instance_name}. Total processed: {Retriever.total_requests_processed}")
        return [query]
```
In this example, requests to both A and B will modify the **same** `Retriever.total_requests_processed` variable, which will lead to a cross-endpoint race condition.

### Best Practice

The architectural pattern above (initializing the same class in each endpoint file) is technically feasible but is generally considered bad practice for the following reasons:

1.  **Violates DRY (Don't Repeat Yourself)**: You're repeating the object creation logic in multiple places.
2.  **Resource Waste**: If `Retriever()` initialization is an expensive operation (like loading a large model), you are now loading it twice, consuming double the memory and startup time.
3.  **Inconsistent State**: You might expect `retriever` to be a global singleton, but you've actually created multiple instances, which could lead to unexpected behavior.

#### Centralized Dependency Management

A cleaner, more robust approach is to create a single shared instance and have all components that need it use that one instance.

```python
# src/dependencies.py

from .retriever_class import Retriever

# Create the single, shared instance here.
# There will only be one retriever object during the entire application lifecycle.
retriever = Retriever() 
```

```python
# endpoint_a.py
from src.dependencies import retriever # Import the instance directly!

def A(query):
    a = retriever(query)
    return a
```

```python
# endpoint_b.py
from src.dependencies import retriever # Import the same instance!

def B(query):
    b = retriever(query)
    return b
```

This way, all requests, whether to A or B, will share the **single instance** created in `dependencies.py`. This not only saves resources but also makes state management clear and controllable.

## Conclusion

In this article, we started with the scenario of "multiple requests simultaneously accessing the same global variable on a FastAPI server." We explored how FastAPI handles Synchronous (Multi-Thread) and Asynchronous (Async) operations, the conditions under which race conditions occur, and the golden rules for avoiding them. Finally, we also covered how Python's module caching and management system works.