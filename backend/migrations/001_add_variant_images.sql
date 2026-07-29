-- 添加 variant_images 表用于存储图片插入信息
CREATE TABLE IF NOT EXISTS variant_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variant_id INTEGER NOT NULL,
    segment_index INTEGER NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    filename VARCHAR(255),
    caption TEXT,
    inserted_by VARCHAR(10) NOT NULL,
    prompt_used TEXT,
    context_before TEXT,
    context_after TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (variant_id) REFERENCES variants(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_variant_images_variant ON variant_images(variant_id);
CREATE INDEX IF NOT EXISTS idx_variant_images_segment ON variant_images(variant_id, segment_index);
