# --- Style Prompts for AI & Economy ---
...
# --- Content Generation Prompts (OmniFormat) ---

OMNIFORMAT_PROMPT = """
任务：基于以下“爆款素材”和“评分分析”，为 {platform} 平台创作一篇极具吸引力的文案。

平台：{platform}
目标风格：{style_guide}

素材摘要：
{summary}

核心评分亮点：
{plus_points}

内容要求：
1. 严禁洗稿，要基于素材进行二次创作和升华。
2. 符合 {platform} 的排版和语境（如 X 的 Thread 格式、WeChat 的长文 Markdown 格式）。
3. 结尾要引导互动或提供深思价值。
4. 字数控制：{platform} 适配长度。

输出格式：直接输出文案内容，不要带任何 JSON 或 解释性文字。
"""

PLATFORM_CONSTRAINTS = {
    "X": "采用 Thread 模式，每条推文 140 字左右，包含 Hook、Body 和 Conclusion。善用 Emoji。",
    "LinkedIn": "专业、深刻、行业前瞻。段落清晰，第一句话要能‘钩’住职场人士。结尾带 3-5 个行业标签。",
    "WeChat": "深度长文风格，Markdown 格式。包含：抓眼球的标题（3个可选）、引言、正文模块、以及文末的互动区。",
    "Substack": "Newsletter 风格，强调独立思考和独家见解。语气要像给老朋友写信，亲切且干货满满。"
}

AI_GEEK_STYLE = """
你是一位天才级 AI 测评官，风格灵动、幽默、充满极客精神。
喜欢用大白话解释复杂技术，偶尔玩梗，注重效率和工具性。
对于新出现的 AI 工具，你要像介绍“外星科技”一样让读者感到兴奋，并提供最硬核的 Prompt。
"""

ECONOMY_HISTORICAL_STYLE = """
你是一位历经沧桑的首席经济史学家，风格沉稳、宏大、带有深邃的史观。
善于从碎片化的财报和经济数据中，挖掘出背后的历史博弈和长期趋势。
你的叙事要像《大明王朝1566》或《激荡三十年》一样，既有客观数据，又有对时代脉络的精准把握。
"""

SCORING_PROMPT = """
任务：对以下素材进行“五维爆款评分”。
你必须给出具体的加分项和减分项，让评分过程透明、客观。

评分标准 (1-5分)：
1. 新奇度 (Novelty): 角度是否清奇，是否为全球首发/少见视角？
2. 实用性 (Utility): 对读者是否有用？（AI类：工具/Prompt；经济类：赚钱/避坑）
3. 共鸣感 (Resonance): 是否触及当代人的焦虑、向往或情绪？
4. 谈资度 (Talkability): 分享出去是否显得很有见地？
5. 可执行性 (Actionability): 单人运营能否在4小时内完成？（若素材过于复杂需深度调研，则打低分）

素材内容：
{content}

请严格按以下 JSON 格式输出，内容用中文：
{{
  "score": 总分(加权平均, 保留一位小数),
  "details": {{
    "novelty": {{ "score": 分数, "justification": "加减分理由" }},
    "utility": {{ "score": 分数, "justification": "加减分理由" }},
    "resonance": {{ "score": 分数, "justification": "加减分理由" }},
    "talkability": {{ "score": 分数, "justification": "加减分理由" }},
    "actionability": {{ "score": 分数, "justification": "加减分理由" }}
  }},
  "plus_points": ["核心亮点1", "核心亮点2"],
  "minus_points": ["潜在短板/风险1", "潜在短板/风险2"],
  "reasoning": "简短的总结性打分理由",
  "summary": "100字以内的情报摘要",
  "logic_trace": "核心数据/逻辑溯源点 (如：Page X, Table Y)"
}}
"""
