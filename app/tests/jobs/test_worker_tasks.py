from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from app.worker.tasks import process_job
from app.modules.jobs.models import JobStatus


def _make_job(job_type="demo"):
    job = MagicMock()
    job.id = "test-job-id"
    job.job_type = job_type
    job.user_id = "test-user-id"
    job.job_metadata = None
    job.status = JobStatus.PENDING.value
    return job


def _make_db(job=None):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = job
    return db


def test_process_job_success():
    job = _make_job()
    db = _make_db(job)

    with patch("app.worker.tasks.SessionLocal", return_value=db):
        process_job("test-job-id")

    assert job.status == JobStatus.SUCCESS.value
    assert job.finished_at is not None
    db.commit.assert_called()
    db.close.assert_called()


def test_process_job_not_found():
    db = _make_db(job=None)

    with patch("app.worker.tasks.SessionLocal", return_value=db):
        process_job("00000000-0000-0000-0000-000000000000")

    db.close.assert_called()


def test_process_job_sets_running_status():
    job = _make_job()
    db = _make_db(job)

    statuses = []
    original_setattr = object.__setattr__

    def track_status(val):
        statuses.append(val)

    type(job).status = property(fget=lambda self: statuses[-1] if statuses else JobStatus.PENDING.value,
                                fset=lambda self, v: statuses.append(v))

    with patch("app.worker.tasks.SessionLocal", return_value=db):
        process_job("test-job-id")

    assert JobStatus.RUNNING.value in statuses
    assert JobStatus.SUCCESS.value in statuses


def test_process_job_rag_ingestion_skips_when_no_doc():
    job = _make_job(job_type="rag_ingestion")
    job.job_metadata = {"document_id": "nonexistent-doc"}
    db = _make_db(job)
    # Second query (for Document) returns None
    db.query.return_value.filter.return_value.first.side_effect = [job, None]

    with patch("app.worker.tasks.SessionLocal", return_value=db):
        process_job("test-job-id")

    assert job.status == JobStatus.SUCCESS.value
