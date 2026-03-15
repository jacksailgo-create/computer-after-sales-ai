---
source: lenovo_support
url: https://iknow.lenovo.com.cn//knowledgeapi/api/knowledge/knowledgeDetails?knowledgeNo=897
category: manuals
---

# 知识库 897

## WIN2000SERVER安全模式可以进入，但是无法进入正常模式，如何解决？

## 问题描述
本文提供了WIN2000SERVER安全模式可以进入但是无法进入正常模式的解决方案。

## 分类
主类别: 操作系统故障
子类别: 系统应用操作
问题类别: 系统应用操作

## 元数据
创建时间: 2024-12-15|版本: 1.0

## 解决方案
**解决方法：**

万全T168安装WIN2000SERVER系统，系统登录时长时间停留在蓝色进度条处，没有任何报错，无法进入系统。但是[安全模式](/detail/kd_17783.html)可以正常进入。怀疑系统受保护的链接文件调用出错。以安全模式登录，在[命令提示符](/detail/kd_17641.html)中执行命令：[SFC](/detail/kd_18007.html) /SCANNOW，即使用[系统文件](/detail/kd_17533.html)检查器对受保护的系统文件进行快速扫描，然后[重启](/detail/kd_17977.html)，问题解决，WIN2000 SERVER可以正常登录。

<!-- 文档主题: WIN2000SERVER安全模式可以进入，但是无法进入正常模式，如何解决？ （知识库编号: 897） -->