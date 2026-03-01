import pytest
from app.worker.tasks import process_job
from app.modules.jobs.models import Job, JobStatus, JobResult
from app.modules.users.models import User
from sqlalchemy.orm import Session

def test_process_job_success(db: Session):
    # Setup: Create a user and a job
    user = User(email="worker_test@example.com", hashed_password="hashed")
    db.add(user)
    db.commit()
    
    job = Job(user_id=user.id, status=JobStatus.PENDING.value)
    db.add(job)
    db.commit()
    
    # Execute the task logic
    # Mocking time.sleep might be needed if tests are too slow, 
    # but for now we let it run as it is a small task.
    process_job(job.id)
    
    # Refresh from DB
    db.refresh(job)
    
    # Assertions
    assert job.status == JobStatus.SUCCESS.value
    assert job.finished_at is not None
    
    # Check if result is saved
    result = db.query(JobResult).filter(JobResult.job_id == job.id).first()
    assert result is not None
    assert result.result_data == {"answer": 42}

def test_process_job_not_found(db: Session):
    # Should not raise exception, just return early and log error
    # Our logging will capture this if configured
    process_job("non-existent-id")
    # No changes to DB expected
    assert db.query(Job).count() == 0
