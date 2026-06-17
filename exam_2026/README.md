# 2026 笔试归档

本目录归档了 2026 年宏观研究 / 量化方向笔试题目和解答。

## 目录结构

```
exam_2026/
├── README.md                              ← 本索引
├── Q1_market_factors/                     ← 第一题:结构化信息提取
│   ├── question.md                        题目原文
│   ├── extract_market_factors.py          可运行代码 (含 prompt + 解析逻辑)
│   ├── design_notes.md                    答题说明 (运行方法 + 设计思路)
│   ├── answers.md                         两道简答题的完整作答
│   ├── run_log.txt                        运行日志 (token 用量、耗时、步骤)
│   └── sample_output.json                 示例文本对应的结构化输出
└── Q2_cta_backtest_bug/                   ← 第二题:Bug 诊断与代码审查
    ├── question.md                        题目原文 (背景 + Part A + Part B)
    └── original_buggy.py                  实习生 vibe-coding 的原始有 bug 版本
```

## 题目一览

| 题号 | 题目             | 类型              | 状态        |
| ---- | ---------------- | ----------------- | ----------- |
| 1    | 结构化信息提取   | LLM Prompt 工程   | ✅ 已完成   |
| 2    | CTA 回测 Bug 诊断 | 代码审查 + 重写    | ⏳ 待完成   |

## 使用方式

### Q1

```bash
cd Q1_market_factors
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-xxx
python extract_market_factors.py
```

### Q2

```bash
cd Q2_cta_backtest_bug
python original_buggy.py        # 复现有 bug 的原始回测
# Part A / Part B 解答待添加
```
