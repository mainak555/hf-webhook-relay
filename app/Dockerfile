
FROM python:3.12.10-slim-bookworm

# Non-root user (HF Spaces requirement)
# UID 1000 is the standard user for HF Spaces
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user app.py .
COPY --chown=user watch_list.py .
COPY --chown=user requirements.txt .

RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r requirements.txt

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
