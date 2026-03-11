
from huggingface_hub import HfApi
from util import create_hf_repo
import os

hfApi = HfApi(token=os.getenv("HF_TOKEN"))
hf_repo = os.getenv('HF_REPO')

# Create HF Space
create_hf_repo(hfApi, hf_repo, "space")

# Adding Secrets to Space
hfApi.add_space_secret(
    value=os.getenv("HF_TOKEN"),
    repo_id=hf_repo,
    key='HF_TOKEN',
);
hfApi.add_space_secret(
    value=os.getenv("HF_WEBHOOK_SECRET"),
    key='HF_WEBHOOK_SECRET',
    repo_id=hf_repo,
);
hfApi.add_space_secret(
    value=os.getenv("GH_PAT"),
    repo_id=hf_repo,
    key='GH_PAT'
)

# Deploying Relay App
hfApi.upload_folder(
    ignore_patterns=["*pycache**/", ".env"],
    folder_path="./app",
    repo_type="space",
    repo_id=hf_repo
)
