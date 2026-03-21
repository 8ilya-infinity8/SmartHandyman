"""Custom Streamlit Web Interface for SmartHandyman."""

import streamlit as st
import streamlit.components.v1 as components

from config import ACTIVE_API_KEY, LLM_PROVIDER
from diagnostic_agent import DiagnosticAgent
from instruction_generator import InstructionGenerator
from safety_checker import SafetyChecker
from shopping_agent import ShoppingAgent
from vision_analyzer import VisionAnalyzer

# Page configuration
st.set_page_config(
    page_title="SmartHandyman",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main background with gradient */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        min-height: 100vh;
    }
    
    /* Hide default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Keep Streamlit header functional for sidebar toggle */
    [data-testid="stHeader"] {
        background: transparent;
    }
    
    /* Header */
    .main-header {
        background: linear-gradient(90deg, #00d9ff, #00ff88);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        color: #e2e8f0;
        font-size: 1.1rem;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Cards */
    .card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }
    
    .card-title {
        color: #00d9ff;
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, rgba(0, 217, 255, 0.15), rgba(0, 255, 136, 0.1));
        color: #e2e8f0 !important;
        border: 1px solid rgba(0, 217, 255, 0.35);
        border-radius: 10px;
        padding: 0.5rem 1.4rem;
        min-height: 2.4rem;
        font-weight: 600;
        font-size: 0.9rem;
        letter-spacing: 0.3px;
        transition: all 0.2s ease;
        box-shadow: 0 0 12px rgba(0, 217, 255, 0.08);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(0, 217, 255, 0.28), rgba(0, 255, 136, 0.2));
        border-color: rgba(0, 217, 255, 0.7);
        box-shadow: 0 0 20px rgba(0, 217, 255, 0.25);
        transform: translateY(-1px);
    }

    .stButton > button:active {
        transform: translateY(0px);
        box-shadow: 0 0 10px rgba(0, 217, 255, 0.15);
    }

    /* Primary buttons */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #00d9ff, #00ff88);
        color: #1a1a2e !important;
        border: none;
        box-shadow: 0 0 20px rgba(0, 217, 255, 0.3);
    }

    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #33e1ff, #33ff9f);
        box-shadow: 0 0 30px rgba(0, 217, 255, 0.5);
        transform: translateY(-1px);
    }

    /* Form submit buttons (st.form_submit_button) */
    [data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, rgba(0, 217, 255, 0.15), rgba(0, 255, 136, 0.1));
        color: #e2e8f0 !important;
        border: 1px solid rgba(0, 217, 255, 0.35);
        border-radius: 10px;
        padding: 0.5rem 1.4rem;
        min-height: 2.4rem;
        font-weight: 600;
        font-size: 0.9rem;
        letter-spacing: 0.3px;
        transition: all 0.2s ease;
        box-shadow: 0 0 12px rgba(0, 217, 255, 0.08);
    }

    [data-testid="stFormSubmitButton"] > button:hover {
        background: linear-gradient(135deg, rgba(0, 217, 255, 0.28), rgba(0, 255, 136, 0.2));
        border-color: rgba(0, 217, 255, 0.7);
        box-shadow: 0 0 20px rgba(0, 217, 255, 0.25);
        transform: translateY(-1px);
    }

    [data-testid="stFormSubmitButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #00d9ff, #00ff88);
        color: #1a1a2e !important;
        border: none;
        box-shadow: 0 0 20px rgba(0, 217, 255, 0.3);
    }

    [data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #33e1ff, #33ff9f);
        box-shadow: 0 0 30px rgba(0, 217, 255, 0.5);
        transform: translateY(-1px);
    }

    [data-testid="stFormSubmitButton"] > button p,
    [data-testid="stFormSubmitButton"] > button span,
    [data-testid="stFormSubmitButton"] > button div {
        color: inherit !important;
    }

    /* Browse files button — force dark text on light uploader background */
    [data-testid="stFileUploaderDropzone"] button {
        color: #1a1a2e !important;
        background: rgba(0, 0, 0, 0.07) !important;
        border-color: rgba(0, 0, 0, 0.18) !important;
        box-shadow: none !important;
        transform: none !important;
    }

    [data-testid="stFileUploaderDropzone"] button:hover {
        background: rgba(0, 0, 0, 0.13) !important;
        border-color: rgba(0, 0, 0, 0.3) !important;
        transform: none !important;
        box-shadow: none !important;
    }

    [data-testid="stFileUploaderDropzone"] button span,
    [data-testid="stFileUploaderDropzone"] button p {
        color: #1a1a2e !important;
    }
    /* Progress bar */
    .progress-container {
        position: relative;
        margin: 1rem 0 2rem;
        padding: 0.2rem 0 0.4rem;
    }
    
    .progress-steps {
        display: grid;
        grid-template-columns: repeat(6, minmax(0, 1fr));
        gap: 0;
        position: relative;
    }
    
    .progress-line {
        position: absolute;
        top: 20px;
        left: calc(100% / 12);
        right: calc(100% / 12);
        height: 3px;
        background: rgba(255, 255, 255, 0.1);
        z-index: 1;
        border-radius: 999px;
    }
    
    .progress-fill {
        position: absolute;
        top: 20px;
        left: calc(100% / 12);
        height: 3px;
        background: linear-gradient(90deg, #00d9ff, #00ff88);
        z-index: 2;
        transition: width 0.5s ease;
        border-radius: 999px;
    }
    
    .step {
        position: relative;
        z-index: 3;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.5rem;
    }
    
    .step-circle {
        width: 52px;
        height: 52px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.1);
        border: 2px solid rgba(255, 255, 255, 0.25);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        color: #a0aec0;
        transition: all 0.3s ease;
        box-shadow: 0 0 18px rgba(0, 217, 255, 0.08);
        font-size: 1.05rem;
    }
    
    .step.active .step-circle {
        background: linear-gradient(135deg, #00d9ff, #00ff88);
        border-color: transparent;
        color: #1a1a2e;
        transform: scale(1.08);
        box-shadow: 0 0 28px rgba(0, 217, 255, 0.45);
    }
    
    .step.completed .step-circle {
        background: #00ff88;
        border-color: #00ff88;
        color: #1a1a2e;
        box-shadow: 0 0 24px rgba(0, 255, 136, 0.35);
    }
    
    .step-label {
        color: #e2e8f0;
        font-size: 0.95rem;
        font-weight: 500;
        text-align: center;
        max-width: 110px;
    }
    
    .step.active .step-label {
        color: #00d9ff;
        text-shadow: 0 0 8px rgba(0, 217, 255, 0.35);
    }
    
    .step.completed .step-label {
        color: #00ff88;
        text-shadow: 0 0 8px rgba(0, 255, 136, 0.35);
    }
    
    /* Alert boxes */
    .warning-box {
        background: rgba(255, 193, 7, 0.15);
        border: 1px solid rgba(255, 193, 7, 0.4);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #fbbf24;
    }
    
    .danger-box {
        background: rgba(244, 67, 54, 0.15);
        border: 1px solid rgba(244, 67, 54, 0.4);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #f87171;
    }
    
    .success-box {
        background: rgba(76, 175, 80, 0.15);
        border: 1px solid rgba(76, 175, 80, 0.4);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #4ade80;
    }
    
    .info-box {
        background: rgba(0, 217, 255, 0.15);
        border: 1px solid rgba(0, 217, 255, 0.4);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #67e8f9;
    }
    
    /* Metrics */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
        min-width: 150px;
    }

    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #00d9ff;
        word-wrap: break-word;
        overflow-wrap: break-word;
        max-width: 100%;
        display: block;
        line-height: 1.3;
    }
    
    .metric-label {
        color: #e2e8f0;
        font-size: 0.85rem;
        margin-top: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* List styling */
    .custom-list {
        list-style: none;
        padding: 0;
    }
    
    .custom-list li {
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        background: rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        border-left: 3px solid #00d9ff;
        color: #e2e8f0;
    }
    
    /* Divider */
    .glow-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0, 217, 255, 0.5), transparent);
        margin: 2rem 0;
        border: none;
    }
    
    /* Text inputs */
    .stTextInput > div > input,
    .stTextArea > div > textarea {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        color: #fff;
    }
    
    .stTextInput > div > input:focus,
    .stTextArea > div > textarea:focus {
        border-color: #00d9ff;
        box-shadow: 0 0 15px rgba(0, 217, 255, 0.2);
    }
    
    /* File uploader */
    .stFileUploader > div > div {
        background: rgba(255, 255, 255, 0.95);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 8px;
    }
    
    .stFileUploader label,
    .stFileUploader .stMarkdown,
    .stFileUploader p,
    .stFileUploader input[type="file"] {
        color: #1a1a2e !important;
    }
    
    /* Streamlit text elements */
    .stMarkdown, .stText, .stDataFrame, .stTable, .stDataFrame * {
        color: #e2e8f0;
    }
    
    /* Ensure all text in cards is light */
    .card *, .card-title *, .metric-card * {
        color: #e2e8f0 !important;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }
    
    /* Paragraphs and spans */
    p, span, div:not(.stFileUploader *) {
        color: #e2e8f0;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        display: none;
        visibility: hidden;
        width: 0;
        min-width: 0;
    }

    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }

    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #67e8f9 !important;
    }

    [data-testid="stSidebar"] .stMetric {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 0.6rem;
    }

    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
    }

    /* Streamlit text elements - light text on dark background */
    .stMarkdown, .stText, .stDataFrame, .stTable, .stDataFrame *,
    .stMarkdown *, .stText *, .stExpander *, .stAlert * {
        color: #e2e8f0 !important;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    
    /* Ensure markdown containers show full text */
    [data-testid="stMarkdownContainer"] {
        max-width: 100%;
        word-wrap: break-word;
        overflow-wrap: break-word;
        overflow: visible;
    }
    
    [data-testid="stMarkdownContainer"] p {
        max-width: 100%;
        display: block;
        white-space: normal;
        overflow: visible;
        text-overflow: clip;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }

    /* Exception: file uploader text should be dark on light background */
    .stFileUploader label,
    .stFileUploader .stMarkdown,
    .stFileUploader p,
    .stFileUploader input[type="file"]::-webkit-file-upload-button {
        color: #1a1a2e !important;
    }
    
    /* But file name after upload should be white */
    .stFileUploaderFileName,
    .stFileUploaderFileName * {
        color: #e2e8f0 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)


def init_session_state():
    """Initialize session state variables."""
    defaults = {
        "step": 0,
        "analysis_result": None,
        "questions": [],
        "answers": {},
        "diagnosis": None,
        "safety_info": None,
        "instructions": None,
        "shopping_list": None,
        "uploaded_image": None,
        "workflow_started": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def check_api_key():
    """Check if API key is configured."""
    if not ACTIVE_API_KEY:
        st.error("API ключ не настроен! Добавьте ключ в .env файл")
        provider_info = "OpenAI" if LLM_PROVIDER == "openai" else "Claude"
        st.info(f"Получите API ключ на платформе {provider_info}")
        st.stop()


def reset_workflow():
    """Reset the entire workflow."""
    st.session_state.step = 0
    st.session_state.workflow_started = False
    st.session_state.analysis_result = None
    st.session_state.questions = []
    st.session_state.answers = {}
    st.session_state.diagnosis = None
    st.session_state.safety_info = None
    st.session_state.instructions = None
    st.session_state.shopping_list = None
    st.session_state.uploaded_image = None
    st.session_state["_shopping_buffer"] = None
    st.session_state["_shopping_thread_started"] = False


def render_progress_bar():
    """Render progress bar."""
    step_labels = [
        "Загрузка",
        "Анализ",
        "Вопросы",
        "Безопасность",
        "Инструкция",
        "Покупки",
    ]
    n = len(step_labels)
    max_step_index = n - 1
    safe_step = min(max(st.session_state.step, 0), max_step_index)

    line_start_pct = 100 / (2 * n)
    line_width_pct = 100 - 2 * line_start_pct
    fill_ratio = safe_step / max_step_index if max_step_index > 0 else 0
    fill_width_pct = fill_ratio * line_width_pct

    steps_html = []
    for i, label in enumerate(step_labels):
        if i < safe_step:
            state_class = "completed"
            icon = "✓"
        elif i == safe_step:
            state_class = "active"
            icon = str(i + 1)
        else:
            state_class = ""
            icon = str(i + 1)

        steps_html.append(f"""
            <div class="step {state_class}">
                <div class="step-circle">{icon}</div>
                <div class="step-label">{label}</div>
            </div>""")

    progress_html = f"""
    <!DOCTYPE html><html><head><meta charset="utf-8">
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
      * {{ box-sizing: border-box; margin: 0; padding: 0; }}
      body {{ background: transparent; font-family: 'Inter', sans-serif; padding: 8px 0 4px; }}
      .progress-container {{ position: relative; padding: 4px 0 8px; }}
      .progress-track {{
        position: absolute; top: 26px;
        left: {line_start_pct:.4f}%; width: {line_width_pct:.4f}%;
        height: 3px; background: rgba(255,255,255,0.12);
        border-radius: 999px; z-index: 1;
      }}
      .progress-fill {{
        position: absolute; top: 26px;
        left: {line_start_pct:.4f}%; width: {fill_width_pct:.4f}%;
        height: 3px; background: linear-gradient(90deg, #00d9ff, #00ff88);
        border-radius: 999px; z-index: 2;
      }}
      .progress-steps {{
        display: grid; grid-template-columns: repeat({n}, 1fr);
        position: relative; z-index: 3;
      }}
      .step {{ display: flex; flex-direction: column; align-items: center; gap: 6px; }}
      .step-circle {{
        width: 52px; height: 52px; border-radius: 50%;
        background: rgba(255,255,255,0.08); border: 2px solid rgba(255,255,255,0.2);
        display: flex; align-items: center; justify-content: center;
        font-weight: 600; color: #8896a5; font-size: 1rem; transition: all 0.25s ease;
      }}
      .step.active .step-circle {{
        background: linear-gradient(135deg, #00d9ff, #00ff88);
        border-color: transparent; color: #1a1a2e;
        transform: scale(1.1); box-shadow: 0 0 28px rgba(0,217,255,0.5);
      }}
      .step.completed .step-circle {{
        background: #00ff88; border-color: #00ff88; color: #1a1a2e;
        box-shadow: 0 0 20px rgba(0,255,136,0.4);
      }}
      .step-label {{
        color: #8896a5; font-size: 0.78rem; font-weight: 500;
        text-align: center; max-width: 90px; line-height: 1.2;
      }}
      .step.active .step-label {{ color: #00d9ff; text-shadow: 0 0 8px rgba(0,217,255,0.4); }}
      .step.completed .step-label {{ color: #00ff88; text-shadow: 0 0 8px rgba(0,255,136,0.35); }}
    </style></head>
    <body>
      <div class="progress-container">
        <div class="progress-track"></div>
        <div class="progress-fill"></div>
        <div class="progress-steps">{"".join(steps_html)}</div>
      </div>
    </body></html>
    """
    components.html(progress_html, height=110)


def main():
    """Main application function."""
    init_session_state()

    # Header
    st.markdown('<div class="main-header">SmartHandyman</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">AI-помощник по ремонту бытовой техники и дома</div>',
        unsafe_allow_html=True,
    )

    check_api_key()

    # Кнопка управления
    col_left, col_restart, col_right = st.columns(
        [1, 3, 1], vertical_alignment="center"
    )
    with col_restart:
        if st.button("Начать сначала", key="restart_btn", use_container_width=True):
            reset_workflow()
            st.rerun()

    # Progress bar (always visible)
    render_progress_bar()
    st.markdown('<hr class="glow-divider">', unsafe_allow_html=True)

    # Step routing
    if st.session_state.step == 0:
        show_upload_step()
    elif st.session_state.step == 1:
        show_analysis_step()
    elif st.session_state.step == 2:
        show_questions_step()
    elif st.session_state.step == 3:
        show_safety_step()
    elif st.session_state.step == 4:
        show_instructions_step()
    elif st.session_state.step == 5:
        show_shopping_step()


def show_upload_step():
    """Step 0: Upload image."""
    st.session_state.workflow_started = True

    st.markdown('<div class="card-title">Загрузите фото</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Выберите изображение",
            type=["jpg", "jpeg", "png"],
            help="Загрузите четкое фото проблемы",
        )

        if uploaded_file:
            st.session_state.uploaded_image = uploaded_file.getvalue()
            st.image(uploaded_file, caption="Ваше фото", use_container_width=True)

    with col2:
        st.markdown("#### Советы")
        st.markdown("""
            - Сфотографируйте проблему крупно
            - Убедитесь, что фото четкое
            - Включите коды ошибок в кадр
            - Используйте хорошее освещение
        """)

    if st.session_state.uploaded_image:
        if st.button(
            "Анализировать изображение", type="primary", use_container_width=True
        ):
            st.session_state.step = 1
            st.rerun()


def show_analysis_step():
    """Step 1: Analyze image."""
    st.markdown(
        '<div class="card-title">Результаты анализа</div>', unsafe_allow_html=True
    )

    if not st.session_state.analysis_result:
        with st.spinner("Анализирую изображение..."):
            analyzer = VisionAnalyzer()
            st.session_state.analysis_result = analyzer.analyze_image(
                st.session_state.uploaded_image
            )

    result = st.session_state.analysis_result

    if "error" in result:
        st.error(f"Ошибка анализа: {result.get('error')}")

        if st.button("Попробовать снова", type="primary"):
            st.session_state.uploaded_image = None
            st.session_state.step = 0
            st.rerun()
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Объект", result.get("object", "N/A"))

    with col2:
        st.metric("Уверенность", f"{result.get('confidence', 0)}%")

    with col3:
        danger_level = result.get("danger_level", "medium")
        danger_text = (
            "Высокий"
            if danger_level == "high"
            else "Средний"
            if danger_level == "medium"
            else "Низкий"
        )

        st.metric("Опасность", danger_text)

    st.markdown('<hr class="glow-divider">', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### Детали")
        st.write(f"**Бренд/Модель:** {result.get('brand', 'Не определено')}")
        st.write(f"**Проблема:** {result.get('problem', 'Не определено')}")
        st.write(f"**Категория:** {result.get('category', 'Не определено')}")

    with col_b:
        st.markdown("#### Видимые детали")
        visible_details = result.get("visible_details", [])
        if visible_details:
            for detail in visible_details:
                st.markdown(f"- {detail}")
        else:
            st.info("Детали не обнаружены")

    if st.button("Продолжить к диагностике", type="primary", use_container_width=True):
        st.session_state.step = 2
        st.rerun()


def show_questions_step():
    """Step 2: Diagnostic questions."""
    st.markdown(
        '<div class="card-title">Уточняющие вопросы</div>', unsafe_allow_html=True
    )
    st.write("Ответьте на вопросы для точной диагностики")

    agent = DiagnosticAgent()

    if not st.session_state.questions:
        with st.spinner("Генерирую вопросы..."):
            questions = agent.generate_questions(
                st.session_state.analysis_result,
                st.session_state.answers if st.session_state.answers else None,
            )
            st.session_state.questions = questions

    if st.session_state.questions:
        with st.form("diagnostic_questions"):
            answers = {}
            for i, question in enumerate(st.session_state.questions):
                st.markdown(f"**Вопрос {i + 1}:** {question}")
                answer = st.text_area(
                    f"Ответ на вопрос {i + 1}",
                    key=f"q_{i}",
                    height=80,
                    placeholder="Введите ваш ответ...",
                )
                if answer:
                    answers[question] = answer
                st.markdown('<hr class="glow-divider">', unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button(
                    "Отправить ответы", type="primary", use_container_width=True
                )
            with col2:
                skip = st.form_submit_button("Пропустить", use_container_width=True)

            if submit and answers:
                st.session_state.answers.update(answers)
                with st.spinner("Анализирую ответы..."):
                    diagnosis = agent.analyze_answers(
                        st.session_state.analysis_result, st.session_state.answers
                    )
                    st.session_state.diagnosis = diagnosis
                st.session_state.step = 3
                st.rerun()
            elif skip:
                with st.spinner("Формирую диагноз..."):
                    diagnosis = agent.analyze_answers(
                        st.session_state.analysis_result, {}
                    )
                    st.session_state.diagnosis = diagnosis
                st.session_state.step = 3
                st.rerun()


def show_safety_step():
    """Step 3: Safety check."""
    st.markdown(
        '<div class="card-title">Проверка безопасности</div>', unsafe_allow_html=True
    )

    if not st.session_state.safety_info:
        with st.spinner("Проверяю безопасность..."):
            checker = SafetyChecker()
            st.session_state.safety_info = checker.check_safety(
                st.session_state.analysis_result, st.session_state.answers
            )

    safety_info = st.session_state.safety_info
    safety_message = SafetyChecker.format_safety_message(safety_info)

    if safety_info.get("is_dangerous"):
        st.markdown(
            f'<div class="danger-box">{safety_message}</div>', unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="success-box">{safety_message}</div>', unsafe_allow_html=True
        )

    if st.session_state.diagnosis:
        st.markdown("#### Диагноз")
        st.write(f"**{st.session_state.diagnosis.get('refined_diagnosis')}**")

        causes = st.session_state.diagnosis.get("probable_causes", [])
        if causes:
            st.markdown("**Вероятные причины:**")
            for cause in causes:
                st.markdown(f"- {cause}")

        confidence = st.session_state.diagnosis.get("confidence", 0)
        st.metric("Уверенность", f"{confidence}%")

    if safety_info.get("requires_professional"):
        st.error("**Рекомендуется обратиться к профессионалу**")
        st.write(
            f"Причина: {safety_info.get('professional_reason', 'Высокая сложность')}"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Продолжить", type="primary"):
                st.session_state.step = 4
                st.rerun()
        with col2:
            if st.button("Отмена"):
                reset_workflow()
                st.rerun()
    else:
        if st.button("Получить инструкцию", type="primary", use_container_width=True):
            st.session_state.step = 4
            st.rerun()


def show_instructions_step():
    """Step 4: Repair instructions."""
    st.markdown(
        '<div class="card-title">Инструкция по ремонту</div>', unsafe_allow_html=True
    )

    if not st.session_state.instructions:
        with st.spinner("Генерирую инструкцию..."):
            generator = InstructionGenerator()
            instructions = generator.generate_instructions(
                st.session_state.diagnosis,
                st.session_state.analysis_result,
                st.session_state.safety_info,
            )
            st.session_state.instructions = instructions

    instructions = st.session_state.instructions
    formatted = InstructionGenerator.format_instructions(instructions)
    st.markdown(formatted)

    if st.button("Перейти к списку покупок", type="primary", use_container_width=True):
        st.session_state.step = 5
        st.rerun()


def _render_item_card(item: dict) -> None:
    """Render a single shopping item as a styled inline card."""
    icon = "🔧" if item.get("category") == "инструмент" else "📦"
    accent = "#00d9ff" if item.get("category") == "инструмент" else "#00ff88"
    opt_badge = (
        " <span style='font-size:0.72rem;color:#94a3b8;font-weight:400;'>(опционально)</span>"
        if item.get("optional")
        else ""
    )
    price = item.get("estimated_price", 0)
    source = item.get("where_to_buy", "Строительный магазин")
    qty = item.get("quantity", "1 шт")
    name = item.get("name", "—")

    st.markdown(
        f"""
        <div style="
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.08);
            border-left: 3px solid {accent};
            border-radius: 12px;
            padding: 0.85rem 1.1rem;
            margin: 0.4rem 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            backdrop-filter: blur(8px);
        ">
            <div style="flex:1; min-width:0;">
                <div style="font-weight:600; color:#e2e8f0; font-size:0.92rem; word-break:break-word;">
                    {icon} {name}{opt_badge}
                </div>
                <div style="color:#94a3b8; font-size:0.78rem; margin-top:0.2rem;">
                    📍 {source}&nbsp;&nbsp;·&nbsp;&nbsp;📦 {qty}
                </div>
            </div>
            <div style="
                text-align:right; white-space:nowrap;
                font-size:1.05rem; font-weight:700; color:{accent};
                flex-shrink:0;
            ">
                ~{price:,} ₽
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_shopping_cards(items: list, cost: dict | None, done: bool) -> None:
    """Render all item cards split by category, plus optional cost summary."""
    tools = [i for i in items if i.get("category") == "инструмент"]
    mats = [i for i in items if i.get("category") != "инструмент"]

    if tools:
        st.markdown("#### 🔧 Инструменты")
        for item in tools:
            _render_item_card(item)

    if mats:
        st.markdown("#### 📦 Материалы")
        for item in mats:
            _render_item_card(item)

    if done and cost:
        st.markdown(
            '<hr style="border:none;border-top:1px solid rgba(255,255,255,0.1);margin:1.5rem 0;">',
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("Материалы", f"{cost['materials_cost']:,} ₽")
        c2.metric("Инструменты", f"{cost['tools_cost']:,} ₽")
        c3.metric("ИТОГО", f"{cost['total_cost']:,} ₽")


def show_shopping_step():
    """Step 5: Shopping list with live streaming cards."""
    import threading

    st.markdown('<div class="card-title">Список покупок</div>', unsafe_allow_html=True)

    # ── Уже полностью готово — рендерим из кэша ─────────────────────
    if st.session_state.shopping_list:
        items = st.session_state.shopping_list["list"].get("items", [])
        cost = st.session_state.shopping_list["cost"]
        _render_shopping_cards(items, cost, done=True)
        st.success("Диагностика завершена! Удачного ремонта!")
        if st.button("Новая диагностика", type="primary", use_container_width=True):
            reset_workflow()
            st.rerun()
        return

    # ── Инициализируем разделяемый буфер (plain Python list) ────────
    # Ключ "_shopping_buffer" хранит СПИСОК — к нему обращается и main-тред
    # (для чтения/рендера) и фоновый тред (для append).
    # Фоновый тред НЕ читает st.session_state — только вызывает append на
    # переданном объекте списка, что thread-safe в CPython (GIL).
    if st.session_state.get("_shopping_buffer") is None:
        st.session_state["_shopping_buffer"] = []

    buffer: list = st.session_state["_shopping_buffer"]

    # ── Запускаем фоновый тред один раз ─────────────────────────────
    if not st.session_state.get("_shopping_thread_started"):
        st.session_state["_shopping_thread_started"] = True

        instructions = st.session_state.instructions

        # Замыкание на buffer (plain list) — НЕ на st.session_state
        def on_item_ready(item: dict, _buf=buffer):
            _buf.append(item)  # thread-safe append (GIL)

        def on_done(full_list: dict, _buf=buffer):
            agent_inner = ShoppingAgent()
            cost = agent_inner.estimate_total_cost(full_list)
            # Специальный sentinel-объект в конце буфера
            _buf.append(
                {"__done__": True, "cost": cost, "items": full_list.get("items", [])}
            )

        def _run():
            agent_inner = ShoppingAgent()
            result = agent_inner.generate_shopping_list(instructions, on_item_ready)
            on_done(result)

        threading.Thread(target=_run, daemon=True).start()

    # ── Autorefresh каждые 10 секунд пока тред работает ────────────
    from streamlit_autorefresh import st_autorefresh

    st_autorefresh(interval=10000, limit=200, key="shopping_refresh")

    # ── Читаем буфер (snapshot) и рендерим ──────────────────────────
    snapshot = list(buffer)  # shallow copy — безопасно читать из main-треда

    # Проверяем sentinel
    done_entry = next(
        (x for x in snapshot if isinstance(x, dict) and x.get("__done__")), None
    )
    is_done = done_entry is not None
    items = [x for x in snapshot if not x.get("__done__")]

    if is_done:
        cost = done_entry["cost"]
        st.session_state.shopping_list = {
            "list": {
                "items": done_entry["items"],
                "total_items": len(done_entry["items"]),
            },
            "cost": cost,
        }
        _render_shopping_cards(done_entry["items"], cost, done=True)
        st.success("Диагностика завершена! Удачного ремонта!")
        if st.button("Новая диагностика", type="primary", use_container_width=True):
            reset_workflow()
            st.rerun()
    elif items:
        _render_shopping_cards(items, None, done=False)
        st.caption(f"⏳ Найдено {len(items)} товаров, ищу дальше…")
    else:
        st.info("🔍 Ищу товары и цены…")


if __name__ == "__main__":
    main()
