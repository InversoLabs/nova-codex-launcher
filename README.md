# NOVA Codex Launcher

Windows PowerShell launcher for native Codex sessions backed by NOVA. Includes model configuration, isolated Codex home, context limits, and optional app-server support.

Requires PowerShell, Node.js, Codex CLI, SSH, and a running NOVA bridge. Configure the NOVA-SERVER SSH host and bridge addresses for your environment. Supply NOVA_DESKTOP_API_KEY privately through your environment. No key files are included.

Example:

`powershell -ExecutionPolicy Bypass -File ./nova-codex-interactive.ps1 -Model gpt-oss:20b -Workspace C:/Projects/example -BaseUrl http://127.0.0.1:8788 -ContextTokens 16384`

Start [NOVA Codex Proxy](https://github.com/InversoLabs/nova-codex-proxy) separately when using port 8788. Conductor and Director bundle their own launcher copy.
