
from fastapi import FastAPI, Header, HTTPException, Query
from watch_list import TRACKING_PATHS
from huggingface_hub import HfApi
import httpx
import os

HF_WEBHOOK_SECRET = os.getenv("HF_WEBHOOK_SECRET")
GH_PAT = os.getenv("GH_PAT")

app = FastAPI(
    title="Hugging Face Webhook Relay",
    description="Trigger Actions from HF Webhook",
    version="1.0.0"
)

@app.get("/")
def liveProbe():
    return app.title

@app.post("/v1/github_hook")
async def github_hook(
    x_webhook_secret: str = Header(None),
    hf_repo: str = Query(..., description="Hugging Face repo (format: user/repo)"), 
    gh_repo: str = Query(..., description="GitHub repo to trigger (format: user/repo)"), 
    hf_repo_type: str = Query(..., description="Hugging Face repo type (format: dataset|model|space)")
):
    # Verifying request is from HF Webhook
    if x_webhook_secret != HF_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid Secret")
    elif hf_repo not in TRACKING_PATHS or hf_repo_type not in TRACKING_PATHS[hf_repo]:        
        return {"filtered": True}
    else:
        ## check tracking files affected
        hfApi = HfApi(token=os.getenv("HF_TOKEN"))
        commit = hfApi.list_repo_commits(
            repo_type=hf_repo_type,
            repo_id=hf_repo
        )[0]

        changes = []
        tree = list(hfApi.list_repo_tree(hf_repo, repo_type=hf_repo_type, expand=True))
        for item in tree:
            if hasattr(item, 'last_commit') and item.last_commit:
                if item.last_commit['oid'] == commit.commit_id:
                    changes.append(item.path)

        exists = any(f in changes for f in TRACKING_PATHS[hf_repo][hf_repo_type])
        if not exists:
            return {"ignored": True}

    # Trigger GitHub Action            
    url = f"https://api.github.com/repos/{gh_repo}/dispatches"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers={
            "Authorization": f"Bearer {GH_PAT}",
            "Accept": "application/vnd.github.v3+json",
        }, json={
            "event_type": "hf_webhook_event", # match 'on' type in github action
            "client_payload": {
                "description": "Hugging Face Webhook",
                "hf_repo_type": hf_repo_type,
                "hf_repo": hf_repo,                
            }
        })

    print(f"HF Repo: {hf_repo} | HF Type: {hf_repo_type} | GitHub Repo: {gh_repo} | GitHub Status: {response.status_code}")
    return {"success": True}
