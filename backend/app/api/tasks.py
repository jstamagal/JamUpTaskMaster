from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from app.database import get_session
from app.models.task import Task
from app.llm.processor import get_processor

router = APIRouter()


class TaskCreate(BaseModel):
    raw_input: str


class TaskUpdate(BaseModel):
    status: Optional[str] = None
    priority_score: Optional[float] = None
    notes: Optional[str] = None
    due_by: Optional[datetime] = None


@router.post("/tasks/capture")
async def capture_task(
    task_input: TaskCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Capture a task - the main entry point from rofi/fuzzel
    This is SILENT and INSTANT - no LLM processing, just save
    Processing happens in background
    """
    # Create task immediately - no LLM, no waiting
    task = Task(
        raw_input=task_input.raw_input,
        status="captured",
        created_at=datetime.utcnow(),
        touched_at=datetime.utcnow(),
    )

    session.add(task)
    await session.commit()
    await session.refresh(task)

    # Return immediately - background worker will process
    return {
        "id": task.id,
        "status": "captured",
        "message": "Task captured"
    }


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_session)
):
    """List tasks, optionally filtered by status"""
    query = select(Task)

    if status:
        query = query.where(Task.status == status)

    # Order by priority (desc) and touched_at (desc)
    query = query.order_by(Task.priority_score.desc(), Task.touched_at.desc()).limit(limit)

    result = await session.execute(query)
    tasks = result.scalars().all()

    return {
        "tasks": [task.to_dict() for task in tasks],
        "count": len(tasks)
    }


@router.get("/tasks/{task_id}")
async def get_task(
    task_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get a specific task"""
    result = await session.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task.to_dict()


@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Update a task"""
    result = await session.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Update fields
    if task_update.status is not None:
        task.status = task_update.status
    if task_update.priority_score is not None:
        task.priority_score = task_update.priority_score
    if task_update.notes is not None:
        task.notes = task_update.notes
    if task_update.due_by is not None:
        task.due_by = task_update.due_by

    task.touched_at = datetime.utcnow()

    await session.commit()
    await session.refresh(task)

    return task.to_dict()


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Delete a task"""
    result = await session.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await session.delete(task)
    await session.commit()

    return {"message": "Task deleted"}


@router.get("/tasks/stats/overview")
async def get_stats(session: AsyncSession = Depends(get_session)):
    """Get overview stats"""
    result = await session.execute(select(Task))
    all_tasks = result.scalars().all()

    stats = {
        "total": len(all_tasks),
        "by_status": {},
        "life_critical_active": 0,
        "quick_wins": 0,
        "high_priority": 0,
    }

    for task in all_tasks:
        # Count by status
        status = task.status or "unknown"
        stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

        # Count special categories
        if task.is_life_critical and task.status == "active":
            stats["life_critical_active"] += 1
        if task.is_quick_win and task.status == "active":
            stats["quick_wins"] += 1
        if task.priority_score >= 0.7 and task.status == "active":
            stats["high_priority"] += 1

    return stats


@router.post("/tasks/process")
async def process_captured_tasks(session: AsyncSession = Depends(get_session)):
    """
    Manually trigger processing of captured tasks
    (Background worker calls this periodically)
    """
    processor = get_processor()

    # Get all captured tasks
    result = await session.execute(
        select(Task).where(Task.status == "captured")
    )
    captured_tasks = result.scalars().all()

    if not captured_tasks:
        return {"message": "No tasks to process", "count": 0}

    # Get context: existing active tasks
    result = await session.execute(
        select(Task).where(Task.status == "active")
    )
    active_tasks = result.scalars().all()

    # Process with LLM
    new_task_dicts = [t.to_dict() for t in captured_tasks]
    active_task_dicts = [t.to_dict() for t in active_tasks]

    try:
        processed = await processor.process_new_tasks(
            new_task_dicts,
            active_task_dicts
        )

        # Update tasks in DB
        for task, data in zip(captured_tasks, processed):
            task.processed_text = data.get("processed_text")
            task.priority_score = data.get("priority_score", 0.5)
            task.category = data.get("category")
            task.is_life_critical = data.get("is_life_critical", False)
            task.is_quick_win = data.get("is_quick_win", False)
            task.notes = data.get("notes", "")
            task.status = "active"
            task.touched_at = datetime.utcnow()

        await session.commit()

        return {
            "message": "Tasks processed",
            "count": len(captured_tasks)
        }
    except Exception as e:
        print(f"Error processing tasks: {e}")
        return {"error": str(e)}, 500


@router.get("/tasks/suggestions")
async def get_suggestions(
    user_state: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):
    """Get AI suggestions for what to do next"""
    processor = get_processor()

    # Get active tasks
    result = await session.execute(
        select(Task).where(Task.status == "active")
    )
    active_tasks = result.scalars().all()

    if not active_tasks:
        return {"suggestions": "No active tasks. Add some tasks to get started!"}

    task_dicts = [t.to_dict() for t in active_tasks]
    suggestions = await processor.get_suggestions(task_dicts, user_state)

    return {"suggestions": suggestions}
