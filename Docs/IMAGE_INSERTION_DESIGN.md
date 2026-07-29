# 图片插入位置功能设计文档

## 需求概述

在现有图片生成功能基础上添加：
1. **自由选择插入位置**：字与字之间或段落之间任意位置
2. **多种插入方式**：任意位置可选人工上传或 AI 生成
3. **智能生成**：根据插入位置上下文智能生成最匹配的图片
4. **持久化保存**：插入的图片能准确保存并在对应位置正常显示

## 数据模型设计

### 方案选择

考虑两种方案：
- **方案A（关系表）**：新建 `variant_images` 表，每张图片一条记录
- **方案B（JSON字段）**：在 `variants` 表添加 `content_segments` JSON 字段

**选择方案A**，理由：
- 更易查询和管理单张图片（删除、更新）
- 支持未来扩展（如图片版本、编辑历史）
- 数据库规范化，避免 JSON 字段膨胀

### VariantImage 表结构

```sql
CREATE TABLE variant_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variant_id INTEGER NOT NULL,
    segment_index INTEGER NOT NULL,  -- 在 segments 数组中的位置
    image_url VARCHAR(500) NOT NULL,  -- /api/images/files/{filename} 或外链
    filename VARCHAR(255),            -- 本地文件名（如果是生成的图片）
    caption TEXT,                     -- 图片说明
    inserted_by VARCHAR(10) NOT NULL, -- 'manual' | 'ai'
    prompt_used TEXT,                 -- AI生成时使用的 prompt
    context_before TEXT,              -- 插入点前的上下文（用于智能生成）
    context_after TEXT,               -- 插入点后的上下文
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (variant_id) REFERENCES variants(id) ON DELETE CASCADE
);

CREATE INDEX idx_variant_images_variant ON variant_images(variant_id);
CREATE INDEX idx_variant_images_segment ON variant_images(variant_id, segment_index);
```

### 数据流转逻辑

#### 保存时
前端 `ContentSegment[]` → 后端拆分：
- Text segments: 合并为 `variant.final_text`（或保持原样）
- Image segments: 逐个插入 `variant_images` 表，记录 `segment_index`

#### 加载时
后端组装：
1. 读取 `variant.final_text`
2. 查询 `variant_images` 并按 `segment_index` 排序
3. 将文本按段落分割，在对应 `segment_index` 插入 image segments
4. 返回完整的 `ContentSegment[]` 给前端

## API 接口设计

### 1. 保存图文内容

```
PUT /api/variants/{variant_id}/content
```

**请求体**：
```json
{
  "segments": [
    { "type": "text", "content": "..." },
    {
      "type": "image",
      "url": "/api/images/files/abc123.png",
      "filename": "abc123.png",
      "caption": "图片说明",
      "insertedBy": "ai",
      "promptUsed": "描述...",
      "contextBefore": "前文...",
      "contextAfter": "后文..."
    },
    { "type": "text", "content": "..." }
  ]
}
```

**响应**：
```json
{
  "variant_id": 123,
  "segments": [...],  // 回显保存后的完整内容
  "updated_at": "2026-07-29T..."
}
```

### 2. 获取图文内容

```
GET /api/variants/{variant_id}/content
```

**响应**：
```json
{
  "variant_id": 123,
  "segments": [
    { "type": "text", "content": "..." },
    { "type": "image", "url": "...", "caption": "...", "insertedBy": "ai" },
    { "type": "text", "content": "..." }
  ]
}
```

### 3. 智能生成图片（基于上下文）

```
POST /api/images/generate-contextual
```

**请求体**：
```json
{
  "variant_id": 123,
  "context_before": "前100字符...",
  "context_after": "后100字符...",
  "user_prompt": "用户额外提示词（可选）",
  "size": "1024x1024"
}
```

**响应**：
```json
{
  "image_url": "/api/images/files/xyz789.png",
  "filename": "xyz789.png",
  "prompt_used": "根据上下文生成的完整 prompt",
  "caption": "智能生成的说明"
}
```

## 前端交互流程

### 现有 ContentEditor 增强

#### 1. 初始加载
```typescript
useEffect(() => {
  // 加载已保存的图文内容
  loadVariantContent(variantId).then(data => {
    if (data.segments && data.segments.length > 0) {
      setSegments(data.segments);
    } else {
      // 首次打开，只有文本
      setSegments([{ type: "text", content: finalText }]);
    }
  });
}, [variantId]);
```

#### 2. 保存按钮
在 ContentEditor 顶部添加"保存排版"按钮：
```tsx
<button onClick={handleSave} disabled={isSaving}>
  {isSaving ? "保存中..." : "保存排版"}
</button>
```

#### 3. 智能生成（基于上下文）
在 `ImageInsertPanel` 的 AI 生成 tab 添加"智能匹配上下文"选项：
```tsx
<label>
  <input type="checkbox" checked={useContext} onChange={...} />
  根据插入位置上下文智能生成
</label>
```

当勾选时，提取插入点前后文本作为 `context_before/after` 传给后端。

### 段落索引 vs 字符偏移

前端 `segments` 数组使用**数组索引**（`segment_index`）定位，优点：
- 简单直观，与前端数据结构一致
- 插入/删除时只需 splice 操作
- 后端存储时直接记录当前索引

字符偏移量方案更复杂（需处理文本变化、多字节字符），不采用。

## 后端实现要点

### 1. 保存逻辑（`routers/variants.py`）

