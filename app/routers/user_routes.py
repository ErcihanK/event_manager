"""
This Python file is part of a FastAPI application, demonstrating user management functionalities including creating, reading,
updating, and deleting (CRUD) user information. It uses OAuth2 with Password Flow for security, ensuring that only authenticated
users can perform certain operations. Additionally, the file showcases the integration of FastAPI with SQLAlchemy for asynchronous
database operations, enhancing performance by non-blocking database calls.

The implementation emphasizes RESTful API principles, with endpoints for each CRUD operation and the use of HTTP status codes
and exceptions to communicate the outcome of operations. It introduces the concept of HATEOAS (Hypermedia as the Engine of
Application State) by including navigational links in API responses, allowing clients to discover other related operations dynamically.

OAuth2PasswordBearer is employed to extract the token from the Authorization header and verify the user's identity, providing a layer
of security to the operations that manipulate user data.

Key Highlights:
- Use of FastAPI's Dependency Injection system to manage database sessions and user authentication.
- Demonstrates how to perform CRUD operations in an asynchronous manner using SQLAlchemy with FastAPI.
- Implements HATEOAS by generating dynamic links for user-related actions, enhancing API discoverability.
- Utilizes OAuth2PasswordBearer for securing API endpoints, requiring valid access tokens for operations.
"""

from builtins import dict, int, len, str
from datetime import timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_current_user, get_db, get_email_service, require_role
from app.schemas.pagination_schema import EnhancedPagination
from app.schemas.token_schema import TokenResponse
from app.schemas.user_schemas import (
    LoginRequest, UserBase, UserCreate, UserListResponse, 
    UserResponse, UserUpdate, UserUpdateProfilePicture,
    UserUpdateProfessionalInfo
)
from app.models.user_model import User  # Add this import for type hints
from app.services.user_service import UserService
from app.services.jwt_service import JWTService
from app.utils.link_generation import create_user_links, generate_pagination_links
from app.dependencies import get_settings
from app.services.email_service import EmailService
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
settings = get_settings()
@router.get("/users/{user_id}", response_model=UserResponse, name="get_user", tags=["User Management Requires (Admin or Manager Roles)"])
async def get_user(user_id: UUID, request: Request, db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme), current_user: dict = Depends(require_role(["ADMIN", "MANAGER"]))):
    """
    Endpoint to fetch a user by their unique identifier (UUID).

    Utilizes the UserService to query the database asynchronously for the user and constructs a response
    model that includes the user's details along with HATEOAS links for possible next actions.

    Args:
        user_id: UUID of the user to fetch.
        request: The request object, used to generate full URLs in the response.
        db: Dependency that provides an AsyncSession for database access.
        token: The OAuth2 access token obtained through OAuth2PasswordBearer dependency.
    """
    user = await UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserResponse.model_construct(
        id=user.id,
        nickname=user.nickname,
        first_name=user.first_name,
        last_name=user.last_name,
        bio=user.bio,
        profile_picture_url=user.profile_picture_url,
        github_profile_url=user.github_profile_url,
        linkedin_profile_url=user.linkedin_profile_url,
        role=user.role,
        email=user.email,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        links=create_user_links(user.id, request)  
    )

# Additional endpoints for update, delete, create, and list users follow a similar pattern, using
# asynchronous database operations, handling security with OAuth2PasswordBearer, and enhancing response
# models with dynamic HATEOAS links.

# This approach not only ensures that the API is secure and efficient but also promotes a better client
# experience by adhering to REST principles and providing self-discoverable operations.

@router.put("/users/{user_id}", response_model=UserResponse, name="update_user", tags=["User Management Requires (Admin or Manager Roles)"])
async def update_user(user_id: UUID, user_update: UserUpdate, request: Request, db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme), current_user: dict = Depends(require_role(["ADMIN", "MANAGER"]))):
    """
    Update user information.

    - **user_id**: UUID of the user to update.
    - **user_update**: UserUpdate model with updated user information.
    """
    user_data = user_update.model_dump(exclude_unset=True)
    updated_user = await UserService.update(db, user_id, user_data)
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserResponse.model_construct(
        id=updated_user.id,
        bio=updated_user.bio,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        nickname=updated_user.nickname,
        email=updated_user.email,
        last_login_at=updated_user.last_login_at,
        profile_picture_url=updated_user.profile_picture_url,
        github_profile_url=updated_user.github_profile_url,
        linkedin_profile_url=updated_user.linkedin_profile_url,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at,
        links=create_user_links(updated_user.id, request)
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, name="delete_user", tags=["User Management Requires (Admin or Manager Roles)"])
async def delete_user(user_id: UUID, db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme), current_user: dict = Depends(require_role(["ADMIN", "MANAGER"]))):
    """
    Delete a user by their ID.

    - **user_id**: UUID of the user to delete.
    """
    success = await UserService.delete(db, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)



