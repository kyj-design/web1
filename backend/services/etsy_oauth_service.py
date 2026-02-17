"""
Etsy OAuth 2.0 PKCE 서비스
- Authorization Code + PKCE (RFC 7636) 흐름 구현
- 단일 사용자: 항상 최신 토큰 레코드 1개만 유지
"""
import base64
import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from ..config import settings
from ..database import OAuthToken

logger = logging.getLogger(__name__)

ETSY_AUTH_URL = "https://www.etsy.com/oauth/connect"
ETSY_TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"
ETSY_SCOPES = "listings_r listings_w shops_r shops_w"

# 임시 PKCE 상태 저장 (프로세스 메모리, 단일 사용자이므로 충분)
_pending_oauth: dict = {}   # {"state": {"code_verifier": ..., "created_at": ...}}


def _generate_code_verifier() -> str:
    """PKCE code_verifier: 43-128자의 URL-safe random string"""
    return secrets.token_urlsafe(64)


def _generate_code_challenge(verifier: str) -> str:
    """PKCE code_challenge: base64url(sha256(code_verifier))"""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


class EtsyOAuthService:
    """Etsy OAuth 2.0 PKCE 흐름 처리"""

    def generate_auth_url(self) -> dict:
        """
        Etsy 인증 URL 생성.
        반환: {"auth_url": str, "state": str}
        """
        state = secrets.token_urlsafe(32)
        code_verifier = _generate_code_verifier()
        code_challenge = _generate_code_challenge(code_verifier)

        # 임시 저장 (callback에서 code_verifier 필요)
        _pending_oauth[state] = {
            "code_verifier": code_verifier,
            "created_at": datetime.utcnow(),
        }

        params = {
            "response_type": "code",
            "redirect_uri": settings.etsy_callback_url,
            "scope": ETSY_SCOPES,
            "client_id": settings.etsy_api_key,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        from urllib.parse import urlencode
        auth_url = f"{ETSY_AUTH_URL}?{urlencode(params)}"
        logger.info(f"Generated Etsy OAuth URL for state={state[:8]}...")
        return {"auth_url": auth_url, "state": state}

    async def handle_callback(
        self, code: str, state: str, db: Session
    ) -> OAuthToken:
        """
        OAuth callback 처리: code ↔ token 교환 후 DB 저장.
        """
        pending = _pending_oauth.pop(state, None)
        if not pending:
            raise ValueError("Invalid or expired OAuth state. Please try again.")

        # 5분 이상 지난 state는 거부
        age = (datetime.utcnow() - pending["created_at"]).total_seconds()
        if age > 300:
            raise ValueError("OAuth state expired (>5 min). Please try again.")

        token_data = await self._exchange_code(code, pending["code_verifier"])
        token = self._save_token(token_data, db)
        # shop_id 조회는 비동기로 처리 (이벤트 루프 블로킹 방지)
        await self._fetch_and_update_shop_info(token, db)
        return token

    async def _exchange_code(self, code: str, code_verifier: str) -> dict:
        """Etsy token endpoint에 code 교환 요청"""
        payload = {
            "grant_type": "authorization_code",
            "client_id": settings.etsy_api_key,
            "redirect_uri": settings.etsy_callback_url,
            "code": code,
            "code_verifier": code_verifier,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(ETSY_TOKEN_URL, data=payload)
            resp.raise_for_status()
            return resp.json()

    async def refresh_access_token(self, db: Session) -> Optional[OAuthToken]:
        """
        저장된 refresh_token으로 access_token 갱신.
        갱신 실패 시 None 반환 (재인증 필요).
        """
        token = self.get_stored_token(db)
        if not token or not token.refresh_token:
            return None

        payload = {
            "grant_type": "refresh_token",
            "client_id": settings.etsy_api_key,
            "refresh_token": token.refresh_token,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(ETSY_TOKEN_URL, data=payload)
                resp.raise_for_status()
                data = resp.json()
            refreshed = self._save_token(data, db, existing=token)
            # shop_id는 이미 저장되어 있으므로 갱신 불필요 (실패해도 기존 값 유지)
            return refreshed
        except httpx.HTTPError as e:
            logger.error(f"Token refresh failed: {e}")
            return None

    def _save_token(
        self, data: dict, db: Session, existing: Optional[OAuthToken] = None
    ) -> OAuthToken:
        """
        토큰 데이터를 DB에 저장 (UPSERT 패턴).
        - existing이 있으면 업데이트, 없으면 기존 레코드 조회 후 업데이트/신규 생성
        """
        expires_in = data.get("expires_in")
        expires_at = (
            datetime.utcnow() + timedelta(seconds=int(expires_in))
            if expires_in
            else None
        )

        # UPSERT: 이미 existing이 주어졌거나, DB에 있는 레코드를 재사용
        if existing is None:
            existing = db.query(OAuthToken).order_by(OAuthToken.created_at.desc()).first()

        if existing is None:
            token = OAuthToken()
            db.add(token)
        else:
            token = existing
            # 나머지 오래된 레코드 정리 (단일 사용자 - 중복 방지)
            db.query(OAuthToken).filter(OAuthToken.id != token.id).delete()

        token.access_token = data["access_token"]
        token.refresh_token = data.get("refresh_token") or getattr(token, "refresh_token", None)
        token.token_type = data.get("token_type", "Bearer")
        token.expires_at = expires_at
        token.scope = data.get("scope", ETSY_SCOPES)

        db.flush()   # shop_id 조회 전에 token.id 확정
        db.commit()
        db.refresh(token)
        return token

    async def _fetch_and_update_shop_info(self, token: OAuthToken, db: Session) -> None:
        """
        access_token 저장 후 Etsy /v3/application/shops/me 호출로
        shop_id와 shop_name을 비동기로 업데이트 (실패 시 무시).
        """
        try:
            headers = {
                "x-api-key": settings.etsy_api_key,
                "Authorization": f"Bearer {token.access_token}",
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://openapi.etsy.com/v3/application/shops/me",
                    headers=headers,
                )
            if resp.status_code == 200:
                shop_data = resp.json()
                token.shop_id = str(shop_data.get("shop_id", ""))
                token.shop_name = shop_data.get("shop_name", "")
                db.commit()
                db.refresh(token)
                logger.info(f"Shop info saved: {token.shop_name} (id={token.shop_id})")
        except Exception as e:
            logger.warning(f"Could not fetch shop info: {e}. shop_id will be empty.")

    def get_stored_token(self, db: Session) -> Optional[OAuthToken]:
        """DB에서 최신 OAuth 토큰을 조회"""
        return db.query(OAuthToken).order_by(OAuthToken.created_at.desc()).first()

    def is_token_valid(self, token: OAuthToken) -> bool:
        """토큰이 유효한지 확인 (만료 5분 전부터 무효 처리)"""
        if not token:
            return False
        if token.expires_at is None:
            return True  # 만료 시간 없음 = 유효
        return token.expires_at > datetime.utcnow() + timedelta(minutes=5)

    async def get_valid_access_token(self, db: Session) -> Optional[str]:
        """
        유효한 access_token 반환.
        만료된 경우 자동으로 refresh 시도.
        실패 시 None 반환.
        """
        token = self.get_stored_token(db)
        if not token:
            return None
        if self.is_token_valid(token):
            return token.access_token
        # 토큰 만료 → refresh 시도
        refreshed = await self.refresh_access_token(db)
        return refreshed.access_token if refreshed else None

    def revoke_token(self, db: Session) -> None:
        """저장된 모든 토큰 삭제 (연결 해제)"""
        db.query(OAuthToken).delete()
        db.commit()
        logger.info("Etsy OAuth tokens revoked.")

    def get_auth_status(self, db: Session) -> dict:
        """현재 인증 상태 반환"""
        token = self.get_stored_token(db)
        if not token:
            return {"authenticated": False, "shop_id": None, "shop_name": None}
        valid = self.is_token_valid(token)
        return {
            "authenticated": valid,
            "shop_id": token.shop_id,
            "shop_name": token.shop_name,
            "scope": token.scope,
            "expires_at": token.expires_at.isoformat() if token.expires_at else None,
            "can_refresh": bool(token.refresh_token),
        }


# 싱글턴
etsy_oauth_service = EtsyOAuthService()
