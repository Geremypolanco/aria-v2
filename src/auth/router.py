from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from src.core.config import settings
from src.auth.jwt import create_access_token
from src.db.repositories import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@router.get("/login/google")
async def login_google(request: Request):
    redirect_uri = request.url_for("auth_callback_google")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback/google", name="auth_callback_google")
async def auth_callback_google(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo") or await oauth.google.userinfo(token=token)

        # Persist user in Supabase
        await UserRepository.upsert(
            google_sub=user_info["sub"],
            email=user_info["email"],
            name=user_info.get("name", ""),
            picture=user_info.get("picture", ""),
        )

        # Issue JWT
        access_token = create_access_token({
            "sub": user_info["sub"],
            "email": user_info["email"],
            "name": user_info.get("name", ""),
            "picture": user_info.get("picture", ""),
        })

        # Redirect to frontend with token in fragment
        response = RedirectResponse(url=f"/?token={access_token}")
        return response

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.get("/me")
async def me(request: Request):
    """Returns current user info from JWT (for frontend validation)."""
    from fastapi import Depends, HTTPException
    from src.auth.dependencies import get_current_user
    # This endpoint is handled via dependency injection in protected routes
    return {"message": "Use Authorization: Bearer <token> header"}
