import os
import re
import json
import time
import gradio as gr
from dotenv import load_dotenv
from google import genai

# ---------------------------------------------------------------------------
# API Key — loaded from .env file (gitignored)
# ---------------------------------------------------------------------------
load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found. Add it to your .env file.")
client = genai.Client(api_key=GEMINI_API_KEY)

# ---------------------------------------------------------------------------
# Models & Languages
# ---------------------------------------------------------------------------
MODELS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]

LANGUAGES = [
    "Python", "Java", "C++", "C", "JavaScript", "TypeScript",
    "Go", "Rust", "C#", "Kotlin", "Swift", "Ruby", "PHP",
]

# ---------------------------------------------------------------------------
# Prompt — pure I/O test cases, zero code
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a test-case generator that produces xUnit-style unit tests following the Arrange-Act-Assert (AAA) pattern.

RULES:
1. Return ONLY a valid raw JSON array. No markdown fences, no commentary.
2. Each object must have exactly these keys:
   "id"              -> integer starting from 0
   "title"           -> short label (e.g. "Positive integers")
   "category"        -> one of: Basic | Edge Case | Boundary | Negative | Error Handling
   "input"           -> function parameters or stdin values
   "expected_output" -> exact return value or stdout
   "explanation"     -> one sentence on what this tests
   "test_code"       -> complete xUnit test method in the requested language,
                        using the Arrange-Act-Assert pattern with explicit
                        // Arrange, // Act, // Assert comments.
                        For C# use xUnit [Fact]; for Java use JUnit @Test;
                        for Python use pytest; for JavaScript/TypeScript use Jest;
                        for other languages use the closest xUnit-family framework.
3. Generate 6-8 diverse test cases.
4. The test_code MUST follow this structure:
   // Arrange  — set up inputs and expected values
   // Act      — call the function / method under test
   // Assert   — verify the result matches expected output
"""

CODE_PROMPT = """Generate xUnit-style unit test cases (Arrange-Act-Assert) for this {language} code.
Return ONLY the raw JSON array. Each object must include a "test_code" field
containing a complete test method using the appropriate xUnit framework for {language},
with // Arrange, // Act, // Assert comments.

{code}"""

DESC_PROMPT = """Generate test cases for this feature.
Return ONLY the raw JSON array.

