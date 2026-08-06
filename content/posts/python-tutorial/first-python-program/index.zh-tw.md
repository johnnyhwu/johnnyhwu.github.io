---
# weight: 1
title: "第一個 Python 程式：用 input( ) 與 print( ) 寫出互動程式"
date: 2022-01-26T03:39:20
lastmod: 2026-08-06
draft: false
description: "把變數與資料類型組起來，寫出第一支會跟使用者互動的 Python 程式。本文逐行拆解 print( )、input( )、len( ) 的用法，並說明 str( )、int( )、float( ) 型別轉換為什麼是必要的。"
featuredImage: "featured-image.jpg"

tags: ["Python Tip"]
categories: ["python-tutorial"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "python-tutorial/:contentbasename"
---

<!--more-->

## 前言

這是 Python 程式語言入門教學的第 4 篇文章。前一篇[〈Python 變數與資料類型〉](../python-variable-data-type/)介紹了「變數」的觀念以及基本的「資料類型」，這兩者幾乎是所有程式語言共通的基礎，如果還沒有概念，建議先把那篇看完再回來。

這篇要做的事情很單純：把前面學到的零件組起來，寫出第一支「跑得動、而且會跟人互動」的 Python 程式，然後一行一行拆開來看它到底做了什麼。

## 第一個 Python 程式的功能

第一支完整的程式，目標是做出「互動性」。所謂互動，就是程式不再只是自言自語地印出固定內容，而是能接收使用者給的資料，經過一些運算後，再把結果回饋給使用者。

具體來說，我們希望使用者透過「鍵盤」輸入一些文字或數字，程式拿到輸入後做一些處理，最後把結果顯示到「螢幕」上。

## 電腦的輸入與輸出裝置

你可能會覺得奇怪，為什麼要特別強調是「鍵盤輸入」與「螢幕輸出」？因為電腦連接的輸入裝置不只有鍵盤，輸出裝置當然也不只有螢幕。

{{< image src="input-and-output-device-of-cimputer.jpg" alt="電腦周邊輸入與輸出裝置的示意圖，左側為輸入裝置、右側為輸出裝置。" caption="電腦有許多輸入與輸出裝置" >}}

如上圖所示，輸入裝置還包含「滑鼠」、「鍵盤」、「攝影機」；輸出裝置則包含「印表機」、「螢幕」與「喇叭」。寫程式時，我們可以自由地決定要讀取哪一個輸入裝置的資訊，以及要把結果送到哪一個輸出裝置。這篇的程式只用到最單純的一組：鍵盤進、螢幕出。

## 程式碼撰寫

搞懂輸入與輸出裝置之後，就可以開始動手寫程式了。先開啟 Colab（如果還不熟悉 Colab 的操作，可以先看[〈Google Colaboratory〉](../google-colaboratory/)那篇），把下圖的程式碼一字不漏地打上去並執行。

之所以用圖片而不是可複製的程式碼區塊，就是為了不讓你複製。第一次學程式，盡量每個字都自己敲過一遍，進步會快很多。

{{< image src="python-program.jpg" alt="Colab 上的第一支 Python 程式截圖，包含註解、print( )、input( )、len( ) 等程式碼與下方的執行結果。" caption="第一個 Python 程式" >}}

執行這段程式碼時，會有兩次「輸入」的機會，跑完之後應該會得到類似程式碼下方 (黑色字體) 的結果。

## 了解程式碼

如果看不懂上面的程式碼也別擔心，接下來會逐行拆解。有任何問題也歡迎在 [YT](https://www.youtube.com/channel/UCKzu0kgUsffUddIORpQFGtQ) 頻道留言詢問。

- 第 1 行：以「#」開頭的內容在 Python 中一律視為「註解」，程式執行時會直接忽略。註解的用途是解釋程式碼在做什麼，日後回頭看這份程式碼會輕鬆很多。
- 第 2 行：透過 print( ) 函式把字串顯示在螢幕上。「函式」的完整概念會在[之後的文章](../python-function/)介紹，這裡只需要先知道：呼叫 (使用) print( ) 時，要把想顯示的字串放進 print( ) 的括號中。例如把字串 ‘Hello World !’ 放進括號裡，執行後螢幕就會顯示「Hello World !」。像這樣傳入函式的東西，我們稱為「參數」。
- 第 3-4 行：和第 2 行一樣都是用 print( ) 把字串印到螢幕上。差別在於第 3 行的參數用到了字串乘法 (String Replication) 的技巧，也就是把同一個字串重複接起來，例如 ‘ab’ * 3 會得到 ‘ababab’，常拿來畫分隔線。
- 第 5 行：透過 input( ) 函式接收使用者輸入的資料。在 Colab 上執行 input( ) 時，畫面會跳出一個輸入框等待使用者打字，使用者按下 Enter 就算完成輸入，Python 會把輸入的內容打包成「一個字串」存進變數 (myName) 裡。
- 第 6 行：一樣用 print( ) 把字串印到螢幕上，但這次是先用字串加法 (String Concatenation) 把幾段字串接成一段，再當作參數傳進去，例如 ‘Hello, ’ + ‘Tom’ 會得到 ‘Hello, Tom’。這裡要特別注意：不管用的是字串乘法還是字串加法，最後傳進 print( ) 的參數始終都只有「一個字串」。
- 第 7 行：透過 len( ) 函式計算字串的長度。把字串傳入 len( )，它就會回傳這個字串的長度。因為 len( ) 回傳的是整數型別 (int type)，沒辦法直接跟字串做加法，所以要再用 str( ) 函式把整數轉成字串型別 (str type)。
- 第 8-11 行：用到的都是前面出現過的觀念，這裡就不再贅述。

第 7 行是這支程式裡最容易卡住的地方，值得再多看一眼。我們可以看看下圖的程式碼：

{{< image src="python-len-function.jpg" alt="Python 中呼叫 len( ) 函式取得字串長度的程式碼與輸出結果截圖。" caption="透過 Python 中的 len( ) 函式取得字串長度" >}}

len( ) 會回傳傳入字串的長度，而且回傳的型別是整數 (int)。在程式中我們需要做的是字串加法，所以得先把整數型別 (int) 的 3 轉成字串型別 (str) 的 ‘3’，才能跟其他字串接在一起。

## 型別轉換

型別轉換在程式中相當常見，因為不同型別各有各的能力。字串型別 (str) 可以做字串的加法 (Concatenation) 與乘法 (Replication)；整數型別 (int) 與浮點數型別 (float) 則可以做數值運算。當手上資料的型別跟你想做的運算對不起來時，轉型就是必要動作。

如下圖所示：

{{< image src="python-type-conversion.jpg" alt="Python 中 str( )、int( )、float( ) 三種型別轉換函式的程式碼與輸出結果截圖。" caption="Python 中的型別轉換" >}}

透過 str( ) 將整數 3 轉為字串 ‘3’；透過 int( ) 將字串 ‘3’ 轉為整數 3；透過 float( ) 將字串 ‘3’ 轉為浮點數 3.0。

## 結論

這篇我們寫出了第一支具有互動性的 Python 程式，用上了前一篇提過的變數與資料類型，也順帶認識了新的觀念：函式，包含 print( )、input( )、len( ) 以及 str( )、int( )、float( ) 這幾個轉型用的函式。函式的完整概念會在[之後的文章](../python-function/)深入介紹。

下一篇文章要學的是 Python 程式中的流程控制，從[〈Python Boolean Operator〉](../python-boolean-operator/)開始。