@router.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["User Management"])
async def create_user(
    user: UserCreate, 
    request: Request, 
    db: AsyncSession = Depends(get_db), 
    email_service: EmailService = Depends(get_email_service)
):
    """
    Create a new user without requiring authentication.
    This endpoint is public to allow new user registration.
    """
    try:
        existing_user = await UserService.get_by_email(db, user.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Email already exists"
            )
        
        created_user = await UserService.create(db, user.model_dump(), email_service)
        if not created_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Failed to create user"
            )
        
        return UserResponse.model_construct(
            id=created_user.id,
            bio=created_user.bio,
            first_name=created_user.first_name,
            last_name=created_user.last_name,
            profile_picture_url=created_user.profile_picture_url,
            github_profile_url=created_user.github_profile_url,
            linkedin_profile_url=created_user.linkedin_profile_url,
            nickname=created_user.nickname,
            email=created_user.email,
            last_login_at=created_user.last_login_at,
            created_at=created_user.created_at,
            updated_at=created_user.updated_at,
            links=create_user_links(created_user.id, request)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/users/", response_model=UserListResponse, tags=["User Management Requires (Admin or Manager Roles)"])
async def list_users(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["ADMIN", "MANAGER"]))
):
    total_users = await UserService.count(db)
    users = await UserService.list_users(db, skip, limit)

    user_responses = [
        UserResponse.model_validate(user) for user in users
    ]
    
    pagination_links = generate_pagination_links(request, skip, limit, total_users)
    
    # Construct the final response with pagination details
    return UserListResponse(
        items=user_responses,
        total=total_users,
        page=skip // limit + 1,
        size=len(user_responses),
        links=pagination_links  # Ensure you have appropriate logic to create these links
    )


@router.post("/register/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Login and Registration"])
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service)
):
    """
    Register a new user with validation and email verification.
    
    Parameters:
    - email: Valid email address
    - nickname: Username (3-50 characters, alphanumeric and [-._])
    - password: Strong password (min 8 chars, 1 uppercase, 1 lowercase, 1 number, 1 special)
    - first_name: User's first name
    - last_name: User's last name
    - bio: Optional user biography
    - profile_picture_url: Optional URL to profile picture
    - linkedin_profile_url: Optional LinkedIn profile URL
    - github_profile_url: Optional GitHub profile URL
    """
    try:
        # Check if email already exists
        existing_user = await UserService.get_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if nickname already exists
        existing_nickname = await UserService.get_by_nickname(db, user_data.nickname)
        if existing_nickname:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nickname already taken"
            )
        
        # Create user and send verification email
        created_user = await UserService.create(db, user_data.model_dump(), email_service)
        
        return UserResponse(
            id=created_user.id,
            email=created_user.email,
            nickname=created_user.nickname,
            first_name=created_user.first_name,
            last_name=created_user.last_name,
            bio=created_user.bio,
            profile_picture_url=created_user.profile_picture_url,
            linkedin_profile_url=created_user.linkedin_profile_url,
            github_profile_url=created_user.github_profile_url,
            role=created_user.role,
            is_professional=created_user.is_professional,
            last_login_at=created_user.last_login_at,
            created_at=created_user.created_at,
            updated_at=created_user.updated_at,
            links=create_user_links(created_user.id, request)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/login/", response_model=TokenResponse, tags=["Login and Registration"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_db)):
    """
    Authenticate a user and return an access token.

    Parameters:
    - username: User's email or nickname
    - password: User's password

    Returns:
    - TokenResponse: Access token and token type

    Raises:
    - HTTPException(400): Account is locked due to too many failed attempts
    - HTTPException(401): Invalid credentials
    - HTTPException(500): Internal server error during authentication
    """
    try:
        if await UserService.is_account_locked(session, form_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Account locked due to too many failed login attempts."
            )

        user = await UserService.login_user(session, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Incorrect email or password"
            )

        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = JWTService.create_access_token(
            data={"sub": user.email, "role": str(user.role.name)},
            expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during authentication. Please try again later."
        )


@router.get("/verify-email/{user_id}/{token}", status_code=status.HTTP_200_OK, name="verify_email", tags=["Login and Registration"])
async def verify_email(user_id: UUID, token: str, db: AsyncSession = Depends(get_db), email_service: EmailService = Depends(get_email_service)):
    """
    Verify user's email with a provided token.
    
    - **user_id**: UUID of the user to verify.
    - **token**: Verification token sent to the user's email.
    """
    if await UserService.verify_email_with_token(db, user_id, token):
        return {"message": "Email verified successfully"}
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token")

# Fix route paths
@router.patch("/users/{user_id}/profile-picture", response_model=UserResponse)
async def update_profile_picture(
    user_id: UUID,
    profile_data: UserUpdateProfilePicture,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if str(current_user["user_id"]) != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized to update this profile")
    updated_user = await UserService.update_profile_picture(db, user_id, profile_data.profile_picture_url)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.patch("/{user_id}/professional", response_model=UserResponse)
async def update_user_professional_info(
    user_id: UUID,
    professional_info: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if str(current_user.id) != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
        
    updated_user = await UserService.update_user(
        db,
        user_id,
        {
            "linkedin_profile_url": professional_info.get("linkedin_url"),
            "github_profile_url": professional_info.get("github_url")
        }
    )
    return updated_user

@router.patch("/users/{user_id}/professional", response_model=UserResponse)
async def update_professional_info(
    user_id: UUID,
    professional_data: UserUpdateProfessionalInfo,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if str(current_user["user_id"]) != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized to update this profile")
    updated_user = await UserService.update_professional_info(db, user_id, professional_data)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.post("/users/verify-email/{token}", response_model=dict)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        if await UserService.verify_email(db, token):
            return {"message": "Email verified successfully"}
        raise HTTPException(status_code=400, detail="Invalid verification token")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ...existing code...