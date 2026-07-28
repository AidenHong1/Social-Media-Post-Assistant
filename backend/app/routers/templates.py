import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Template
from app.schemas import TemplateCreate, TemplateOut

router = APIRouter(prefix="/templates", tags=["templates"])


BUILTIN_TEMPLATES = [
    {
        "name": "产品发布公告",
        "description": "发布新产品或功能的正式公告模板",
        "category": "product_launch",
        "platform": "linkedin",
        "topic": "新产品发布",
        "key_points": ["产品核心功能", "解决的痛点", "目标用户群体", "可用性时间"],
        "brand_tone": "专业、兴奋",
    },
    {
        "name": "思想领导力分享",
        "description": "分享行业洞察和专业观点的模板",
        "category": "thought_leadership",
        "platform": "linkedin",
        "topic": "行业趋势分析",
        "key_points": ["趋势观察", "数据支持", "个人见解", "行动建议"],
        "brand_tone": "权威、启发性",
    },
    {
        "name": "职业里程碑",
        "description": "庆祝团队或个人职业成就的模板",
        "category": "career_milestone",
        "platform": "linkedin",
        "topic": "团队成就庆祝",
        "key_points": ["具体成就", "团队贡献", "感谢致辞", "未来展望"],
        "brand_tone": "感激、激励",
    },
    {
        "name": "活动预告",
        "description": "推广即将举行的活动或网络研讨会",
        "category": "event",
        "platform": "both",
        "topic": "活动邀请",
        "key_points": ["活动主题", "时间地点", "嘉宾亮点", "报名链接"],
        "brand_tone": "邀请性、期待",
    },
    {
        "name": "用户成功故事",
        "description": "展示客户案例和成功实践",
        "category": "social_proof",
        "platform": "linkedin",
        "topic": "客户案例分享",
        "key_points": ["客户背景", "面临挑战", "解决方案", "量化成果"],
        "brand_tone": "真实、鼓舞人心",
    },
    {
        "name": "幕后故事",
        "description": "分享团队日常和企业文化",
        "category": "behind_scenes",
        "platform": "facebook",
        "topic": "团队日常",
        "key_points": ["团队活动", "工作环境", "企业价值观", "团队成员"],
        "brand_tone": "亲切、真诚",
    },
    {
        "name": "社区互动帖",
        "description": "鼓励粉丝参与讨论和互动",
        "category": "engagement",
        "platform": "facebook",
        "topic": "话题讨论",
        "key_points": ["引发思考的问题", "开放式讨论", "鼓励分享", "互动号召"],
        "brand_tone": "友好、包容",
    },
    {
        "name": "年度总结",
        "description": "回顾全年成就和展望未来",
        "category": "year_review",
        "platform": "both",
        "topic": "年度回顾",
        "key_points": ["关键成就", "重要里程碑", "团队成长", "新年目标"],
        "brand_tone": "回顾、展望",
    },
]


def seed_builtin_templates(db: Session) -> None:
    """Seed built-in templates if none exist."""
    existing = db.query(Template).filter(Template.is_builtin == True).first()
    if existing:
        return

    for t in BUILTIN_TEMPLATES:
        template = Template(
            name=t["name"],
            description=t["description"],
            category=t["category"],
            platform=t["platform"],
            topic=t["topic"],
            key_points=json.dumps(t["key_points"], ensure_ascii=False),
            brand_tone=t["brand_tone"],
            is_builtin=True,
        )
        db.add(template)
    db.commit()


@router.get("", response_model=list[TemplateOut])
def get_templates(db: Session = Depends(get_db)):
    """List all templates (builtin + user-created)."""
    seed_builtin_templates(db)
    templates = db.query(Template).order_by(Template.is_builtin.desc(), Template.created_at.desc()).all()
    return [
        TemplateOut(
            id=t.id,
            name=t.name,
            description=t.description,
            category=t.category,
            platform=t.platform,
            topic=t.topic,
            key_points=json.loads(t.key_points),
            brand_tone=t.brand_tone,
            is_builtin=t.is_builtin,
            created_at=t.created_at,
        )
        for t in templates
    ]


@router.post("", response_model=TemplateOut, status_code=201)
def create_template(req: TemplateCreate, db: Session = Depends(get_db)):
    """Create a user-defined template."""
    template = Template(
        name=req.name,
        description=req.description,
        category=req.category,
        platform=req.platform,
        topic=req.topic,
        key_points=json.dumps(req.key_points, ensure_ascii=False),
        brand_tone=req.brand_tone,
        is_builtin=False,
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    return TemplateOut(
        id=template.id,
        name=template.name,
        description=template.description,
        category=template.category,
        platform=template.platform,
        topic=template.topic,
        key_points=json.loads(template.key_points),
        brand_tone=template.brand_tone,
        is_builtin=template.is_builtin,
        created_at=template.created_at,
    )


@router.delete("/{template_id}", status_code=204)
def delete_template(template_id: int, db: Session = Depends(get_db)):
    """Delete a user template (built-ins cannot be deleted)."""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(404, "Template not found")
    if template.is_builtin:
        raise HTTPException(403, "Cannot delete built-in templates")

    db.delete(template)
    db.commit()
