from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.auth import require_session
from app.db import get_db
from app.models.goals import FinancialGoal, HealthGoal
from app.schemas.finance import ListResponse
from app.schemas.goals import FinancialGoalCreate, FinancialGoalResponse, GoalPatch, HealthGoalCreate, HealthGoalResponse
from app.services import goals

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_session)])
Db = Annotated[Session, Depends(get_db)]
PageLimit = Annotated[int, Query(ge=1, le=200)]
PageOffset = Annotated[int, Query(ge=0)]


@router.get("/financial-goals", response_model=ListResponse[FinancialGoalResponse])
def financial_goals(db: Db, include_archived: bool = False, limit: PageLimit = 50, offset: PageOffset = 0):
    items, total = goals.list_goals(db, FinancialGoal, include_archived, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/financial-goals", response_model=FinancialGoalResponse, status_code=201)
def create_financial_goal(data: FinancialGoalCreate, db: Db):
    return goals.create_goal(db, data)


@router.get("/financial-goals/{goal_id}", response_model=FinancialGoalResponse)
def financial_goal(goal_id: UUID, db: Db):
    return goals.get_goal(db, FinancialGoal, goal_id)


@router.patch("/financial-goals/{goal_id}", response_model=FinancialGoalResponse)
def update_financial_goal(goal_id: UUID, data: GoalPatch, db: Db):
    return goals.update_goal(db, FinancialGoal, goal_id, data)


@router.delete("/financial-goals/{goal_id}", status_code=204)
def delete_financial_goal(goal_id: UUID, db: Db):
    goals.delete_goal(db, FinancialGoal, goal_id)
    return Response(status_code=204)


@router.get("/health-goals", response_model=ListResponse[HealthGoalResponse])
def health_goals(db: Db, include_archived: bool = False, limit: PageLimit = 50, offset: PageOffset = 0):
    items, total = goals.list_goals(db, HealthGoal, include_archived, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/health-goals", response_model=HealthGoalResponse, status_code=201)
def create_health_goal(data: HealthGoalCreate, db: Db):
    return goals.create_goal(db, data)


@router.get("/health-goals/{goal_id}", response_model=HealthGoalResponse)
def health_goal(goal_id: UUID, db: Db):
    return goals.get_goal(db, HealthGoal, goal_id)


@router.patch("/health-goals/{goal_id}", response_model=HealthGoalResponse)
def update_health_goal(goal_id: UUID, data: GoalPatch, db: Db):
    return goals.update_goal(db, HealthGoal, goal_id, data)


@router.delete("/health-goals/{goal_id}", status_code=204)
def delete_health_goal(goal_id: UUID, db: Db):
    goals.delete_goal(db, HealthGoal, goal_id)
    return Response(status_code=204)
