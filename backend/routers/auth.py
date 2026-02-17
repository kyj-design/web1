"""
Auth Router - Etsy OAuth 2.0 PKCE 인증 엔드포인트
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.etsy_oauth_service import etsy_oauth_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/status")
def get_auth_status(db: Session = Depends(get_db)):
    """
    현재 Etsy OAuth 인증 상태 반환.
    프론트엔드 Settings 페이지에서 연결 여부 확인용.
    """
    return etsy_oauth_service.get_auth_status(db)


@router.get("/etsy/login")
def etsy_login():
    """
    Etsy OAuth 인증 URL 생성.
    반환된 auth_url로 사용자를 리다이렉트하면 Etsy 로그인 화면이 표시됩니다.
    """
    result = etsy_oauth_service.generate_auth_url()
    return result


@router.get("/etsy/callback")
async def etsy_callback(
    code: str = Query(..., description="Etsy에서 반환된 인증 코드"),
    state: str = Query(..., description="PKCE state 파라미터"),
    error: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """
    Etsy OAuth callback 처리.
    - code + state 수신 → access_token 교환 → DB 저장
    - 성공 시 프론트엔드 /settings?etsy_connected=true 로 리다이렉트
    - 실패 시 /settings?error=... 로 리다이렉트
    """
    from ..config import settings as cfg

    frontend_settings = cfg.frontend_url.rstrip("/") + "/settings"

    # 사용자가 Etsy 인증을 거부한 경우
    if error:
        logger.warning(f"Etsy OAuth denied by user: {error}")
        return RedirectResponse(url=f"{frontend_settings}?error={error}")

    try:
        token = await etsy_oauth_service.handle_callback(code, state, db)
        logger.info(f"Etsy OAuth completed: shop={token.shop_name or 'unknown'}")
        return RedirectResponse(
            url=f"{frontend_settings}?etsy_connected=true"
        )
    except ValueError as e:
        logger.error(f"OAuth callback error: {e}")
        return RedirectResponse(
            url=f"{frontend_settings}?error=oauth_failed"
        )
    except Exception as e:
        logger.error(f"OAuth callback unexpected error: {e}")
        return RedirectResponse(
            url=f"{frontend_settings}?error=server_error"
        )


@router.delete("/etsy/disconnect")
def etsy_disconnect(db: Session = Depends(get_db)):
    """
    Etsy 연결 해제: 저장된 OAuth 토큰 삭제.
    """
    etsy_oauth_service.revoke_token(db)
    return {"message": "Etsy account disconnected successfully."}


@router.post("/etsy/refresh")
async def etsy_refresh_token(db: Session = Depends(get_db)):
    """
    수동으로 access_token 갱신 (테스트/디버그용).
    """
    token = await etsy_oauth_service.refresh_access_token(db)
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Token refresh failed. Please reconnect your Etsy account.",
        )
    return {
        "message": "Token refreshed successfully.",
        "expires_at": token.expires_at.isoformat() if token.expires_at else None,
    }
