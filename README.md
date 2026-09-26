# NOVA Codex Launcher

Windows PowerShell launcher for native Codex sessions backed by NOVA. Includes model configuration, isolated Codex home, context limits, and optional app-server support.

The Windows GUI now includes **Gemma E2B - trained pilot + compact adapter**.
It uses the existing NOVA URL/key and runs Codex tools locally. See
[Gemma setup and limitations](gemma-agent/LAUNCHER.md). The actual two-step
checkpoint is registered on NOVA as `gemma4-codex:pilot-v1`.

Build the GUI with `dotnet build gui/NovaCodexLauncher.csproj -c Release`.
Place the GUI build in a `gui` folder next to these scripts, then use
`Start-Launcher.ps1`; it reuses the existing Windows-protected Conductor key.
The original provider profiles remain available.

Requires PowerShell, Node.js, Python, Codex CLI, and a running NOVA bridge. The Gemma profile uses the existing bridge connection without SSH. Legacy profiles may use the existing NOVA-SERVER SSH configuration for warm-up. Supply NOVA_DESKTOP_API_KEY privately through your environment, or use Start-Launcher.ps1 to reuse the protected Conductor credential. No key files are included.

Example:

`powershell -ExecutionPolicy Bypass -File ./nova-codex-interactive.ps1 -Model gpt-oss:20b -Workspace C:/Projects/example -BaseUrl http://127.0.0.1:8788 -ContextTokens 16384`

The GUI starts the bundled [NOVA Codex Proxy](https://github.com/InversoLabs/nova-codex-proxy) when port 8788 is not already available. Command-line users should start it separately. Conductor and Director bundle their own launcher copy.
