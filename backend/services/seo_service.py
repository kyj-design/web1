"""
SEO Service - LLM 기반 Etsy 리스팅 SEO 콘텐츠 생성
Ollama(로컬) 또는 OpenAI를 사용하여 제목/태그/설명을 생성합니다.
"""
import json
import logging
import re
import httpx
from typing import Optional
from sqlalchemy.orm import Session

from ..config import settings
from ..database import CanvaTemplate, SEOContent, Keyword

logger = logging.getLogger(__name__)

# Etsy 태그 제한: 최대 13개, 각 20자 이하
MAX_TAGS = 13
MAX_TAG_LENGTH = 20
# Etsy 제목 제한: 140자 이하
MAX_TITLE_LENGTH = 140

SYSTEM_PROMPT = """You are an expert Etsy SEO copywriter specializing in digital products and Canva templates.
Your job is to write highly searchable, buyer-focused Etsy listing content that:
1. Uses high-traffic, buyer-intent keywords naturally
2. Follows Etsy's search algorithm (keyword front-loading in title)
3. Sounds conversational and appealing, not keyword-stuffed
4. Maximizes click-through rate and conversion"""

def _build_user_prompt(
    template_name: str,
    category: str,
    niche: str,
    keywords: list[str],
    description: str,
) -> str:
    kw_str = ", ".join(keywords[:15]) if keywords else "(none provided)"
    return f"""Create an Etsy listing for a Canva digital template:

Template Name: {template_name}
Category: {category or "Digital Template"}
Niche: {niche or "General"}
Description: {description or "(none)"}
Top Keywords to incorporate: {kw_str}

Return ONLY valid JSON (no markdown fences) in this exact format:
{{
  "title": "Etsy title here (max 140 chars, front-load top keywords)",
  "description": "Full Etsy listing description (300-500 words). Include what it is, what's included, how to use, who it's for. Use line breaks for readability.",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9", "tag10", "tag11", "tag12", "tag13"],
  "seo_score": 85
}}

Rules for tags: exactly 13 tags, each max 20 characters, no special characters, lowercase preferred.
Rules for title: max 140 characters, start with the most important keyword."""


def _fallback_content(template_name: str, category: str, keywords: list[str]) -> dict:
    """LLM 실패 시 기본 콘텐츠 생성"""
    top_kws = keywords[:3] if keywords else ["digital template", "printable", "editable"]
    title = f"{top_kws[0].title()} Template | {template_name} | Canva Editable"[:MAX_TITLE_LENGTH]

    desc = (
        f"Introducing the {template_name} – a professionally designed Canva template "
        f"perfect for anyone looking for a high-quality {category or 'digital'} product.\n\n"
        "✅ WHAT'S INCLUDED:\n"
        "• Instant digital download\n"
        "• Fully editable Canva template link\n"
        "• Easy to customize – no design skills required\n\n"
        "✏️ HOW TO USE:\n"
        "1. Click the template link in the PDF\n"
        "2. Open in Canva (free account works!)\n"
        "3. Edit text, colors, and images to match your style\n"
        "4. Download in any format\n\n"
        "⭐ WHY YOU'LL LOVE IT:\n"
        "• Saves hours of design time\n"
        "• Professional, modern design\n"
        "• Commercial use included\n\n"
        "Questions? Message us anytime. We're happy to help!"
    )

    raw_tags = [k.lower()[:MAX_TAG_LENGTH] for k in (keywords[:10] + ["canva template", "digital download", "printable"])]
    tags = list(dict.fromkeys(raw_tags))[:MAX_TAGS]

    return {"title": title, "description": desc, "tags": tags, "seo_score": 60.0}


