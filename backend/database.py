"""
Database configuration and session management.
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from .config import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Database Models
class Niche(Base):
    """틈새시장 정보"""
    __tablename__ = "niches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, nullable=False)
    search_volume = Column(Integer, default=0)
    competition_score = Column(Float, default=0.0)
    avg_price = Column(Float, default=0.0)
    trend_score = Column(Float, default=0.0)
    profit_potential_score = Column(Float, default=0.0)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    keywords = relationship("Keyword", back_populates="niche", cascade="all, delete-orphan")
    templates = relationship("CanvaTemplate", back_populates="niche")
    bestsellers = relationship("BestsellerTemplate", back_populates="niche")


class Keyword(Base):
    """키워드 분석 데이터"""
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, nullable=False, index=True)
    niche_id = Column(Integer, ForeignKey("niches.id"), nullable=False)
    search_volume = Column(Integer, default=0)
    competition = Column(Float, default=0.0)
    relevance_score = Column(Float, default=0.0)
    is_longtail = Column(Integer, default=0)  # SQLite doesn't have boolean
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    niche = relationship("Niche", back_populates="keywords")


class CanvaTemplate(Base):
    """Canva 템플릿 정보"""
    __tablename__ = "canva_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    template_link = Column(String, nullable=False)  # Canva Template Link URL
    niche_id = Column(Integer, ForeignKey("niches.id"), nullable=True)
    category = Column(String, nullable=True)
    preview_image_path = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    niche = relationship("Niche", back_populates="templates")
    pdfs = relationship("DeliveryPDF", back_populates="template", cascade="all, delete-orphan")
    listings = relationship("EtsyListing", back_populates="template")
    seo_contents = relationship("SEOContent", back_populates="template", cascade="all, delete-orphan")


class DeliveryPDF(Base):
    """생성된 Delivery PDF"""
    __tablename__ = "delivery_pdfs"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("canva_templates.id"), nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    template = relationship("CanvaTemplate", back_populates="pdfs")
    listings = relationship("EtsyListing", back_populates="pdf")


class EtsyListing(Base):
    """Etsy 리스팅 정보"""
    __tablename__ = "etsy_listings"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("canva_templates.id"), nullable=False)
    pdf_id = Column(Integer, ForeignKey("delivery_pdfs.id"), nullable=True)
    etsy_listing_id = Column(String, unique=True, index=True, nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    tags = Column(JSON, nullable=False)  # List of tags
    price = Column(Float, nullable=False)
    status = Column(String, default="draft")  # draft/published/sold_out
    views = Column(Integer, default=0)
    favorites = Column(Integer, default=0)
    sales = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    template = relationship("CanvaTemplate", back_populates="listings")
    pdf = relationship("DeliveryPDF", back_populates="listings")


class SEOContent(Base):
    """생성된 SEO 콘텐츠 (A/B 테스트용)"""
    __tablename__ = "seo_content"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("canva_templates.id"), nullable=False)
    version = Column(Integer, default=1)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    tags = Column(JSON, nullable=False)  # List of tags
    performance_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    template = relationship("CanvaTemplate", back_populates="seo_contents")


class BestsellerTemplate(Base):
    """Etsy 베스트셀러 템플릿 분석 데이터"""
    __tablename__ = "bestseller_templates"

    id = Column(Integer, primary_key=True, index=True)
    etsy_listing_id = Column(String, unique=True, index=True, nullable=False)
    niche_id = Column(Integer, ForeignKey("niches.id"), nullable=True)
    title = Column(String, nullable=False)
    seller_name = Column(String, nullable=True)
    sales_count = Column(Integer, default=0)  # 추정
    reviews_count = Column(Integer, default=0)
    avg_rating = Column(Float, default=0.0)
    price = Column(Float, default=0.0)
    image_url = Column(String, nullable=True)
    color_palette = Column(JSON, nullable=True)  # [{"color": "#3498db", "percentage": 25}]
    layout_data = Column(JSON, nullable=True)  # {"title_position": "top", "text_alignment": "center"}
    style = Column(String, nullable=True)  # minimal/bold/vintage/modern
    keywords = Column(JSON, nullable=True)  # ["editable", "printable"]
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    niche = relationship("Niche", back_populates="bestsellers")


# Dependency to get DB session
def get_db():
    """
    Dependency for FastAPI to get database session.
    Usage: def route_function(db: Session = Depends(get_db))
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create all tables
def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
