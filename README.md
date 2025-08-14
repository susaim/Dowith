# dowith

开发文档见 [about.md](about.md)。

更多文档与待办事项请见 [docs](docs/) 目录，特别是 [tudo.md](docs/tudo.md) 用于追踪文档目标与后续维护。完整指南参见 [文档索引](docs/index.md)。

## 使用

```bash
pip install -e .
dw start --name MyProject --mode handoff
dw roles
dw status
dw flow ls        # 查看工作流阶段
dw pm --seed "hello"   # 启动 PM 角色对话并记录日志
dw role add qa --from qa.md  # 导入角色
dw next          # 下一阶段
dw back          # 上一阶段
```

开发进展记录存放于 [docs/progress](docs/progress/) 目录，按日期总结已完成与待办事项。
