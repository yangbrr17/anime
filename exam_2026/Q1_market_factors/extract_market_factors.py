"""
第一题: 结构化信息提取与展示
使用 Claude API 将非结构化的市场资讯文本解析为结构化的 "市场因子卡片" JSON。
"""

import json
import re
import os
from anthropic import Anthropic

client = Anthropic()
MODEL = "claude-opus-4-7"


SYSTEM_PROMPT = """你是一名资深宏观研究员助手,专门负责把市场资讯文本(央行讲话、PMI 数据、美联储会议纪要等)
解析为结构化的"市场因子卡片"。你必须严格按照下方 JSON Schema 输出,不得擅自增减字段。

# 输出 JSON Schema
{
  "date": "YYYY-MM-DD",                       // 资讯发生日期, ISO 格式
  "factors": [                                // 因子卡片数组, 每条核心事件一张卡
    {
      "factor_id": "string",                  // 大写英文+下划线+日期, 如 FED_RATE_20260430
      "category": "货币政策|经济数据|财政政策|地缘政治|流动性|其他",
      "entity": "string",                     // 事件主体, 如 美联储/中国央行/美国劳工部
      "event": "string",                      // 事件简述, 一句话
      "details": {},                          // 关键数值字段, 灵活展开 (rate_range, value, prev, expected, stance ...)
      "market_impact": "利多债券|利空债券|中性偏鹰|中性偏鸽|利多权益|利空权益|中性",
      "sentiment_score": 0.0,                 // 情绪打分, [-1, 1] 区间, 负值偏鹰/偏空, 正值偏鸽/偏多
      "source_quote": "string"                // 原文中支撑该判断的关键引用
    }
  ],
  "cross_asset_summary": {                    // 跨资产行情快照
    "rates": {},                              // 例: {"10Y Treasury": {"change_bp": -12, "close": 4.28}}
    "fx": {},
    "equity": {}
  }
}

# 正向约束 (必须遵守)
1. 只输出一个 JSON 对象, 用 ```json ... ``` 代码块包裹, 不输出任何解释性文字。
2. 所有字符串字段使用双引号; 中文字段保持中文。
3. date / factor_id 内日期统一 ISO 格式 (YYYY-MM-DD / YYYYMMDD)。
4. 数值字段使用数字类型, 不要加引号或单位; 单位通过字段名表达 (change_bp, close, value_wan_yi 等)。
5. factors 数组按事件在原文出现的先后顺序排列。
6. 每个因子必须从原文中摘录 source_quote 作为依据 (若原文无直接引语, 取最相关的短句)。
7. sentiment_score 必须在 [-1, 1] 闭区间内, 保留一位小数。
8. cross_asset_summary 中无数据的子项保留空对象 {}, 不要省略键。

# 负向约束 (禁止做的事)
1. 禁止输出 Schema 以外的字段; 禁止改字段名大小写。
2. 禁止编造原文未出现的数字、机构、日期或言论。
3. 禁止把多个事件合并到同一张因子卡; 一事一卡。
4. 禁止使用 null、None、NaN; 缺失数值改为不出现该子键, 缺失字符串使用空字符串 ""。
5. 禁止在 JSON 中加入注释 (// 或 /* */)。
6. 禁止使用 markdown 列表/标题等格式, 只输出纯 JSON。
7. 禁止把单位写进数值 (例如 "4.28%" → close: 4.28; "12bp" → change_bp: -12)。
"""


USER_PROMPT_TEMPLATE = """请根据上述规则,把下面这段市场资讯解析为结构化 JSON。

<news_text>
{text}
</news_text>

再次提醒: 仅输出一个 JSON 对象, 使用 ```json ... ``` 包裹。"""


def _strip_code_fence(raw: str) -> str:
    """从模型回复中提取被 ```json ... ``` 包裹的纯 JSON 字符串。"""
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
    if match:
        return match.group(1)
    # 兜底: 抓第一个 { 到最后一个 }
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start : end + 1]
    return raw


def extract_market_factors(text: str) -> dict:
    """将一段市场资讯文本解析为结构化的市场因子卡片 JSON。

    Args:
        text: 非结构化的中文市场资讯文本。

    Returns:
        符合题目 JSON Schema 的 dict 对象。
    """
    message = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": USER_PROMPT_TEMPLATE.format(text=text)}],
    )

    raw = "".join(block.text for block in message.content if block.type == "text")
    json_str = _strip_code_fence(raw)

    try:
        result = json.loads(json_str)
    except json.JSONDecodeError as e:
        # 出现解析错误时, 让模型自我修复一次
        repair = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            temperature=0,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(text=text)},
                {"role": "assistant", "content": raw},
                {
                    "role": "user",
                    "content": f"上面的输出不是合法 JSON, 错误: {e}。请仅重新输出修正后的 JSON 代码块, 不要任何解释。",
                },
            ],
        )
        raw2 = "".join(b.text for b in repair.content if b.type == "text")
        result = json.loads(_strip_code_fence(raw2))

    return result


if __name__ == "__main__":
    sample = (
        "2026年4月30日,美联储维持基准利率在4.25%-4.50%区间不变,"
        "鲍威尔在会后记者会上表示\"通胀回落进程有所停滞,我们将保持耐心\"。"
        "同日公布的美国4月非农就业新增17.5万人,低于市场预期的24万人,"
        "失业率小幅上升至4.2%。中国央行宣布自5月15日起下调存款准备金率"
        "0.5个百分点,释放长期流动性约1万亿元。10年期美债收益率当日下跌12bp至4.28%。"
    )

    output = extract_market_factors(sample)
    print(json.dumps(output, ensure_ascii=False, indent=2))
