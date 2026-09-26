using System.Diagnostics;
using System.Net.Http.Headers;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;

namespace NovaCodexLauncher;

internal static class Program
{
    [STAThread]
    static void Main()
    {
        ApplicationConfiguration.Initialize();
        Application.Run(new LauncherForm());
    }
}

internal sealed class LauncherForm : Form
{
    private readonly ComboBox _model = new() { DropDownStyle = ComboBoxStyle.DropDownList };
    private readonly ComboBox _baseUrl = new() { DropDownStyle = ComboBoxStyle.DropDown };
    private readonly ComboBox _reasoning = new() { DropDownStyle = ComboBoxStyle.DropDownList };
    private readonly ComboBox _context = new() { DropDownStyle = ComboBoxStyle.DropDownList };
    private readonly ComboBox _sandbox = new() { DropDownStyle = ComboBoxStyle.DropDownList };
    private readonly TextBox _workspace = new();
    private readonly TextBox _apiKey = new() { UseSystemPasswordChar = true };
    private readonly TextBox _pullTag = new() { PlaceholderText = "Example: qwen2.5-coder:7b" };
    private readonly Label _status = new() { AutoSize = false, TextAlign = ContentAlignment.MiddleLeft };
    private readonly Button _refresh = new() { Text = "Refresh models" };
    private readonly Button _pull = new() { Text = "Pull model" };
    private readonly Button _launch = new() { Text = "Launch Codex" };
    private const string GemmaChoice = "Gemma E2B - trained pilot + compact adapter";
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromMinutes(30) };
    private readonly string _toolsDirectory = Directory.GetParent(AppContext.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar))?.FullName ?? AppContext.BaseDirectory;

    public LauncherForm()
    {
        Text = "NOVA Codex Launcher � Gemma 4K / 8K / 16K / 32K";
        StartPosition = FormStartPosition.CenterScreen;
        MinimumSize = new Size(680, 640);
        Size = new Size(760, 720);
        BackColor = Color.FromArgb(10, 11, 17);
        ForeColor = Color.FromArgb(232, 234, 244);
        Font = new Font("Segoe UI Variable Text", 10f);

        _baseUrl.Items.AddRange(["http://127.0.0.1:8788", "http://192.168.86.51:8787", "https://nova.inversolabs.us"]);
        _baseUrl.Text = "http://127.0.0.1:8788";
        _reasoning.Items.AddRange(["minimal", "low", "medium", "high"]);
        _reasoning.SelectedIndex = 0;
        _context.Items.AddRange(["4K · Low memory", "8K · Recommended", "12K · Long", "16K · Experimental", "32K · Gemma testing"]);
        _context.SelectedIndex = 1;
        _sandbox.Items.AddRange(["workspace-write", "read-only"]);
        _sandbox.SelectedIndex = 0;
        _workspace.Text = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Desktop), "codex");
        _model.Items.Add(GemmaChoice);
        _model.SelectedIndex = 0;
        _model.SelectedIndexChanged += (_, _) =>
        {
            var gemma = _model.SelectedItem?.ToString() == GemmaChoice;
            _reasoning.Enabled = !gemma;
            if (gemma) { _context.SelectedIndex = 1; SetStatus("Trained Gemma pilot through your existing NOVA URL and API key."); }
        };

        var title = new Label { Text = "NOVA // CODEX", Font = new Font("Segoe UI Variable Display", 22, FontStyle.Bold), AutoSize = true, ForeColor = Color.FromArgb(126, 113, 255) };
        var subtitle = new Label { Text = "Select a NOVA-hosted model and launch a configured Codex session.", AutoSize = true, ForeColor = Color.FromArgb(155, 160, 180) };
        var browse = Button("Browse…", (_, _) => BrowseWorkspace());
        _refresh.Click += async (_, _) => await RefreshModelsAsync();
        _pull.Click += async (_, _) => await PullModelAsync();
        _launch.Click += (_, _) => LaunchCodex();

        Style(_model); Style(_baseUrl); Style(_reasoning); Style(_context); Style(_sandbox); Style(_workspace); Style(_apiKey); Style(_pullTag);
        Style(_refresh); Style(_pull); Style(_launch); Style(browse);
        _launch.BackColor = Color.FromArgb(93, 79, 230);
        _launch.ForeColor = Color.White;
        _launch.Height = 48;
        _status.ForeColor = Color.FromArgb(94, 196, 255);

        var layout = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(30), ColumnCount = 3, RowCount = 13 };
        layout.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 150));
        layout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        layout.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 125));
        for (var i = 0; i < 13; i++) layout.RowStyles.Add(new RowStyle(i is 0 or 1 ? SizeType.AutoSize : SizeType.Absolute, i is 0 or 1 ? 0 : 48));
        layout.Controls.Add(title, 0, 0); layout.SetColumnSpan(title, 3);
        layout.Controls.Add(subtitle, 0, 1); layout.SetColumnSpan(subtitle, 3);
        AddRow(layout, 2, "NOVA URL", _baseUrl);
        AddRow(layout, 3, "API key", _apiKey);
        AddRow(layout, 4, "Installed model", _model, _refresh);
        AddRow(layout, 5, "Pull model tag", _pullTag, _pull);
        AddRow(layout, 6, "Workspace", _workspace, browse);
        AddRow(layout, 7, "Permissions", _sandbox);
        AddRow(layout, 8, "Reasoning", _reasoning);
        AddRow(layout, 9, "Context", _context);
        layout.Controls.Add(_status, 0, 10); layout.SetColumnSpan(_status, 3);
        layout.Controls.Add(_launch, 0, 11); layout.SetColumnSpan(_launch, 3);
        Controls.Add(layout);

        Shown += async (_, _) =>
        {
            var existing = Environment.GetEnvironmentVariable("NOVA_DESKTOP_API_KEY");
            if (!string.IsNullOrWhiteSpace(existing)) _apiKey.Text = existing;
            if (!Directory.Exists(_workspace.Text)) Directory.CreateDirectory(_workspace.Text);
            if (!string.IsNullOrWhiteSpace(_apiKey.Text)) await RefreshModelsAsync();
            if (_model.SelectedItem?.ToString() == GemmaChoice)
            {
                _reasoning.Enabled = false;
                var requestedContext = Environment.GetEnvironmentVariable("NOVA_LAUNCH_CONTEXT");
                if (requestedContext == "32768") _context.SelectedIndex = 4;
                else if (requestedContext == "16384") _context.SelectedIndex = 3;
                else if (requestedContext == "4096") _context.SelectedIndex = 0;
                SetStatus("Trained Gemma pilot through your existing NOVA URL and API key.");
            }
        };
    }

    private static void AddRow(TableLayoutPanel layout, int row, string label, Control field, Control? action = null)
    {
        layout.Controls.Add(new Label { Text = label, Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleLeft, ForeColor = Color.FromArgb(178, 182, 200) }, 0, row);
        field.Dock = DockStyle.Fill; layout.Controls.Add(field, 1, row);
        if (action != null) { action.Dock = DockStyle.Fill; layout.Controls.Add(action, 2, row); }
        else layout.SetColumnSpan(field, 2);
    }

    private static Button Button(string text, EventHandler click) { var b = new Button { Text = text }; b.Click += click; return b; }
    private static void Style(Control c)
    {
        c.BackColor = Color.FromArgb(27, 29, 39); c.ForeColor = Color.FromArgb(232, 234, 244);
        if (c is Button b) { b.FlatStyle = FlatStyle.Flat; b.FlatAppearance.BorderColor = Color.FromArgb(55, 58, 75); }
    }

    private void BrowseWorkspace()
    {
        using var dialog = new FolderBrowserDialog { InitialDirectory = Directory.Exists(_workspace.Text) ? _workspace.Text : Environment.GetFolderPath(Environment.SpecialFolder.Desktop) };
        if (dialog.ShowDialog(this) == DialogResult.OK) _workspace.Text = dialog.SelectedPath;
    }

    private HttpRequestMessage Request(HttpMethod method, string route, string? json = null)
    {
        var request = new HttpRequestMessage(method, _baseUrl.Text.TrimEnd('/') + route);
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", _apiKey.Text.Trim());
        if (json != null) request.Content = new StringContent(json, Encoding.UTF8, "application/json");
        return request;
    }

    private async Task RefreshModelsAsync()
    {
        if (string.IsNullOrWhiteSpace(_apiKey.Text)) { SetStatus("Enter the NOVA API key first.", true); return; }
        if (!EnsureCompatibilityProxy()) return;
        await BusyAsync(_refresh, "Loading…", async () =>
        {
            using var response = await _http.SendAsync(Request(HttpMethod.Get, "/models"));
            var body = await response.Content.ReadAsStringAsync();
            if (!response.IsSuccessStatusCode) throw new InvalidOperationException($"NOVA returned {(int)response.StatusCode}: {Safe(body)}");
            using var doc = JsonDocument.Parse(body);
            var names = ReadModelNames(doc.RootElement).Where(x => !x.StartsWith("gemma4-codex:pilot-v1", StringComparison.OrdinalIgnoreCase)).Distinct(StringComparer.OrdinalIgnoreCase).OrderBy(x => x).ToArray();
            var previous = _model.SelectedItem?.ToString();
            _model.Items.Clear(); _model.Items.Add(GemmaChoice); _model.Items.AddRange(names);
            if (previous != null && _model.Items.Contains(previous)) _model.SelectedItem = previous;
            else if (_model.Items.Count > 0) _model.SelectedIndex = 0;
            SetStatus($"Connected. Found {names.Length} installed model{(names.Length == 1 ? "" : "s")}.");
        });
    }

    private static IEnumerable<string> ReadModelNames(JsonElement root)
    {
        JsonElement models;
        if (root.ValueKind == JsonValueKind.Array) models = root;
        else if (!root.TryGetProperty("models", out models) && !root.TryGetProperty("data", out models)) yield break;
        foreach (var item in models.EnumerateArray())
        {
            if (item.ValueKind == JsonValueKind.String) { yield return item.GetString()!; continue; }
            foreach (var key in new[] { "name", "model", "id" })
                if (item.TryGetProperty(key, out var value) && value.ValueKind == JsonValueKind.String) { yield return value.GetString()!; break; }
        }
    }

    private async Task PullModelAsync()
    {
        var tag = _pullTag.Text.Trim();
        if (string.IsNullOrWhiteSpace(tag)) { SetStatus("Enter an Ollama model tag to pull.", true); return; }
        await BusyAsync(_pull, "Pulling…", async () =>
        {
            var json = JsonSerializer.Serialize(new { model = tag });
            using var response = await _http.SendAsync(Request(HttpMethod.Post, "/models/pull", json));
            var body = await response.Content.ReadAsStringAsync();
            if (!response.IsSuccessStatusCode) throw new InvalidOperationException($"Pull failed ({(int)response.StatusCode}): {Safe(body)}");
            SetStatus($"Installed {tag}."); _pullTag.Clear(); await RefreshModelsAsync();
        });
    }

    private async Task BusyAsync(Button button, string busyText, Func<Task> work)
    {
        var old = button.Text; button.Enabled = false; button.Text = busyText; UseWaitCursor = true;
        try { await work(); } catch (Exception ex) { SetStatus(ex.Message, true); }
        finally { button.Text = old; button.Enabled = true; UseWaitCursor = false; }
    }

    private void LaunchCodex()
    {
        var selected = _model.SelectedItem?.ToString();
        if (string.IsNullOrWhiteSpace(selected)) { SetStatus("Select an installed model.", true); return; }
        var gemma = selected == GemmaChoice;
        if (string.IsNullOrWhiteSpace(_apiKey.Text)) { SetStatus("Enter the NOVA API key.", true); return; }
        if (!Directory.Exists(_workspace.Text)) { SetStatus("The workspace folder does not exist.", true); return; }
        if (RemoteCodexIsRunning()) { SetStatus("A NOVA Codex session is already running. Close it before starting another.", true); return; }
        if (!EnsureCompatibilityProxy()) return;
        var script = Path.Combine(_toolsDirectory, "nova-codex-interactive.ps1");
        if (!File.Exists(script)) { SetStatus($"Launcher script is missing: {script}", true); return; }
        var contextTokens = _context.SelectedIndex switch { 0 => 4096, 2 => 12288, 3 => 16384, 4 => 32768, _ => 8192 };
        if (gemma && contextTokens == 12288) { SetStatus("For Gemma select 4K, 8K, 16K or 32K.", true); return; }
        if (!gemma && contextTokens == 32768) { SetStatus("32K testing is currently configured for Gemma only.", true); return; }
        if (gemma) selected = "gemma4-codex:pilot-v1";
        var args = $"-NoExit -NoProfile -ExecutionPolicy Bypass -File {Q(script)} -Model {Q(selected)} -Workspace {Q(_workspace.Text)} -BaseUrl {Q(_baseUrl.Text.TrimEnd('/'))} -Sandbox {Q(_sandbox.Text)} -Reasoning {Q(_reasoning.Text)} -ContextTokens {contextTokens}";
        var start = new ProcessStartInfo("powershell.exe", args) { UseShellExecute = false, CreateNoWindow = false, WorkingDirectory = _workspace.Text };
        start.Environment["NOVA_DESKTOP_API_KEY"] = _apiKey.Text.Trim();
        Process.Start(start);
        SetStatus($"Started Codex with {selected} at {contextTokens / 1024}K context. The API key was passed only to that process.");
    }

    private bool EnsureCompatibilityProxy()
    {
        if (!_baseUrl.Text.TrimEnd('/').Equals("http://127.0.0.1:8788", StringComparison.OrdinalIgnoreCase)) return true;
        if (CanConnect(8788)) return true;
        var proxy = Path.Combine(_toolsDirectory, "nova-codex-proxy.js");
        if (!File.Exists(proxy)) { SetStatus($"Compatibility proxy is missing: {proxy}", true); return false; }
        try
        {
            Process.Start(new ProcessStartInfo("node.exe", Q(proxy))
            {
                UseShellExecute = false,
                CreateNoWindow = true,
                WindowStyle = ProcessWindowStyle.Hidden,
                WorkingDirectory = _toolsDirectory,
            });
            var deadline = DateTime.UtcNow.AddSeconds(10);
            while (DateTime.UtcNow < deadline)
            {
                Thread.Sleep(200);
                if (CanConnect(8788)) return true;
            }
            SetStatus("The NOVA compatibility proxy did not start on port 8788.", true);
        }
        catch (Exception ex) { SetStatus($"Could not start the compatibility proxy: {ex.Message}", true); }
        return false;
    }

    private static bool CanConnect(int port)
    {
        try
        {
            using var client = new TcpClient();
            return client.ConnectAsync("127.0.0.1", port).Wait(TimeSpan.FromMilliseconds(300));
        }
        catch { return false; }
    }

    private static bool RemoteCodexIsRunning()
    {
        try
        {
            using var session = Mutex.OpenExisting(@"Local\NOVA.Codex.Remote.Session");
            try
            {
                if (!session.WaitOne(0)) return true;
                session.ReleaseMutex();
                return false;
            }
            catch (AbandonedMutexException)
            {
                session.ReleaseMutex();
                return false;
            }
        }
        catch (WaitHandleCannotBeOpenedException)
        {
            return false;
        }
    }

    private static string Q(string value) => "\"" + value.Replace("\"", "\\\"") + "\"";
    private static string Safe(string value) => value.Length <= 300 ? value : value[..300] + "…";
    private void SetStatus(string text, bool error = false) { _status.Text = text; _status.ForeColor = error ? Color.FromArgb(255, 120, 140) : Color.FromArgb(94, 196, 255); }
}