{description}"""

# ---------------------------------------------------------------------------
# JSON parser
# ---------------------------------------------------------------------------
def parse_cases(raw: str):
    if not raw:
        return None
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE)
    text = text.strip()
    try:
        data = json.loads(text)
        if isinstance(data, list) and data:
            return data
    except Exception:
        pass
    m = re.search(r"\[\s*\{.*\}\s*\]", text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group())
            if isinstance(data, list) and data:
                return data
        except Exception:
            pass
    return None

# ---------------------------------------------------------------------------
# Escape helper
# ---------------------------------------------------------------------------
def esc(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )

# ---------------------------------------------------------------------------
# Category colours
# ---------------------------------------------------------------------------
CAT = {
    "Basic":          ("#68BA7F", "rgba(104,186,127,.12)", "rgba(104,186,127,.35)"),
    "Edge Case":      ("#f59e0b", "rgba(245,158,11,.12)",  "rgba(245,158,11,.35)"),
    "Boundary":       ("#CFFFDC", "rgba(207,255,220,.15)", "rgba(207,255,220,.35)"),
    "Negative":       ("#fb7185", "rgba(251,113,133,.12)", "rgba(251,113,133,.35)"),
    "Error Handling": ("#c084fc", "rgba(192,132,252,.12)", "rgba(192,132,252,.35)"),
}

# ---------------------------------------------------------------------------
# Build test-case viewer HTML
# ---------------------------------------------------------------------------
def build_html(cases):
    sidebar = ""
    panels = ""

    for idx, tc in enumerate(cases):
        title = esc(tc.get("title", f"Test Case {idx}"))
        cat   = tc.get("category", "Basic")
        inp   = esc(str(tc.get("input", "")))
        out   = esc(str(tc.get("expected_output", "")))
        expl  = esc(str(tc.get("explanation", "")))
        code  = esc(str(tc.get("test_code", "")))

        col, bg, bdr = CAT.get(cat, CAT["Basic"])
        active   = " active" if idx == 0 else ""
        display  = "block" if idx == 0 else "none"

        switch = (
            f"var r=this.closest('.tcv');"
            f"r.querySelectorAll('.si').forEach(e=>e.classList.remove('active'));"
            f"r.querySelectorAll('.pn').forEach(e=>e.style.display='none');"
            f"this.classList.add('active');"
            f"var p=r.querySelector('#pn{idx}');if(p)p.style.display='block';"
        )

        sidebar += f"""
        <div class="si{active}" onclick="{switch}">
            <span class="sn" style="background:{bg};color:{col};border:1px solid {bdr};">{idx}</span>
            <div class="sm">
                <span class="sl">Test case {idx}</span>
                <span class="sc" style="color:{col};">{cat}</span>
            </div>
        </div>"""

        # Build the test code section (collapsible)
        code_section = ""
        if code:
            code_section = f"""
            <div class="code-section">
                <div class="code-header" onclick="var b=this.nextElementSibling;var a=this.querySelector('.chevron');if(b.style.display==='none'){{b.style.display='block';a.textContent='▾';}}else{{b.style.display='none';a.textContent='▸';}}">
                    <span class="code-title">🧪 Unit Test Code (xUnit · Arrange-Act-Assert)</span>
                    <span class="chevron">▾</span>
                </div>
                <pre class="code-body">{code}</pre>
            </div>"""

        panels += f"""
        <div id="pn{idx}" class="pn" style="display:{display};">
            <div class="pt">{title}</div>
            <span class="ct" style="background:{bg};color:{col};border:1px solid {bdr};">{cat}</span>

            <div class="iobox">
                <div class="iolbl">Input</div>
                <pre class="ioval">{inp}</pre>
            </div>

            <div class="iobox ob">
                <div class="iolbl" style="color:#22d3ee;">Expected Output</div>
                <pre class="ioval eo">{out}</pre>
            </div>

            {"<div class='expl'>" + expl + "</div>" if expl else ""}

            {code_section}
        </div>"""

    return f"""
<div class="tcv">
  <div class="topbar">
    <span class="tbt">Test Results</span>
    <span class="tbc">{len(cases)} cases</span>
  </div>
  <div class="body">
    <div class="sidebar">{sidebar}</div>
    <div class="detail">{panels}</div>
  </div>
