"""
Background worker that processes captured tasks periodically
Runs independently, can be triggered manually via API
"""
import asyncio
import os
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.models.task import Task
from app.llm.processor import get_processor


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/tasks.db")


async def process_captured_tasks_worker():
    """Main worker loop - processes captured tasks"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    processor = get_processor()
    print(f"[Worker] Started - processing every 2 minutes")

    while True:
        try:
            async with async_session_maker() as session:
                # Get captured tasks
                result = await session.execute(
                    select(Task).where(Task.status == "captured")
                )
                captured_tasks = result.scalars().all()

                if captured_tasks:
                    print(f"[Worker] Processing {len(captured_tasks)} captured tasks...")

                    # Get active tasks for context
                    result = await session.execute(
                        select(Task).where(Task.status == "active")
                    )
                    active_tasks = result.scalars().all()

                    # Process
                    new_task_dicts = [t.to_dict() for t in captured_tasks]
                    active_task_dicts = [t.to_dict() for t in active_tasks]

                    processed = await processor.process_new_tasks(
                        new_task_dicts,
                        active_task_dicts
                    )

                    # Update DB
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
                    print(f"[Worker] Processed {len(captured_tasks)} tasks")

        except Exception as e:
            print(f"[Worker] Error: {e}")

        # Wait before next run (default 2 minutes)
        interval = int(os.getenv("WORKER_INTERVAL", "120"))
        await asyncio.sleep(interval)


if __name__ == "__main__":
    asyncio.run(process_captured_tasks_worker())
