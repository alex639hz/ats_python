import hmac
import hashlib

from queue import Queue
import threading

import tempfile
import shutil

# from git import Repo

job_queue = Queue()

GITHUB_SECRET = "super-secret-string"


def verify_github_signature(secret: str, body: bytes, signature: str):
    mac = hmac.new(secret.encode(), msg=body, digestmod=hashlib.sha256)
    expected = "sha256=" + mac.hexdigest()
    return hmac.compare_digest(expected, signature)


def handle_github_event(event: str, payload: dict):
    if event == "push":
        on_push(payload)


def on_push(payload: dict):
    ref = payload["ref"]  # refs/heads/main
    branch = ref.split("/")[-1]

    commit_sha = payload["after"]
    repo_url = payload["repository"]["clone_url"]

    schedule_ci_job(repo_url=repo_url, branch=branch, commit=commit_sha)


def schedule_ci_job(**job):
    job_queue.put(job)


def ci_worker():
    while True:
        job = job_queue.get()
        try:
            run_ci_job(job)
        finally:
            job_queue.task_done()


threading.Thread(target=ci_worker, daemon=True).start()


def run_tests(workdir=""):
    pass


def run_ci_job(job: dict):
    workdir = tempfile.mkdtemp(prefix="ci-")

    try:
        repo = Repo.clone_from(job["repo_url"], workdir, branch=job["branch"], depth=1)

        result = run_tests(workdir)

        store_result(
            repo=job["repo_url"],
            branch=job["branch"],
            commit=job["commit"],
            result=result,
        )

    finally:
        shutil.rmtree(workdir)


def store_result(**data):
    print("CI RESULT:", data)


@server.post("/webhook/github")
async def github_webhook(request: Request):
    body = await request.body()

    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(400, "Missing signature")

    if not server_utils.verify_github_signature(
        server_utils.GITHUB_SECRET, body, signature
    ):
        raise HTTPException(403, "Invalid signature")

    payload = await request.json()
    event = str(request.headers.get("X-GitHub-Event"))

    server_utils.handle_github_event(event, payload)

    return {"status": "accepted"}
