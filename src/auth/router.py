from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth
from src.core.config import settings
from src.auth.jwt import create_access_token
from src.db.repositories import UserRepository

# Cambiamos el prefijo a /api/auth para que coincida con las rutas estándar de Vercel
router = APIRouter(prefix="/api/auth", tags=["auth"])

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@router.get("/login/google")
async def login(request: Request):
    # Forzamos la URL de redirección a HTTPS y con el path correcto
    redirect_uri = str(request.url_for("auth_callback"))
    # En Vercel, a veces url_for genera http en lugar de https tras proxies
    if "vercel.app" in redirect_uri and redirect_uri.startswith("http://"):
        redirect_uri = redirect_uri.replace("http://", "https://")
    
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback", name="auth_callback")
async def callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    user_info = token.get("userinfo") or {}
    sub = user_info.get("sub", "")
    email = user_info.get("email", "")
    name = user_info.get("name", "")
    picture = user_info.get("picture", "")

    if not sub or not email:
        return JSONResponse({"error": "No se pudo obtener info del usuario"}, status_code=400)

    UserRepository.upsert(sub, email, name, picture)

    access_token = create_access_token({"sub": sub, "email": email, "name": name})

    # Redirigir al home con el token
    return RedirectResponse(url=f"/?token={access_token}")


@router.get("/me")
async def me(request: Request):
    from src.auth.jwt import decode_access_token

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse({"authenticated": False})

    token = auth_header[7:]
    payload = decode_access_token(token)
    if not payload:
        return JSONResponse({"authenticated": False})

    return JSONResponse({"authenticated": True, "user": payload})
