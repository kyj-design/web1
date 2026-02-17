"""
Image Analysis Service - PIL + scikit-learn K-means 색상 팔레트 추출
"""
import io
import logging
from typing import Optional

import httpx
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)


class ImageAnalysisService:
    """
    이미지 다운로드 및 색상/레이아웃 분석 서비스.
    """

    def __init__(self, n_colors: int = 5):
        self.n_colors = n_colors

    async def download_and_analyze(self, image_url: str) -> dict:
        """
        URL에서 이미지 다운로드 후 전체 분석 수행.
        반환 형식:
          {
            "color_palette": [{"color": "#3498db", "percentage": 25.3}, ...],
            "dominant_style": "minimal" | "bold" | "vintage" | "modern",
            "layout_data": {"brightness": 0.7, "contrast": 0.5, ...},
            "success": True
          }
        """
        try:
            image = await self._download_image(image_url)
            if image is None:
                return self._empty_analysis()

            color_palette = self.extract_color_palette(image)
            style = self.classify_style(color_palette, image)
            layout = self.analyze_layout(image)

            return {
                "color_palette": color_palette,
                "dominant_style": style,
                "layout_data": layout,
                "success": True,
            }
        except Exception as e:
            logger.error(f"Image analysis failed for {image_url}: {e}")
            return self._empty_analysis()

    async def _download_image(self, url: str) -> Optional[Image.Image]:
        """비동기 이미지 다운로드"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return Image.open(io.BytesIO(resp.content)).convert("RGB")

    def extract_color_palette(self, image: Image.Image) -> list:
        """
        K-means 클러스터링으로 대표 색상 팔레트 추출.
        1. 이미지를 100x100으로 리사이즈 (성능)
        2. 픽셀 배열로 변환
        3. KMeans(n_clusters=self.n_colors) 피팅
        4. 클러스터 중심값 → HEX 색상 변환
        5. 각 클러스터의 비율(%) 계산
        """
        small = image.resize((100, 100))
        pixels = np.array(small).reshape(-1, 3)

        kmeans = KMeans(n_clusters=self.n_colors, random_state=42, n_init=10)
        kmeans.fit(pixels)

        centers = kmeans.cluster_centers_.astype(int)
        labels = kmeans.labels_
        total = len(labels)

        palette = []
        for i, center in enumerate(centers):
            count = int(np.sum(labels == i))
            hex_color = "#{:02x}{:02x}{:02x}".format(
                int(center[0]), int(center[1]), int(center[2])
            )
            palette.append({
                "color": hex_color,
                "percentage": round(count / total * 100, 1),
            })

        return sorted(palette, key=lambda x: x["percentage"], reverse=True)

    def classify_style(self, color_palette: list, image: Image.Image) -> str:
        """
        색상 팔레트 기반 스타일 분류.
        - minimal: 밝고 채도 낮음 (흰색, 회색 계열 주도)
        - bold: 채도 높음, 강한 대비
        - vintage: 갈색/베이지 계열, 낮은 채도
        - modern: 모노톤 + 포인트 컬러
        """
        if not color_palette:
            return "minimal"

        dominant_hex = color_palette[0]["color"]
        r = int(dominant_hex[1:3], 16)
        g = int(dominant_hex[3:5], 16)
        b = int(dominant_hex[5:7], 16)

        brightness = (r * 0.299 + g * 0.587 + b * 0.114) / 255
        saturation = (max(r, g, b) - min(r, g, b)) / 255

        if brightness > 0.8 and saturation < 0.2:
            return "minimal"
        elif saturation > 0.6:
            return "bold"
        elif r > g and r > b and brightness < 0.6:
            return "vintage"
        else:
            return "modern"

    def analyze_layout(self, image: Image.Image) -> dict:
        """
        이미지에서 레이아웃 메타데이터 추출.
        """
        gray = image.convert("L")
        pixels = np.array(gray) / 255.0
        return {
            "brightness": round(float(pixels.mean()), 3),
            "contrast": round(float(pixels.std()), 3),
            "aspect_ratio": round(image.width / image.height, 2),
            "width": image.width,
            "height": image.height,
        }

    def _empty_analysis(self) -> dict:
        return {
            "color_palette": [],
            "dominant_style": "unknown",
            "layout_data": {},
            "success": False,
        }


# 싱글턴 인스턴스
image_analysis_service = ImageAnalysisService(n_colors=5)
