import grpc
import os
from datetime import datetime, timedelta
from typing import Callable, Dict, Generator, List, Optional

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.models import Role, User

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "secret-for-development-only")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_user_by_email(email: str, db: Session) -> Optional[User]:
    return db.query(User).filter(User.email == email).one_or_none()


def get_user_by_id(user_id: int, db: Session) -> Optional[User]:
    return db.get(User, user_id)


def authenticate_user(email: str, password: str, db: Session) -> Optional[User]:
    user = get_user_by_email(email, db)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_access_token(data: Dict[str, object], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Dict[str, object]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    token_data = decode_access_token(credentials.credentials)
    user_id = token_data.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject")

    user = get_user_by_id(int(user_id), db)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")

    roles = token_data.get("roles", [])
    user.roles = [Role(name=role_name) for role_name in roles]
    return user


def require_roles(*allowed_roles: str) -> Callable[[User], User]:
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        user_role_names = {role.name for role in current_user.roles}
        if not user_role_names.intersection(set(allowed_roles)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return current_user

    return dependency


def require_authenticated_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


def get_grpc_auth_token(context) -> str:
    metadata = context.invocation_metadata()
    if not metadata:
        context.abort(grpc.StatusCode.UNAUTHENTICATED, "Missing authorization metadata")

    for item in metadata:
        if item.key.lower() == "authorization" and item.value:
            if item.value.startswith("Bearer "):
                return item.value[len("Bearer "):]
            return item.value

    context.abort(grpc.StatusCode.UNAUTHENTICATED, "Missing authorization token")


def get_user_from_grpc_context(context) -> User:
    token = get_grpc_auth_token(context)
    token_data = decode_access_token(token)
    user_id = token_data.get("sub")
    if not user_id:
        context.abort(grpc.StatusCode.UNAUTHENTICATED, "Token missing subject")

    with SessionLocal() as db:
        user = get_user_by_id(int(user_id), db)
        if not user or not user.is_active:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid user")

        roles = token_data.get("roles", [])
        user.roles = [Role(name=role_name) for role_name in roles]
        return user


def require_grpc_roles(context, *allowed_roles: str) -> User:
    user = get_user_from_grpc_context(context)
    if allowed_roles:
        user_role_names = {role.name for role in user.roles}
        if not user_role_names.intersection(set(allowed_roles)):
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "User does not have required role")
    return user
