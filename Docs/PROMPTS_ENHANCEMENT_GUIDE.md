# 智能体写作技能优化指南

## 📋 优化概述

基于 `Docs/写作技巧.md` 中的高流量社交媒体写作原则,创建了增强版的prompts系统 (`prompts_enhanced.py`),融入以下核心策略:

### 核心改进点

1. **平台差异化策略**
   - LinkedIn: 职业价值、行业洞察、方法论、案例复盘
   - Facebook: 情绪共鸣、生活化表达、社群互动、故事传播

2. **强开头设计**
   - 反常识开头
   - 明确结果展示
   - 真实经历分享
   - 情绪共鸣触发

3. **高信息密度要求**
   - 每句话必须提供新价值
   - 避免空泛内容和鸡汤
   - 提供可引用、可分享的信息

4. **互动设计优化**
   - 结尾必须包含明确的互动提示
   - 设计讨论触发点
   - 降低评论门槛

5. **增强的评审标准**
   - Hook强度评估
   - 信息密度检查
   - 互动设计验证
   - 平台适配度判断
   - 避免广告化内容

## 🔄 如何应用优化

### 方案 1: 直接替换(推荐用于新项目)

```bash
# 备份原文件
cp backend/app/pipeline/prompts.py backend/app/pipeline/prompts_original.py

# 替换为增强版
cp backend/app/pipeline/prompts_enhanced.py backend/app/pipeline/prompts.py
```

### 方案 2: 并行测试(推荐用于生产环境)

在 `generate.py` 和 `critique.py` 中添加切换逻辑:

```python
# 在 generate.py 中
from app.pipeline.prompts_enhanced import build_generation_prompt as build_generation_prompt_v2

def generate_draft_v2(
    llm: LLMClient,
    topic: str,
    key_points: list[str],
    brand_tone: str,
    constraints: PlatformConstraints,
    kb_context: str = "",
) -> str:
    system, user = build_generation_prompt_v2(topic, key_points, brand_tone, constraints, kb_context)
    return llm.chat(system, user).strip()
```

### 方案 3: 渐进式迁移

1. 先替换 `build_generation_prompt` - 优化内容生成
2. 再替换 `build_critique_prompt` - 提升评审标准
3. 最后替换 `build_rewrite_prompt` - 完善重写逻辑

## 📊 预期效果

### LinkedIn 内容
- ✅ 更强的专业价值感
- ✅ 更高的可引用性
- ✅ 更多的行业讨论
- ✅ 更符合职业用户的分享动机

### Facebook 内容
- ✅ 更强的情绪连接
- ✅ 更高的共鸣度
- ✅ 更多的互动评论
- ✅ 更符合社交分享场景

### 通用改进
- ✅ 开头停留率提升
- ✅ 完读率提升
- ✅ 互动率提升
- ✅ 分享率提升
- ✅ 降低广告感

## 🧪 测试建议

### A/B 测试方案

```python
# 在 orchestrator.py 中添加版本标记
def generate_with_ab_test(use_enhanced: bool = False):
    if use_enhanced:
        from app.pipeline.prompts_enhanced import build_generation_prompt
    else:
        from app.pipeline.prompts import build_generation_prompt
    
    # 继续生成逻辑...
```

### 评估指标

1. **内容质量指标**
   - 开头吸引力(人工评分 1-5)
   - 信息密度(人工评分 1-5)
   - 互动提示清晰度(是/否)

2. **平台表现指标**(需要实际发布后测量)
   - 展示量(Impressions)
   - 互动率(Engagement Rate)
   - 点击率(CTR)
   - 分享次数(Shares)
   - 评论数量(Comments)

3. **品牌一致性**
   - 是否符合品牌调性
   - 是否过度营销
   - 是否保持人性化

## 📝 关键差异对比

### 原版 vs 增强版

| 维度 | 原版 | 增强版 |
|------|------|--------|
| 平台策略 | 通用 | LinkedIn/Facebook 差异化 |
| 开头设计 | 无明确要求 | 必须使用强hook模式 |
| 信息密度 | 基础要求 | 每句话价值验证 |
| 互动设计 | 可选 | 必须包含明确CTA |
| 评审标准 | 基础检查 | 5维度深度评估 |
| 避免事项 | 简单列举 | 详细反面教材 |

## 🎯 使用场景建议

### 适合使用增强版的场景
- ✅ 需要高互动率的品牌内容
- ✅ 追求病毒式传播的营销活动
- ✅ 建立个人IP或企业思想领导力
- ✅ 需要快速增长粉丝和影响力

### 继续使用原版的场景
- ⚠️ 纯信息发布(公告、通知)
- ⚠️ 对内容调性有严格限制的行业
- ⚠️ 更注重严肃性而非传播性的内容

## 🔧 后续优化方向

1. **添加内容类型模板**
   - 行业洞察模板
   - 案例复盘模板
   - 故事叙事模板
   - 清单干货模板

2. **增加实时反馈机制**
   - 集成平台API获取真实数据
   - 基于表现数据自动优化prompt

3. **多语言适配**
   - 针对不同语言市场的写作习惯
   - 文化差异下的互动模式

4. **行业垂直优化**
   - SaaS行业专用版本
   - 电商行业专用版本
   - 教育行业专用版本

## 💡 最佳实践

1. **初始测试**: 先用小样本测试(10-20篇内容)
2. **人工审核**: 前期保持人工审核环节
3. **数据追踪**: 记录每篇内容的表现数据
4. **迭代优化**: 根据数据反馈调整prompt参数
5. **保持更新**: 定期更新写作技巧知识库

## 📚 参考资源

- 原始写作技巧文档: `Docs/写作技巧.md`
- 增强版prompts实现: `backend/app/pipeline/prompts_enhanced.py`
- 原版prompts对比: `backend/app/pipeline/prompts.py`

---

**创建日期**: 2026-07-27  
**版本**: v1.0  
**作者**: AI智能体优化项目
