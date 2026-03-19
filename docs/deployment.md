# Deployment

PhdScout can be deployed in three ways: on **HuggingFace Spaces** (free, public), locally on your own machine, or on any Linux server. This page covers all three scenarios.

---

## HuggingFace Spaces (recommended for sharing)

[HuggingFace Spaces](https://huggingface.co/spaces) provides free hosting for Gradio apps with a public URL. The live demo at [huggingface.co/spaces/HipFil98/PhDScout](https://huggingface.co/spaces/HipFil98/PhDScout) is deployed this way.

### Prerequisites

- A HuggingFace account (free at [huggingface.co](https://huggingface.co)).
- A Groq API key (free at [console.groq.com/keys](https://console.groq.com/keys)).

### Step 1 — Create a new Space

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space).
2. Choose **Gradio** as the SDK.
3. Set visibility to **Public** or **Private**.
4. Click **Create Space**.

### Step 2 — Upload the code

The easiest way is to clone the Space repository and push the PhdScout files:

```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
cd YOUR_SPACE_NAME

# Copy PhdScout files
cp -r /path/to/PhDScout/agent .
cp /path/to/PhDScout/app.py .
cp /path/to/PhDScout/config.py .
cp /path/to/PhDScout/requirements.txt .
```

### Step 3 — Add the README frontmatter

HuggingFace Spaces requires a specific YAML frontmatter block at the top of `README.md` to configure the Space:

```yaml
---
title: PhdScout
emoji: 🎓
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: "4.44.0"
app_file: app.py
pinned: false
license: mit
---
```

!!! warning "Two-branch strategy"
    The GitHub `README.md` and the HuggingFace `README.md` serve different purposes: GitHub renders it as a project README (frontmatter would appear as ugly YAML), while HuggingFace requires the frontmatter for Space configuration.

    The recommended approach is to maintain two branches:
    - `main` — GitHub-facing branch, `README.md` has no frontmatter.
    - `hf-space` — HuggingFace-facing branch, `README.md` has the YAML frontmatter.

    ```bash
    # Create the HF branch from main
    git checkout -b hf-space

    # Prepend the frontmatter to README.md
    # (edit manually or with a script)

    # Push to the HF Space remote
    git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE
    git push hf hf-space:main
    ```

    When you update the codebase, merge `main` into `hf-space` and push to both remotes:
    ```bash
    git checkout hf-space
    git merge main
    git push origin hf-space    # GitHub
    git push hf hf-space:main  # HuggingFace
    ```

### Step 4 — Set Space Secrets

In your Space settings, go to **Settings → Repository secrets** and add:

| Secret name | Value | Required |
|---|---|---|
| `GROQ_API_KEY` | Your Groq API key starting with `gsk_` | Yes (for Groq backend) |
| `HF_TOKEN` | Your HuggingFace token | Optional (fallback backend) |

Do **not** put API keys in `app.py` or any tracked file. The `app.py` reads them with:

```python
_GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
_HF_TOKEN  = os.environ.get("HF_TOKEN", "")
```

### Step 5 — Verify the Space

After pushing, HuggingFace will build the Space automatically. Check the **Logs** tab for any build errors. A successful build will show the Gradio UI loading.

If `GROQ_API_KEY` is set, the model dropdown will show "Free via Groq — no user limits". If only `HF_TOKEN` is set, it falls back to HuggingFace Serverless Inference.

!!! note "Cold start"
    HuggingFace Spaces on the free tier may sleep after periods of inactivity. The first request after a cold start may take 20–30 seconds to respond.

---

## Local Deployment

For running PhdScout on your own machine — either for development or private use.

### With Groq

```bash
git clone https://github.com/Hipsterfil998/PhDScout.git
cd PhDScout
pip install -r requirements.txt
pip install gradio>=4.0.0

cat > .env << 'EOF'
LLM_BACKEND=groq
GROQ_API_KEY=gsk_your_key_here
OUTPUT_DIR=./output
EOF

python app.py
# Open http://localhost:7860
```

### With Ollama

```bash
# Install Ollama from https://ollama.com/download
ollama serve &
ollama pull llama3.1:8b

cat > .env << 'EOF'
LLM_BACKEND=ollama
OLLAMA_MODEL=llama3.1:8b
OLLAMA_BASE_URL=http://localhost:11434/v1
EOF

python app.py
```

### With Docker (Ollama)

```dockerfile
# Dockerfile (example — not included in the repo)
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gradio>=4.0.0

COPY . .

ENV LLM_BACKEND=ollama
ENV OLLAMA_BASE_URL=http://host.docker.internal:11434/v1
ENV OLLAMA_MODEL=llama3.1:8b

CMD ["python", "app.py"]
```

```bash
# Run Ollama on the host, then:
docker build -t phdscout .
docker run -p 7860:7860 phdscout
```

---

## Server Deployment

For deploying on a Linux server (VPS, university HPC, etc.) with persistent uptime.

### Using systemd

Create a service file at `/etc/systemd/system/phdscout.service`:

```ini
[Unit]
Description=PhdScout Gradio App
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/PhDScout
Environment="LLM_BACKEND=groq"
Environment="GROQ_API_KEY=gsk_your_key"
ExecStart=/home/youruser/.venv/bin/python app.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable phdscout
sudo systemctl start phdscout
sudo systemctl status phdscout
```

### Behind nginx

```nginx
server {
    listen 80;
    server_name phdscout.example.com;

    location / {
        proxy_pass http://127.0.0.1:7860;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 300;
    }
}
```

Gradio uses WebSockets for streaming; the `Upgrade` headers are required.

---

## GitHub Actions: Automatic Docs Deployment

The `.github/workflows/docs.yml` workflow automatically rebuilds and deploys the MkDocs documentation to GitHub Pages whenever `docs/` or `mkdocs.yml` changes on the `main` branch.

See `.github/workflows/docs.yml` in the repository for the full workflow definition.

To deploy documentation manually:

```bash
pip install mkdocs-material
mkdocs gh-deploy --force
```

This builds the static site and pushes it to the `gh-pages` branch. GitHub Pages then serves it at `https://hipsterfil998.github.io/PhDScout`.

---

## Environment Variables Summary

| Variable | Required for | Notes |
|---|---|---|
| `GROQ_API_KEY` | Groq backend | Free at console.groq.com/keys |
| `HF_API_KEY` | HuggingFace backend (local) | Free at huggingface.co/settings/tokens |
| `HF_TOKEN` | HuggingFace backend (Spaces) | Same token, different variable name |
| `LLM_BACKEND` | CLI only | `groq`, `huggingface`, or `ollama` |
| `OLLAMA_MODEL` | Ollama backend | Default: `llama3.1:8b` |
| `OLLAMA_BASE_URL` | Ollama backend | Default: `http://localhost:11434/v1` |
| `OUTPUT_DIR` | CLI | Default: `./output` |

See [Configuration](../configuration.md) for the full reference.
