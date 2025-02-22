from src.models import Story
from src.schema import (
    StoryCreate,
    StoryResponse,
    UIStoriesResponse,
    StoryResponse,
    UserNameTag,
    StoryInfo
)
from sqlmodel import Session, select, func
from fastapi import HTTPException, status
from typing import Optional, List, Dict


class StoryService:

    # method to get all stories
    def get_stories(
        self,
        db: Session,
        page: int,
        page_size: int = 10
    ) -> UIStoriesResponse:
        try:

            count_statement = select(func.count(Story.id))

            total_count = db.exec(count_statement).first()

            page_count = (total_count + page_size - 1) // page_size

            statement = select(Story).limit(page_size).offset((page - 1)*page_size)

            stories = db.exec(statement).all()

            if not stories:
                raise HTTPException(
                    status_code=404,
                    detail="No stories yet"
                )
            
            stories_to_get = [
                StoryResponse(
                    id=story.id,
                    name=story.name,
                    blurb=story.blurb,
                    author=UserNameTag(
                        id=story.user.id,
                        username=story.user.username
                    )
                )
                for story in stories
            ]

            return UIStoriesResponse(
                page=page,
                page_count=page_count,
                stories=stories_to_get
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"A database error occurred: {e}"
            )
            

    # method to create a story
    def create_story(
        self,
        story_data: StoryCreate,
        db: Session
    ) -> StoryResponse:
        
        try:
            
            # check if the story exists
            story = self.get_story_by_title(story_data.info.name, db)

            if story:
                raise HTTPException(
                    status_code=400,
                    detail="A story with that name already exists"
                )
            
            story_to_create = Story(
                user_id=story_data.user_id,
                name=story_data.info.name,
                blurb=story_data.info.blurb
            )

            db_story = Story.model_validate(story_to_create)

            db.add(db_story)
            db.commit()
            db.refresh(db_story)

            return StoryResponse(
                id=db_story.id,
                name=db_story.name,
                blurb=db_story.blurb,
                author=UserNameTag(
                    id=db_story.user.id,
                    username=db_story.user.username
                )
            )
  
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"A database error occurred: {e}"
            )


    # method to delete a story
    def delete_story(
        self,
        id: int,
        db: Session
    ) -> dict[str, str]:
        try:
            # grab the story
            story_to_delete = self.get_story_by_id(id, db)

            if not story_to_delete:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Story with id {id} not found"
                )

            # delete it
            db.delete(story_to_delete)
            db.commit()

            return {"message": "story successfully deleted"}
        
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"A database error occurred: {e}"
            )


    # method to get a story by its id
    def get_story_by_id(
        self,
        id: int,
        db: Session
    ) -> Story:
        try:

            story = db.get(Story, id)

            if not story:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Story with id {id} not found"
                )
            
            return story
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"A database error occurred: {e}"
            )

    # method to get a story by its title
    def get_story_by_title(
        self,
        title:str,
        db: Session
    ) -> Story:
        try:

            statement=select(Story).where(Story.name == title)

            story = db.exec(statement).first()

            if not story:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Story with title {title} not found"
                )
            return story
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"A database error occurred: {e}"
            )
        

story_service = StoryService()