class SEOService:
    """LLM 기반 SEO 콘텐츠 생성 서비스"""

    def __init__(self):
        self.provider = settings.llm_provider
        self.use_openai = (
            self.provider == "openai" and
            settings.openai_api_key and
            settings.openai_api_key != "your_openai_api_key_here"
        )

    async def generate_seo_content(
        self,
        template_id: int,
        db: Session,
        version: Optional[int] = None,
    ) -> SEOContent:
        """
        템플릿에 대한 SEO 콘텐츠를 LLM으로 생성 후 DB 저장.
        반환: SEOContent 레코드
        """
        template = db.query(CanvaTemplate).filter(CanvaTemplate.id == template_id).first()
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Niche에 연결된 키워드 수집
        keywords = []
        if template.niche_id:
            from ..database import Keyword
            kws = (
                db.query(Keyword)
                .filter(Keyword.niche_id == template.niche_id)
                .order_by(Keyword.search_volume.desc())
                .limit(15)
                .all()
            )
            keywords = [k.keyword for k in kws]

        # LLM으로 콘텐츠 생성
        raw = await self._call_llm(
            template_name=template.name,
            category=template.category or "",
            niche=template.niche.name if template.niche else "",
            keywords=keywords,
            description=template.description or "",
        )

        # 버전 번호 결정
        if version is None:
            existing = (
                db.query(SEOContent)
                .filter(SEOContent.template_id == template_id)
                .count()
            )
            version = existing + 1

        # 태그 정규화
        tags = self._normalize_tags(raw.get("tags", []))
        title = raw.get("title", "")[:MAX_TITLE_LENGTH]

        record = SEOContent(
            template_id=template_id,
            version=version,
            title=title,
            description=raw.get("description", ""),
            tags=tags,
            performance_score=float(raw.get("seo_score", 60)),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    async def _call_llm(self, **kwargs) -> dict:
        """Ollama 또는 OpenAI 호출, 실패 시 fallback"""
        try:
            if self.use_openai:
                return await self._call_openai(**kwargs)
            else:
                return await self._call_ollama(**kwargs)
        except Exception as e:
            logger.warning(f"LLM call failed ({e}). Using fallback content.")
            return _fallback_content(
                kwargs["template_name"], kwargs["category"], kwargs["keywords"]
            )

    async def _call_ollama(self, template_name, category, niche, keywords, description) -> dict:
        """Ollama 로컬 LLM 호출"""
        prompt = _build_user_prompt(template_name, category, niche, keywords, description)
        payload = {
            "model": settings.ollama_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/chat",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["message"]["content"]
        return self._parse_json_response(text, template_name, category, keywords)

    async def _call_openai(self, template_name, category, niche, keywords, description) -> dict:
        """OpenAI API 호출"""
        import openai
        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        prompt = _build_user_prompt(template_name, category, niche, keywords, description)
        resp = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1200,
        )
        text = resp.choices[0].message.content
        return self._parse_json_response(text, template_name, category, keywords)

    def _parse_json_response(self, text: str, template_name: str, category: str, keywords: list) -> dict:
        """LLM 응답에서 JSON 파싱 (마크다운 블록 제거 포함)"""
        # ```json ... ``` 또는 ``` ... ``` 제거
        cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().strip("`").strip()
        # 첫 번째 { ~ 마지막 } 추출
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON object found in LLM response")
        json_str = cleaned[start:end]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON from LLM: {json_str[:200]}")

    def _normalize_tags(self, tags: list) -> list[str]:
        """태그 정규화: 20자 절단, 특수문자 제거, 중복 제거, 정확히 13개로 패딩"""
        _FALLBACK_TAGS = [
            "canva template", "digital download", "instant download",
            "printable", "editable template", "digital product",
            "commercial use", "digital file", "canva design",
            "edit template", "diy template", "digital art", "pdf template",
        ]
        cleaned = []
        seen = set()
        for t in tags:
            tag = re.sub(r"[^a-z0-9 '-]", "", str(t).lower().strip())[:MAX_TAG_LENGTH].strip()
            if tag and tag not in seen:
                seen.add(tag)
                cleaned.append(tag)
            if len(cleaned) >= MAX_TAGS:
                break
        # LLM이 13개 미만을 반환한 경우 fallback으로 채움
        for ft in _FALLBACK_TAGS:
            if len(cleaned) >= MAX_TAGS:
                break
            if ft not in seen:
                seen.add(ft)
                cleaned.append(ft)
        return cleaned

    def seo_to_dict(self, seo: SEOContent) -> dict:
        return {
            "id": seo.id,
            "template_id": seo.template_id,
            "version": seo.version,
            "title": seo.title,
            "description": seo.description,
            "tags": seo.tags,
            "performance_score": seo.performance_score,
            "created_at": seo.created_at.isoformat() if seo.created_at else None,
            "char_count": {
                "title": len(seo.title),
                "description": len(seo.description),
                "tags": len(seo.tags),
            },
        }


# 싱글턴 인스턴스
seo_service = SEOService()