```python
@router.put("/variants/{variant_id}/content")
async def save_variant_content(
    variant_id: int,
    req: SaveVariantContentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    variant = db.get(Variant, variant_id)
    if not variant:
        raise HTTPException(404, "Variant not found")
    
    # 删除旧的图片记录
    db.query(VariantImage).filter_by(variant_id=variant_id).delete()
    
    # 重新插入图片
    for idx, seg in enumerate(req.segments):
        if seg.type == "image":
            img = VariantImage(
                variant_id=variant_id,
                segment_index=idx,
                image_url=seg.url,
                filename=seg.filename,
                caption=seg.caption,
                inserted_by=seg.insertedBy,
                prompt_used=seg.promptUsed,
                context_before=seg.contextBefore,
                context_after=seg.contextAfter,
            )
            db.add(img)
    
    db.commit()
    
    # 返回完整内容
    return await load_variant_content(variant_id, db)
```

### 2. 加载逻辑

```python
@router.get("/variants/{variant_id}/content")
async def load_variant_content(variant_id: int, db: Session = Depends(get_db)):
    variant = db.get(Variant, variant_id)
    if not variant:
        raise HTTPException(404, "Variant not found")
    
    # 查询所有图片
    images = db.query(VariantImage).filter_by(variant_id=variant_id)\
               .order_by(VariantImage.segment_index).all()
    
    # 构建 segments
    segments = []
    text_parts = split_text_by_paragraphs(variant.final_text)
    
    img_by_index = {img.segment_index: img for img in images}
    max_index = max(img_by_index.keys()) if img_by_index else len(text_parts) - 1
    
    text_idx = 0
    for i in range(max_index + 1):
        if i in img_by_index:
            # 插入图片
            img = img_by_index[i]
            segments.append({
                "type": "image",
                "url": img.image_url,
                "caption": img.caption,
                "insertedBy": img.inserted_by,
                # ... 其他字段
            })
        else:
            # 插入文本
            if text_idx < len(text_parts):
                segments.append({
                    "type": "text",
                    "content": text_parts[text_idx]
                })
                text_idx += 1
    
    return {"variant_id": variant_id, "segments": segments}
```

### 3. 智能生成逻辑（`services/image_service.py`）

```python
async def generate_contextual_image(
    self,
    context_before: str,
    context_after: str,
    user_prompt: str = "",
    size: str = "1024x1024"
) -> dict:
    """基于上下文智能生成图片"""
    
    # 调用 LLM 分析上下文并生成 prompt
    system = "You are an expert at analyzing text context and generating image prompts."
    user_message = f"""
Context before insertion point:
{context_before[-200:]}  # 取最后200字符

Context after insertion point:
{context_after[:200]}  # 取前200字符

User hint (optional): {user_prompt}

Generate a detailed DALL-E image prompt that best matches this context.
Return JSON:
{{
  "image_prompt": "detailed English prompt",
  "caption": "short Chinese caption"
}}
"""
    
    # ... 调用 LLM
    analysis = await self._call_llm(system, user_message)
    
    # 合并用户提示词
    if user_prompt:
        analysis["image_prompt"] = f"{analysis['image_prompt']}, {user_prompt}"
    
    # 生成图片
    image_url, filename = await self.generate_image(
        prompt=analysis["image_prompt"],
        size=size
    )
    
    return {
        "image_url": image_url,
        "filename": filename,
        "prompt_used": analysis["image_prompt"],
        "caption": analysis["caption"]
    }
```

## 数据库迁移策略

由于项目没有 Alembic，采用手动迁移：

1. 创建 `backend/migrations/001_add_variant_images.sql`
2. 在应用启动时检测表是否存在，不存在则执行迁移
3. 或提供独立脚本供用户手动执行

```python
# backend/app/main.py
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    
    # 检查并创建 variant_images 表
    from app.db import engine
    with engine.begin() as conn:
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='variant_images'"
        ))
        if not result.fetchone():
            # 执行迁移
            migration_sql = Path("migrations/001_add_variant_images.sql").read_text()
            conn.execute(text(migration_sql))
```

## 前端状态管理优化

当前 ContentEditor 使用纯 `useState`，保存后需要：
- 在保存成功后更新本地 `segments` 状态
- 在 VariantCard 父组件缓存已保存的内容，切换回来时直接使用缓存

```typescript
// VariantCard.tsx
const [cachedSegments, setCachedSegments] = useState<ContentSegment[] | null>(null);

<ContentEditor
  variantId={variant.id}
  finalText={variant.final_text}
  initialSegments={cachedSegments}
  onSaved={(segments) => setCachedSegments(segments)}
/>
```

## 兼容性考虑

### 旧数据兼容
- 已有 variants 没有图片记录 → 加载时返回纯文本 segment
- 前端首次打开编辑器 → 从 `final_text` 初始化

### 降级方案
如果用户不保存，功能退化为当前的纯前端状态（刷新即丢失），不影响现有流程。

## 实现优先级

### P0（核心功能）
1. ✅ 数据模型和表结构
2. ✅ 保存/加载 API
3. ✅ 前端保存按钮和持久化

### P1（增强功能）
4. 智能上下文生成
5. 前端缓存优化

### P2（可选优化）
6. 图片编辑历史
7. 批量操作（删除所有图片）

## 测试计划

1. **插入测试**：在不同位置手动/AI插入图片
2. **保存测试**：保存后刷新页面，图片仍在
3. **加载测试**：切换到其他 variant 再切回，图片正确显示
4. **上下文生成测试**：验证生成的图片与上下文匹配
5. **边界测试**：
   - 空文本插入图片
   - 只有图片没有文本
   - 大量图片（10+张）

## 时间估算

- 后端开发：2-3 小时
- 前端开发：2-3 小时
- 测试和调试：1-2 小时
- 总计：**5-8 小时**