</div>"""

# ---------------------------------------------------------------------------
# Generate handler
# ---------------------------------------------------------------------------
def generate(input_type, code_or_desc, language, model):
    if not code_or_desc or not code_or_desc.strip():
        return '<div class="err">Please enter a code snippet or feature description.</div>'

    prompt = (
        CODE_PROMPT.format(language=language, code=code_or_desc.strip())
        if input_type == "Code Snippet"
        else DESC_PROMPT.format(description=code_or_desc.strip())
    )

    models_to_try = [model] + [m for m in MODELS if m != model]
    last_err = ""

    for m in models_to_try:
        for attempt in range(2):
            try:
                resp = client.models.generate_content(
                    model=m,
                    contents=prompt,
                    config=genai.types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.2,
                        max_output_tokens=3000,
                    ),
                )
                raw = resp.text or ""
                if not raw.strip():
                    break

                cases = parse_cases(raw)
                if cases:
                    return build_html(cases)
                else:
                    last_err = "Unexpected model output format."
            except Exception as e:
                last_err = str(e)
                if "429" in last_err or "RESOURCE_EXHAUSTED" in last_err:
                    time.sleep(3)
                    continue
                if "404" in last_err or "NOT_FOUND" in last_err:
                    break
                break

    return f'<div class="err">Generation failed: {esc(last_err[:250])}</div>'

# ---------------------------------------------------------------------------
# CSS — dark navy + soft cyan, simple & clean
# ---------------------------------------------------------------------------
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ---- base ---- */
body, .gradio-container {
    background: #1a2e22 !important;
    font-family: 'Inter', sans-serif !important;
    color: #CFFFDC !important;
}
.gradio-container {
    max-width: 1100px !important;
    margin: 0 auto !important;
}

/* ---- header ---- */
#hdr {
    text-align: center;
    padding: 28px 16px 20px;
}
#hdr h1 {
    font-size: 28px;
    font-weight: 800;
    color: #CFFFDC;
    margin: 0 0 6px;
}
#hdr h1 span {
    background: linear-gradient(135deg, #68BA7F, #CFFFDC);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
#hdr p {
    color: #8fbf9a;
    font-size: 14px;
    margin: 0;
}

/* ---- config panel ---- */
.cfg {
    background: #253D2C !important;
    border: 1px solid rgba(104,186,127,.25) !important;
    border-radius: 14px !important;
    padding: 18px !important;
}

/* ---- form element text colours ---- */
label, .gr-form label, span.text-gray-500 {
    color: #8fbf9a !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}
input, select, textarea, .gr-input, .gr-box {
    background: #1a2e22 !important;
    color: #CFFFDC !important;
    border: 1px solid rgba(104,186,127,.35) !important;
    border-radius: 10px !important;
}
input:focus, select:focus, textarea:focus {
    border-color: #68BA7F !important;
    box-shadow: 0 0 0 2px rgba(104,186,127,.25) !important;
}

/* ---- code input ---- */
#code-in textarea {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    background: #1a2e22 !important;
    color: #CFFFDC !important;
    border: 1px solid rgba(104,186,127,.25) !important;
    border-radius: 12px !important;
    padding: 14px !important;
}
#code-in textarea::placeholder {
    color: #5a8a65 !important;
}

/* ---- generate button ---- */
#gen-btn {
    background: linear-gradient(135deg, #2E6F40, #68BA7F) !important;
    color: #fff !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 14px !important;
    box-shadow: 0 4px 18px rgba(46,111,64,.4) !important;
    transition: all .2s ease !important;
}
#gen-btn:hover {
    box-shadow: 0 6px 24px rgba(46,111,64,.6) !important;
    transform: translateY(-1px) !important;
}

/* ---- footer ---- */
#ftr {
    text-align: center;
    color: #5a8a65;
    font-size: 12px;
    padding: 18px 0 6px;
}
#ftr a { color: #68BA7F; text-decoration: none; }

/* ==============================================================
   TEST CASE VIEWER
   ============================================================== */
.tcv {
    background: #253D2C;
    border: 1px solid rgba(104,186,127,.25);
    border-radius: 14px;
    overflow: hidden;
    margin-top: 12px;
    box-shadow: 0 8px 28px rgba(0,0,0,.35);
}
.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 18px;
    background: #1e3326;
    border-bottom: 1px solid rgba(104,186,127,.15);
}
.tbt { font-size: 14px; font-weight: 700; color: #CFFFDC; }
.tbc {
    font-size: 11px; font-weight: 700; color: #68BA7F;
    background: rgba(104,186,127,.12);
    border: 1px solid rgba(104,186,127,.3);
    border-radius: 20px;
    padding: 2px 10px;
}

/* split layout */
.body { display: flex; min-height: 380px; }

/* sidebar */
.sidebar {
    width: 200px; min-width: 200px;
    background: #1e3326;
    border-right: 1px solid rgba(104,186,127,.12);
    padding: 10px 6px;
    overflow-y: auto;
}
.si {
    display: flex; align-items: center; gap: 8px;
    padding: 9px 10px; margin-bottom: 3px;
    border-radius: 8px; cursor: pointer;
    border: 1px solid transparent;
    transition: all .12s ease;
}
.si:hover { background: rgba(46,111,64,.25); border-color: rgba(104,186,127,.2); }
.si.active {
    background: rgba(46,111,64,.3);
    border-color: rgba(104,186,127,.5);
}
.sn {
    width: 26px; height: 26px;
    border-radius: 7px;
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    flex-shrink: 0;
}
.sm { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.sl { font-size: 13px; font-weight: 600; color: #CFFFDC; white-space: nowrap; }
.sc { font-size: 10px; font-weight: 600; letter-spacing: .3px; }

/* detail area */
.detail {
    flex: 1; padding: 22px 26px;
    background: #253D2C;
    overflow-y: auto;
}
.pn { animation: fadeIn .18s ease; }
@keyframes fadeIn {
    from { opacity:0; transform:translateY(3px); }
    to   { opacity:1; transform:none; }
}
.pt { font-size: 17px; font-weight: 700; color: #CFFFDC; margin-bottom: 8px; }
.ct {
    display: inline-block;
    padding: 3px 12px; border-radius: 20px;
    font-size: 11px; font-weight: 700;
    text-transform: uppercase; letter-spacing: .4px;
    margin-bottom: 18px;
}

/* input / output boxes */
.iobox {
    background: #1e3326;
    border: 1px solid rgba(104,186,127,.18);
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 12px;
}
.ob { border-color: rgba(104,186,127,.35); background: #1a2e22; }
.iolbl {
    padding: 8px 14px;
    font-size: 11px; font-weight: 700;
    text-transform: uppercase; letter-spacing: .6px;
    color: #8fbf9a;
    background: #1a2e22;
    border-bottom: 1px solid rgba(104,186,127,.15);
}
.ioval {
    margin: 0; padding: 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px; line-height: 1.5;
    color: #CFFFDC;
    white-space: pre-wrap; word-break: break-all;
}
.eo { color: #68BA7F; font-weight: 600; }

/* explanation */
.expl {
    padding: 10px 14px;
    border-radius: 8px;
    background: rgba(30,51,38,.7);
    border: 1px solid rgba(104,186,127,.15);
    font-size: 13px; color: #8fbf9a;
    line-height: 1.4;
    margin-top: 4px;
}

/* ---- test code section ---- */
.code-section {
    margin-top: 14px;
    border: 1px solid rgba(104,186,127,.25);
    border-radius: 10px;
    overflow: hidden;
    background: #1a2e22;
}
.code-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    background: #1e3326;
    cursor: pointer;
    border-bottom: 1px solid rgba(104,186,127,.15);
    user-select: none;
    transition: background .15s ease;
}
.code-header:hover {
    background: rgba(46,111,64,.3);
}
.code-title {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .5px;
    color: #68BA7F;
}
.chevron {
    font-size: 14px;
    color: #68BA7F;
    transition: transform .15s ease;
}
.code-body {
    margin: 0;
    padding: 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    line-height: 1.65;
    color: #CFFFDC;
    white-space: pre-wrap;
    word-break: break-all;
    background: #141f18;
    border-top: 1px solid rgba(104,186,127,.1);
}

/* error */
.err {
    padding: 18px; border-radius: 10px;
    background: #2a1a1a; border: 1px solid rgba(248,113,113,.3);
    color: #fca5a5; font-size: 14px; text-align: center;
    margin-top: 12px;
}
"""

# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------
with gr.Blocks(title="Intelligent Test Case Generator") as demo:

    gr.HTML("""
    <div id="hdr">
        <h1>Intelligent <span>Test Case</span> Generator</h1>
        <p>Generate input / output test cases for your code — powered by AI</p>
    </div>
    """)

    with gr.Row(equal_height=False):

        with gr.Column(scale=1, min_width=240):
            with gr.Group(elem_classes="cfg"):
                model_dd = gr.Dropdown(
                    label="Model",
                    choices=MODELS,
                    value=MODELS[0],
                )
                input_type = gr.Radio(
                    label="Input Type",
                    choices=["Code Snippet", "Feature Description"],
                    value="Code Snippet",
                )
                lang_dd = gr.Dropdown(
                    label="Language",
                    choices=LANGUAGES,
                    value="Python",
                )

        with gr.Column(scale=3):
            code_input = gr.Textbox(
                label="Code Snippet / Feature Description",
                placeholder="Paste your code here…",
                lines=10,
                elem_id="code-in",
            )
            gen_btn = gr.Button("⚡ Generate Test Cases", elem_id="gen-btn", variant="primary")
            output = gr.HTML()

    gen_btn.click(
        fn=generate,
        inputs=[input_type, code_input, lang_dd, model_dd],
        outputs=output,
    )

    gr.HTML("""
    <div id="ftr">
        Built with <a href="https://gradio.app">Gradio</a> &amp; Google Gemini &nbsp;|&nbsp; CA-3 Mini Project
    </div>
    """)

 if __name__ == "__main__":
       demo.launch(
           server_name="0.0.0.0",
           server_port=int(os.environ.get("PORT", 7860)),
           css=CSS,
       )
