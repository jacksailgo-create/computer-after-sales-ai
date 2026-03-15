---
source: lenovo_support
url: https://iknow.lenovo.com.cn//knowledgeapi/api/knowledge/knowledgeDetails?knowledgeNo=408
category: manuals
---

# 知识库 408

## 电脑会自动开机启动，是什么问题？

## 问题描述
有时我们会发现一个奇怪的故障，明明没有 按电源按钮，电脑却无缘无故的自动启动了，这究竟是什么故障？或者是什么功能？应该如何处理呢？

## 分类
主类别: 内置设备
子类别: 内存
问题类别: 内存

## 元数据
创建时间: 2025-01-09|版本: 4.0

## 解决方案
**原因1：BIOS下开启了网络唤醒功能**

请您开机进入BIOS，检查POWER-Automatic Power ON-Wake Up On LAN项，如果此项为非Disabled状态，表示开启了网络唤醒功能，请将其设置为Disabled，即可关闭。

![](https://chinakb.lenovo.com.cn/ueditor/php/upload/image/20160223/1456211638617554.jpg)

**原因2**：BIOS下开启了来电唤醒功能

请您开机进入BIOS，检查检查POWER-After Power Loss选项，如果此项为非Power Off状态，表示开启了来电唤醒功能，即主机通电即开机，请将其更改为Power Off状态即可。

![](https://chinakb.lenovo.com.cn/ueditor/php/upload/image/20160223/1456211638408484.jpg)

**原因3**：上一次使用电脑后非正常关机也可能是导致电脑自动开机的原因，请您在使用电脑完成后，在系统下正常关机。

<!-- 文档主题: 电脑会自动开机启动，是什么问题？ （知识库编号: 408） -->