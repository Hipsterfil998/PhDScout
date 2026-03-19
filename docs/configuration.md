# Configuration

PhdScout is configured through environment variables, loaded automatically from a `.env` file in the project root using `python-dotenv`. All settings are exposed through the `config` singleton (`config.py`).

---

## Environment Variables

### LLM Backend

| Variable | Default | Description |
|---|---|---|
| `LLM_BACKEND` | `ollama` | Active backend: `groq`, `huggingface`, or `ollama` |

### Groq Settings

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | _(empty)_ | Groq API key. Get one free at [console.groq.com/keys](https://console.groq.com/keys) |

The Groq base URL is hardcoded to `https://api.groq.com/openai/v1` and is not configurable via `.env`.

### HuggingFace Settings

| Variable | Default | Description |
|---|---|---|
| `HF_API_KEY` | _(empty)_ | HuggingFace access token |
| `HF_TOKEN` | _(empty)_ | Alternative token variable (used by HF Spaces) |
| `HF_MODEL` | `mistralai/Mistral-7B-Instruct-v0.3` | HuggingFace model ID |

!!! note "HF_TOKEN vs HF_API_KEY"
    In HuggingFace Spaces, secrets are injected as `HF_TOKEN` by convention. PhdScout reads `GROQ_API_KEY` first, then falls back to `HF_TOKEN`. For local use, `HF_API_KEY` is the standard variable name.

### Ollama Settings

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Ollama API base URL (OpenAI-compatible) |
| `OLLAMA_MODEL` | `llama3.1:8b` | Model name as it appears in `ollama list` |

### Generation Settings

| Variable | Default | Description |
|---|---|---|
| `MAX_TOKENS` | `4096` | Maximum tokens per LLM response. Hardcoded in `AppConfig`; not currently read from `.env`. |

### Output

| Variable | Default | Description |
|---|---|---|
| `OUTPUT_DIR` | `./output` | Directory where CLI saves application materials |

### Email (optional)

These variables are only used if you extend PhdScout to send emails programmatically. The `EmailConfig` dataclass reads them but they are not used by the current UI or CLI.

| Variable | Default | Description |
|---|---|---|
| `EMAIL_SMTP_HOST` | `smtp.gmail.com` | SMTP server hostname |
| `EMAIL_SMTP_PORT` | `587` | SMTP port |
| `EMAIL_FROM` | _(empty)_ | Sender email address |
| `EMAIL_PASSWORD` | _(empty)_ | SMTP password or app password |

---

## Complete `.env` Examples

=== "Groq (recommended)"

    ```ini title=".env"
    # LLM backend
    LLM_BACKEND=groq
    GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

    # Output
    OUTPUT_DIR=./output
    ```

=== "HuggingFace"

    ```ini title=".env"
    # LLM backend
    LLM_BACKEND=huggingface
    HF_API_KEY=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    HF_MODEL=mistralai/Mistral-7B-Instruct-v0.3

    # Output
    OUTPUT_DIR=./output
    ```

    !!! warning "Quota exhaustion"
        The free HuggingFace tier has a monthly inference quota. When it is exceeded, `LLMQuotaError` is raised. Switch to Groq or Ollama if this happens.

=== "Ollama (local)"

    ```ini title=".env"
    # LLM backend
    LLM_BACKEND=ollama
    OLLAMA_MODEL=llama3.1:8b
    OLLAMA_BASE_URL=http://localhost:11434/v1

    # Output
    OUTPUT_DIR=./output
    ```

    Make sure `ollama serve` is running and the model is pulled:
    ```bash
    ollama pull llama3.1:8b
    ```

=== "Ollama with custom host"

    If Ollama is running on a different host (e.g. a GPU server on your network):

    ```ini title=".env"
    LLM_BACKEND=ollama
    OLLAMA_MODEL=llama3.3:70b
    OLLAMA_BASE_URL=http://192.168.1.100:11434/v1
    ```

---

## Backend Selection Logic

The `app.py` (Gradio UI) overrides the backend selection at runtime:

```python
_GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
_HF_TOKEN  = os.environ.get("HF_TOKEN", "")

if _GROQ_KEY:
    _BACKEND = "groq"
    _API_KEY  = _GROQ_KEY
else:
    _BACKEND = "huggingface"
    _API_KEY  = _HF_TOKEN
```

This means `LLM_BACKEND` in `.env` is only used by the CLI (`main.py`). The web UI always prefers Groq if `GROQ_API_KEY` is set, and falls back to HuggingFace otherwise.

The CLI reads `config.llm_backend` directly from `.env` and respects whatever value is set.

---

## AppConfig Dataclass

The `AppConfig` dataclass in `config.py` exposes all settings as typed attributes:

```python
from config import config

print(config.llm_backend)       # "groq"
print(config.groq_api_key)      # "gsk_..."
print(config.ollama_model)      # "llama3.1:8b"
print(config.ollama_base_url)   # "http://localhost:11434/v1"
print(config.hf_model)          # "mistralai/Mistral-7B-Instruct-v0.3"
print(config.output_dir)        # "./output"
print(config.max_tokens)        # 4096
```

`config.validate()` performs a runtime check:

- **Ollama**: attempts a GET to `OLLAMA_BASE_URL` (stripped of `/v1`). Prints a warning if unreachable but does not raise.
- **HuggingFace**: warns if `HF_API_KEY` is empty.
- **Groq**: warns if `GROQ_API_KEY` is empty.
- **Unknown backend**: prints a warning with the supported values.

---

## Model Selection in the CLI

The `--model` flag overrides the config at runtime:

```bash
# Uses llama-3.1-8b-instant instead of the .env default
python main.py --cv cv.pdf --field "NLP" --model "llama-3.1-8b-instant"
```

When `--model` is passed, `config.ollama_model` is updated in-memory (for Ollama) and the `LLMClient` is instantiated with that model.

For Groq and HuggingFace, the model string is passed directly to the API; make sure it matches a valid model ID for the selected backend.

---

## Security Notes

!!! warning "Never commit your `.env` file"
    The `.gitignore` should include `.env`. API keys committed to public repositories may be automatically invalidated by the provider's security scanning.

!!! tip "HuggingFace Spaces secrets"
    When deploying to HuggingFace Spaces, add `GROQ_API_KEY` (and optionally `HF_TOKEN`) in the Space's **Settings → Repository secrets** panel. Do not hardcode keys in `app.py` or any tracked file.
