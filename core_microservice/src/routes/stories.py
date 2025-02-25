from fastapi import APIRouter, Request, Depends, HTTPException, Query
from sqlmodel import Session
from src.database import get_db
from src.services.auth import get_current_active_user
from src.services.stories import story_service
from src.models import User
from src.schema import (
    StoryCreate,
    StoryInfo,
    StoryResponse,
    UIStoriesResponse,
    UserNameTag
)

router = APIRouter(
    prefix='/api/stories',
    tags=['stories'],
    responses={404: {'description': 'Not found'}}
)

# get stories
@router.get('/', response_model = UIStoriesResponse)
def get_stories(
    request: Request,
    page: int = Query(gt=0),  
    page_size: int = Query(default=10, gt=0, le=100),  
    db: Session = Depends(get_db)
) -> UIStoriesResponse:
    return story_service.get_stories(db, page, page_size)

# get a story by id
@router.get('/{id}', response_model=StoryResponse)
def get_story(
    id: int,
    db: Session = Depends(get_db)
) -> StoryResponse:
    story = story_service.get_story_by_id(id, db)
    return StoryResponse(
        id=story.id,
        name=story.name,
        blurb=story.blurb,
        author=UserNameTag(
            id=story.user.id,
            username=story.user.username
        )
    )

# create a story
@router.post('/', response_model = StoryResponse)
def create_story(
    request: Request,
    story_data: StoryInfo,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> StoryResponse:
    story_create_data = StoryCreate(user_id=current_user.id, info=story_data)
    return story_service.create_story(story_create_data, db)


# delete a story
@router.delete('/{id}')
def delete_story(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> dict[str, str]:
    story = story_service.get_story_by_id(id, db)

    if story.user.id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to delete this story"
        )
    
    return story_service.delete_story(id, db)