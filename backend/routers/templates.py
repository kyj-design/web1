"""
Templates Router - Canva 템플릿 관리 및 PDF 생성 API
"""
import os
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import CanvaTemplate, DeliveryPDF, get_db
from ..services.template_service import template_service

router = APIRouter()


# ── Pydantic 스키마 ──────────────────────────────────

class TemplateCreate(BaseModel):
    name: str
    template_link: str
    description: str = ""
    category: str = ""
    niche_id: Optional[int] = None


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    template_link: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    niche_id: Optional[int] = None


# ── 엔드포인트 ──────────────────────────────────────

@router.post("/")
def create_template(
    data: TemplateCreate,
    db: Session = Depends(get_db),
):
    """
    Canva 템플릿 등록.
    POST /api/templates/
    Body: {"name": "...", "template_link": "https://www.canva.com/...", ...}
    """
    if not data.name.strip():
        raise HTTPException(status_code=400, detail="Template name cannot be empty")
    if not data.template_link.strip():
        raise HTTPException(status_code=400, detail="Template link cannot be empty")

    template = template_service.create_template(
        name=data.name.strip(),
        template_link=data.template_link.strip(),
        description=data.description,
        category=data.category,
        niche_id=data.niche_id,
        db=db,
    )
    return template_service._template_to_dict(template)


@router.get("/")
def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    niche_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """
    템플릿 목록 조회 (카테고리/Niche 필터 지원).
    GET /api/templates/?category=Planner&niche_id=1
    """
    query = db.query(CanvaTemplate)
    if category:
        query = query.filter(CanvaTemplate.category == category)
    if niche_id:
        query = query.filter(CanvaTemplate.niche_id == niche_id)

    total = query.count()
    templates = (
        query.order_by(CanvaTemplate.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "templates": [template_service._template_to_dict(t) for t in templates],
    }


@router.get("/stats")
def get_template_stats(db: Session = Depends(get_db)):
    """
    대시보드용 템플릿 통계.
    GET /api/templates/stats
    """
    total = db.query(CanvaTemplate).count()
    total_pdfs = db.query(DeliveryPDF).count()

    # 카테고리별 분포
    from sqlalchemy import func
    category_dist = (
        db.query(CanvaTemplate.category, func.count(CanvaTemplate.id))
        .filter(CanvaTemplate.category.isnot(None))
        .group_by(CanvaTemplate.category)
        .all()
    )

    return {
        "total_templates": total,
        "total_pdfs": total_pdfs,
        "category_distribution": {cat: cnt for cat, cnt in category_dist},
    }


@router.get("/{template_id}")
def get_template(template_id: int, db: Session = Depends(get_db)):
    """
    템플릿 상세 조회 (PDF 목록 포함).
    GET /api/templates/{template_id}
    """
    template = db.query(CanvaTemplate).filter(CanvaTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template_service._template_to_dict(template, include_pdfs=True)


@router.put("/{template_id}")
def update_template(
    template_id: int,
    data: TemplateUpdate,
    db: Session = Depends(get_db),
):
    """
    템플릿 수정.
    PUT /api/templates/{template_id}
    """
    template = template_service.update_template(
        template_id=template_id,
        name=data.name,
        template_link=data.template_link,
        description=data.description,
        category=data.category,
        niche_id=data.niche_id,
        db=db,
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template_service._template_to_dict(template)


@router.delete("/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    """
    템플릿 삭제 (연관 PDF 파일도 삭제).
    DELETE /api/templates/{template_id}
    """
    success = template_service.delete_template(template_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": f"Template {template_id} deleted"}


@router.post("/{template_id}/upload-preview")
async def upload_preview(
    template_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    미리보기 이미지 업로드 (최대 10MB, JPG/PNG/WEBP).
    POST /api/templates/{template_id}/upload-preview
    Content-Type: multipart/form-data
    """
    try:
        path = await template_service.upload_preview_image(template_id, file, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not path:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "message": "Preview image uploaded successfully",
        "preview_image_url": template_service._get_image_url(path),
    }


@router.post("/{template_id}/generate-pdf")
def generate_pdf(template_id: int, db: Session = Depends(get_db)):
    """
    Delivery PDF 생성.
    POST /api/templates/{template_id}/generate-pdf

    매번 새 PDF를 생성하며 DB에 기록을 저장합니다.
    """
    pdf_record = template_service.generate_pdf(template_id, db)
    if not pdf_record:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "message": "PDF generated successfully",
        "pdf": template_service._pdf_to_dict(pdf_record),
    }


@router.get("/{template_id}/pdfs/{pdf_id}/download")
def download_pdf(
    template_id: int,
    pdf_id: int,
    db: Session = Depends(get_db),
):
    """
    PDF 파일 다운로드.
    GET /api/templates/{template_id}/pdfs/{pdf_id}/download
    """
    pdf_record = (
        db.query(DeliveryPDF)
        .filter(
            DeliveryPDF.id == pdf_id,
            DeliveryPDF.template_id == template_id,
        )
        .first()
    )
    if not pdf_record:
        raise HTTPException(status_code=404, detail="PDF not found")

    # Path traversal 방지: PDF 디렉토리 내부에만 접근 허용
    from ..config import settings as _settings
    pdf_dir = Path(_settings.pdf_dir).resolve()
    try:
        pdf_path = Path(pdf_record.file_path).resolve()
        pdf_path.relative_to(pdf_dir)
    except (ValueError, RuntimeError):
        raise HTTPException(status_code=403, detail="Access denied")

    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found on disk")

    template = db.query(CanvaTemplate).filter(CanvaTemplate.id == template_id).first()
    # 파일명 특수문자 제거
    raw_name = template.name if template else "delivery"
    safe_name = re.sub(r"[^\w\s-]", "", raw_name).strip().replace(" ", "_")
    filename = f"{safe_name}_delivery.pdf"

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=filename,
    )
