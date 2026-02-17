"""
Template Service - Canva 템플릿 CRUD 및 미리보기 이미지 업로드
"""
import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from ..config import settings
from ..database import CanvaTemplate, DeliveryPDF, Niche
from .pdf_service import pdf_service

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


class TemplateService:
    """Canva 템플릿 관리 서비스 (생성/수정/삭제/이미지 업로드/PDF 생성)"""

    def __init__(self):
        self.image_dir = Path(settings.image_dir)
        self.image_dir.mkdir(parents=True, exist_ok=True)

    # ── CRUD ──────────────────────────────────────

    def create_template(
        self,
        name: str,
        template_link: str,
        description: str = "",
        category: str = "",
        niche_id: Optional[int] = None,
        db: Session = None,
    ) -> CanvaTemplate:
        """템플릿 생성"""
        # Niche 존재 확인
        if niche_id and db:
            niche = db.query(Niche).filter(Niche.id == niche_id).first()
            if not niche:
                niche_id = None

        template = CanvaTemplate(
            name=name,
            template_link=template_link,
            description=description,
            category=category,
            niche_id=niche_id,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        logger.info(f"Template created: {template.id} - {template.name}")
        return template

    def update_template(
        self,
        template_id: int,
        name: Optional[str] = None,
        template_link: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        niche_id: Optional[int] = None,
        db: Session = None,
    ) -> Optional[CanvaTemplate]:
        """템플릿 수정 (None 값은 변경하지 않음)"""
        template = db.query(CanvaTemplate).filter(CanvaTemplate.id == template_id).first()
        if not template:
            return None

        if name is not None:
            template.name = name
        if template_link is not None:
            template.template_link = template_link
        if description is not None:
            template.description = description
        if category is not None:
            template.category = category
        if niche_id is not None:
            niche = db.query(Niche).filter(Niche.id == niche_id).first()
            template.niche_id = niche_id if niche else template.niche_id

        db.commit()
        db.refresh(template)
        return template

    def delete_template(self, template_id: int, db: Session) -> bool:
        """템플릿 삭제 (연관된 PDF 파일도 삭제)"""
        template = db.query(CanvaTemplate).filter(CanvaTemplate.id == template_id).first()
        if not template:
            return False

        # 연관된 PDF 파일 삭제
        for pdf in template.pdfs:
            if pdf.file_path and os.path.exists(pdf.file_path):
                try:
                    os.remove(pdf.file_path)
                except OSError as e:
                    logger.warning(f"Failed to delete PDF file {pdf.file_path}: {e}")

        # 미리보기 이미지 파일 삭제
        if template.preview_image_path and os.path.exists(template.preview_image_path):
            try:
                os.remove(template.preview_image_path)
            except OSError as e:
                logger.warning(f"Failed to delete preview image: {e}")

        db.delete(template)
        db.commit()
        logger.info(f"Template deleted: {template_id}")
        return True

    # ── 미리보기 이미지 업로드 ──────────────────────

    async def upload_preview_image(
        self,
        template_id: int,
        file: UploadFile,
        db: Session,
    ) -> Optional[str]:
        """
        미리보기 이미지 업로드 후 경로 반환.
        기존 이미지가 있으면 덮어씁니다.
        """
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise ValueError(f"Unsupported image type: {file.content_type}")

        template = db.query(CanvaTemplate).filter(CanvaTemplate.id == template_id).first()
        if not template:
            return None

        # 파일 크기 검사
        content = await file.read()
        if len(content) > MAX_IMAGE_SIZE:
            raise ValueError("Image file size exceeds 10 MB limit")

        # 파일 저장
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
        filename = f"template_{template_id}_{uuid.uuid4().hex[:8]}.{ext}"
        save_path = self.image_dir / filename

        # 기존 이미지 삭제
        if template.preview_image_path and os.path.exists(template.preview_image_path):
            try:
                os.remove(template.preview_image_path)
            except OSError:
                pass

        with open(save_path, "wb") as f:
            f.write(content)

        # DB 업데이트
        template.preview_image_path = str(save_path)
        db.commit()
        db.refresh(template)

        logger.info(f"Preview image uploaded for template {template_id}: {save_path}")
        return str(save_path)

    # ── PDF 생성 ───────────────────────────────────

    def generate_pdf(self, template_id: int, db: Session) -> Optional[DeliveryPDF]:
        """
        Delivery PDF 생성 후 DeliveryPDF 레코드 반환.
        매 호출마다 새 PDF를 생성합니다.
        """
        template = db.query(CanvaTemplate).filter(CanvaTemplate.id == template_id).first()
        if not template:
            return None

        filepath = pdf_service.generate_delivery_pdf(
            template_id=template.id,
            template_name=template.name,
            template_link=template.template_link,
            description=template.description or "",
            category=template.category or "",
        )

        file_size = os.path.getsize(filepath)

        pdf_record = DeliveryPDF(
            template_id=template.id,
            file_path=filepath,
            file_size=file_size,
        )
        db.add(pdf_record)
        db.commit()
        db.refresh(pdf_record)

        logger.info(f"PDF created for template {template_id}: {filepath} ({file_size} bytes)")
        return pdf_record

    # ── 직렬화 헬퍼 ───────────────────────────────

    def _template_to_dict(self, t: CanvaTemplate, include_pdfs: bool = False) -> dict:
        d = {
            "id": t.id,
            "name": t.name,
            "template_link": t.template_link,
            "description": t.description,
            "category": t.category,
            "niche_id": t.niche_id,
            "niche_name": t.niche.name if t.niche else None,
            "preview_image_path": t.preview_image_path,
            "preview_image_url": self._get_image_url(t.preview_image_path),
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            "pdf_count": len(t.pdfs),
        }
        if include_pdfs:
            d["pdfs"] = [self._pdf_to_dict(p) for p in t.pdfs]
        return d

    def _pdf_to_dict(self, p: DeliveryPDF) -> dict:
        return {
            "id": p.id,
            "template_id": p.template_id,
            "file_path": p.file_path,
            "file_size": p.file_size,
            "file_size_kb": round(p.file_size / 1024, 1) if p.file_size else 0,
            "generated_at": p.generated_at.isoformat() if p.generated_at else None,
            "download_url": f"/api/templates/{p.template_id}/pdfs/{p.id}/download",
        }

    def _get_image_url(self, path: Optional[str]) -> Optional[str]:
        """파일 경로를 정적 URL로 변환"""
        if not path:
            return None
        # backend/static/images/xxx.jpg → /static/images/xxx.jpg
        try:
            rel = Path(path).relative_to(Path("backend/static"))
            return f"/static/{rel}"
        except ValueError:
            return None


# 싱글턴 인스턴스
template_service = TemplateService()
