# Feature: Support ollama cloud models

User must be able to use ollama cloud models.

1) Cloud model can be identified by ":cloud" or "-cloud" suffix at the end of the model name (e.g. `llama3.2:cloud`, `llama3.2-cloud`). The suffix is stripped before the request is sent to the API.

2) If a cloud model is used, the request must be made to the external host `https://ollama.com`. The cloud endpoint URL must be a configuration parameter in the config file (`ollama_cloud_endpoint`), defaulting to `https://ollama.com`.

3) When a cloud model is used, the app must add an Authorization header using the `OLLAMA_API_KEY` environment variable:
   `Authorization: Bearer <OLLAMA_API_KEY>`

4) User onboarding — when a cloud model is selected but `OLLAMA_API_KEY` is not set, the app must hard-fail with a clear, actionable message that:
   - Explains that cloud models require an Ollama account
   - Directs the user to create an account at https://ollama.com
   - Instructs the user to generate an API key in their account settings
   - Shows the exact environment variable to set: `export OLLAMA_API_KEY=<your-key>`

5) The `--init` interactive setup must inform the user about the cloud model workflow: account creation, API key generation, and the environment variable required.

6) Error handling must be present to identify and clearly report:
   - Missing API key (fail before any network request)
   - Authentication failure (HTTP 401) — invalid or expired API key
   - Authorization / account issue (HTTP 403) — account lacks access to the requested model
   - Rate limiting (HTTP 429) — API quota exceeded
   - Network connectivity issues — cannot reach the cloud endpoint
