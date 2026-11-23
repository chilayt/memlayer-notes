# memlayer — 可审计 agent 记忆笔记

[English](README.md) | **中文**

> 一份**研究笔记，不是记忆产品**：agent 记忆层的评测方法学 + 一个真实调试案例——*render gap（渲染鸿沟）*，检索到的事实到不了模型。

## 这里有什么

| 内容 | 位置 | 说明 |
|---|---|---|
| 诊断文章 | [`article/the-render-gap.zh.md`](article/the-render-gap.zh.md) | 为什么检索到的事实到不了 agent；可跑 A/B 复现机制。 |
| 评测方法学规范 | [`eval-methodology/SPEC.zh.md`](eval-methodology/SPEC.zh.md) | 冻结 / 槽位判分 / 配对精确 McNemar / 盲校准。 |
| 参考实现（教学演示） | [`eval-methodology/reference/`](eval-methodology/reference/) | buggy-vs-fixed 渲染 A/B + 槽位判分 + 精确 McNemar。合成、可跑。 |
| 安全/撤回边界 | [`docs/SAFETY-BOUNDARIES.zh.md`](docs/SAFETY-BOUNDARIES.zh.md) | **撤回≠遗忘**；设计目标，本仓库未实现。 |

## 核心观点

1. **「检索到」≠「模型看见」。** 「排序+预算」的渲染步骤会悄悄丢证据。审计渲染了什么、**以及丢了什么**。
2. **「冲突信新的」≠「全局按时间重排」。** 后者牺牲相关性。
3. **评测要防自欺**：冻结、同语料配对、槽位判分、盲校准。「不显著」≠「等价」；单题翻转是机制演示，不是结论。

## 本仓库能复现什么、不能复现什么

- **能复现**：**渲染机制**——`render_relevance_first.py` 确定性地展示 buggy 丢答案、fixed 保留。无需模型。
- **不能复现**：模型**采纳**数字。那些来自私有环境、是轶事；文章单题 0/5→5/5 **仅作机制示意**——单题、重复不独立，不适用显著性检验。

```bash
python eval-methodology/reference/render_relevance_first.py
python eval-methodology/reference/eval_reference.py
```

仅 Python 标准库，无第三方依赖。

## 状态与边界

- 研究笔记，非生产就绪。完整系统在私有打磨。
- 撤回能力是**设计目标，本仓库未实现**；见 [SAFETY-BOUNDARIES.zh.md](docs/SAFETY-BOUNDARIES.zh.md)。**别假设「撤回=遗忘」。**
- 所有示例均为**合成**，不含真实用户/项目数据。

## 后续实现的验证

遇到改口时，核对旧约定和来源，由作者确认是全量替换还是限定条件的例外，并保留双方出处。回归评测可在新会话分别跑常规场合和例外场合，核对实际送入模型的记忆与输出是否一致。对外示例使用虚构记录，便于复现。

引擎和 DSH 适配器另行准备，本仓库持续维护合成评测方法与渲染演示。

## 许可

- **代码**（`reference/`）：Apache-2.0，见 [LICENSE](LICENSE)。
- **文档与文章**：CC-BY-4.0（署名），见 [NOTICE](NOTICE)。