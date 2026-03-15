🧠 架构思考过程 (Thinking Process)
在这个 Multi-Agent 系统中，我们面临的核心问题是：“当用户提出一个复杂问题时，系统该怎么分工？”

为什么需要 Supervisor（主管）？
大模型如果同时拥有太多工具（比如查故障、查地图、查订单、退款），它会非常容易“幻觉”或搞错调用顺序。因此，我们设立了一个 Supervisor。它的核心职责不是干活，而是当产品经理/路由器。它只负责理解用户的整体意图，然后决定把任务派给谁（更新 state["next_agent"]）。

为什么需要条件边（Conditional Edges）？
这模拟了现实中的派单逻辑。Supervisor 思考完毕后，图必须知道下一步往哪走。add_conditional_edges 就是读取主管的“决策”，然后动态决定是将状态流转给 TechAgent（处理修电脑的技术问题），还是 ServiceAgent（处理查网点、查保修的售后服务问题），亦或是问题已经解决，直接走到 END (FINISH)。

为什么子智能体干完活，还要指回给 Supervisor？(add_edge)
这是这个架构最精妙的地方——形成了闭环（The Loop）。
假设用户问：“我的电脑蓝屏了，而且我想知道附近哪有维修站？”

第一轮：Supervisor 发现有技术问题，派给 TechAgent。

第二轮：TechAgent 解答了蓝屏问题，把控制权交回给 Supervisor。

第三轮：Supervisor 检查对话历史，发现“找维修站”的需求还没处理，于是再次派单给 ServiceAgent。

第四轮：ServiceAgent 查完地图并回复后，交回给 Supervisor。

第五轮：Supervisor 发现用户的所有问题都已解决，输出 FINISH，流程结束。