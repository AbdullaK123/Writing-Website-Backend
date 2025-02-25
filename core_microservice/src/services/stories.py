from src.models import Story
from src.schema import (
    StoryCreate,
    StoryResponse,
    UIStoriesResponse,
    UserNameTag,
    StoryInfo
)
from sqlmodel import Session, select, func
from fastapi import HTTPException, status
from typing import Optional, List, Dict
from src.logging import db_logger

class StoryService:
    def get_stories(self, db: Session, page: int, page_size: int = 10) -> UIStoriesResponse:
        db_logger.info(f"Retrieving stories page {page} with size {page_size}")
        try:
            db_logger.debug("Counting total stories")
            count_statement = select(func.count(Story.id))
            db_logger.debug(f"Count query: {count_statement}")
            
            total_count = db.exec(count_statement).first()
            db_logger.debug(f"Total stories count: {total_count}")

            page_count = (total_count + page_size - 1) // page_size
            db_logger.debug(f"Calculated total pages: {page_count}")

            statement = select(Story).limit(page_size).offset((page - 1)*page_size)
            db_logger.debug(f"Executing story query: {statement}")

            stories = db.exec(statement).all()
            db_logger.debug(f"Retrieved {len(stories)} stories")

            if not stories:
                db_logger.warning("No stories found in database")
                raise HTTPException(
                    status_code=404,
                    detail="No stories yet"
                )
            
            db_logger.debug("Creating response objects for stories")
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
            db_logger.debug(f"Created {len(stories_to_get)} story response objects")

            response = UIStoriesResponse(
                page=page,
                page_count=page_count,
                stories=stories_to_get
            )
            db_logger.info(f"Successfully retrieved page {page} of stories")
            return response

        except HTTPException:
            raise
        except Exception as e:
            db_logger.error(f"Error retrieving stories: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"A database error occurred: {e}"
            )

    def create_story(self, story_data: StoryCreate, db: Session) -> StoryResponse:
        db_logger.info(f"Attempting to create story with name: {story_data.info.name}")
        try:
            db_logger.debug("Checking for existing story with same title")
            story = self.get_story_by_title(story_data.info.name, db)

            if story:
                db_logger.warning(f"Story already exists with name: {story_data.info.name}")
                raise HTTPException(
                    status_code=400,
                    detail="A story with that name already exists"
                )
            
            db_logger.debug("Creating new story object")
            story_to_create = Story(
                user_id=story_data.user_id,
                name=story_data.info.name,
                blurb=story_data.info.blurb
            )
            db_logger.debug(f"Story object created: {story_to_create.__dict__}")

            db_logger.debug("Validating story model")
            db_story = Story.model_validate(story_to_create)

            db_logger.debug("Adding story to database")
            db.add(db_story)
            db_logger.debug("Committing transaction")
            db.commit()
            db_logger.debug("Refreshing story object")
            db.refresh(db_story)

            db_logger.debug("Creating response object")
            response = StoryResponse(
                id=db_story.id,
                name=db_story.name,
                blurb=db_story.blurb,
                author=UserNameTag(
                    id=db_story.user.id,
                    username=db_story.user.username
                )
            )
            db_logger.info(f"Successfully created story with ID: {db_story.id}")
            return response
  
        except Exception as e:
            db_logger.error(f"Error creating story: {str(e)}", exc_info=True)
            db.rollback()
            db_logger.info("Database transaction rolled back")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"A database error occurred: {e}"
            )

    def delete_story(self, id: int, db: Session) -> dict[str, str]:
        db_logger.info(f"Attempting to delete story with ID: {id}")
        try:
            db_logger.debug("Retrieving story to delete")
            story_to_delete = self.get_story_by_id(id, db)

            if not story_to_delete:
                db_logger.warning(f"No story found with ID: {id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Story with id {id} not found"
                )

            db_logger.debug(f"Found story to delete: {story_to_delete.__dict__}")
            db_logger.debug("Deleting story")
            db.delete(story_to_delete)
            db_logger.debug("Committing deletion")
            db.commit()

            db_logger.info(f"Successfully deleted story {id}")
            return {"message": "story successfully deleted"}
        
        except HTTPException:
            raise
        except Exception as e:
            db_logger.error(f"Error deleting story: {str(e)}", exc_info=True)
            db.rollback()
            db_logger.info("Database transaction rolled back")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"A database error occurred: {e}"
            )

    def get_story_by_id(self, id: int, db: Session) -> Story:
        db_logger.info(f"Attempting to get story by ID: {id}")
        try:
            db_logger.debug("Executing database query")
            story = db.get(Story, id)

            if not story:
                db_logger.warning(f"No story found with ID: {id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Story with id {id} not found"
                )
            
            db_logger.debug(f"Found story: {story.__dict__}")
            return story
        
        except HTTPException:
            raise
        except Exception as e:
            db_logger.error(f"Error retrieving story: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"A database error occurred: {e}"
            )

    def get_story_by_title(self, title: str, db: Session) -> Story:
        db_logger.info(f"Attempting to get story by title: {title}")
        try:
            statement = select(Story).where(Story.name == title)
            db_logger.debug(f"Executing query: {statement}")

            story = db.exec(statement).first()

            if not story:
                db_logger.warning(f"No story found with title: {title}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Story with title {title} not found"
                )
            
            db_logger.debug(f"Found story: {story.__dict__}")
            return story
        
        except HTTPException:
            raise
        except Exception as e:
            db_logger.error(f"Error retrieving story: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"A database error occurred: {e}"
            )

db_logger.info("Creating StoryService instance")
story_service = StoryService()
db_logger.info("StoryService instance created")