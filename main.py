"""Main Streamlit application for home repair assistant."""

import streamlit as st
from vision_analyzer import VisionAnalyzer
from diagnostic_agent import DiagnosticAgent
from safety_checker import SafetyChecker
from instruction_generator import InstructionGenerator
from shopping_agent import ShoppingAgent
from config import LLM_PROVIDER, ACTIVE_API_KEY

# Page configuration
st.set_page_config(
    page_title="Помощник по ремонту",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
    }
    .danger-box {
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
        padding: 1rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
    }
    .step-indicator {
        font-size: 1.2rem;
        font-weight: bold;
        color: #6c757d;
        margin: 1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Initialize session state
def init_session_state():
    """Initialize session state variables."""
    if "step" not in st.session_state:
        st.session_state.step = 0
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "questions" not in st.session_state:
        st.session_state.questions = []
    if "answers" not in st.session_state:
        st.session_state.answers = {}
    if "diagnosis" not in st.session_state:
        st.session_state.diagnosis = None
    if "safety_info" not in st.session_state:
        st.session_state.safety_info = None
    if "instructions" not in st.session_state:
        st.session_state.instructions = None
    if "shopping_list" not in st.session_state:
        st.session_state.shopping_list = None
    if "uploaded_image" not in st.session_state:
        st.session_state.uploaded_image = None


def check_api_key():
    """Check if API key is configured."""
    if not ACTIVE_API_KEY:
        if LLM_PROVIDER == "openai":
            st.error("⚠️ API ключ OpenAI не настроен! Создайте файл .env и добавьте OPENAI_API_KEY")
            st.info("Получите API ключ на https://platform.openai.com/api-keys")
        else:
            st.error("⚠️ API ключ Claude не настроен! Создайте файл .env и добавьте CLAUDE_API_KEY и CLAUDE_BASE_URL")
            st.info("Получите API ключ у вашего провайдера Claude API")
        st.stop()

    # Display current provider
    if LLM_PROVIDER == "openai":
        provider_name = "OpenAI GPT"
    else:
        provider_name = "Claude (Anthropic)"
    st.sidebar.info(f"🤖 Используется: {provider_name}")


def reset_workflow():
    """Reset the entire workflow."""
    st.session_state.step = 0
    st.session_state.analysis_result = None
    st.session_state.questions = []
    st.session_state.answers = {}
    st.session_state.diagnosis = None
    st.session_state.safety_info = None
    st.session_state.instructions = None
    st.session_state.shopping_list = None
    st.session_state.uploaded_image = None


def main():
    """Main application function."""
    init_session_state()
    check_api_key()

    st.markdown(
        '<div class="main-header">🔧 Помощник по домашнему ремонту</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "Загрузите фото поломки, и я помогу вам определить проблему и составить план ремонта."
    )

    with st.sidebar:
        st.header("📊 Прогресс диагностики")
        steps = [
            "Загрузка фото",
            "Анализ изображения",
            "Уточняющие вопросы",
            "Проверка безопасности",
            "Инструкция по ремонту",
            "Список покупок",
        ]

        for i, step_name in enumerate(steps):
            if i < st.session_state.step:
                st.success(f"✅ {step_name}")
            elif i == st.session_state.step:
                st.info(f"▶️ {step_name}")
            else:
                st.text(f"⏸️ {step_name}")

        st.divider()
        if st.button("🔄 Начать заново", use_container_width=True):
            reset_workflow()
            st.rerun()

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
    st.header("📸 Шаг 1: Загрузите фото поломки")

    uploaded_file = st.file_uploader(
        "Выберите изображение",
        type=["jpg", "jpeg", "png"],
        help="Загрузите четкое фото проблемы",
    )

    if uploaded_file:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.image(
                uploaded_file,
                caption="Загруженное изображение",
                use_container_width=True,
            )

        with col2:
            st.info(
                """
                **Советы для лучшего результата:**
                - Сфотографируйте проблему крупным планом
                - Убедитесь, что изображение четкое
                - Включите в кадр коды ошибок или маркировки
                - Хорошее освещение улучшит анализ
                """
            )

        st.session_state.uploaded_image = uploaded_file.getvalue()

        if st.button(
            "🔍 Анализировать изображение", type="primary", use_container_width=True
        ):
            st.session_state.step = 1
            st.rerun()


def show_analysis_step():
    """Step 1: Analyze image with Vision LLM."""
    st.header("🔍 Шаг 2: Анализ изображения")

    with st.spinner("Анализирую изображение с помощью Vision AI..."):
        analyzer = VisionAnalyzer()
        result = analyzer.analyze_image(st.session_state.uploaded_image)
        st.session_state.analysis_result = result

    if "error" in result:
        st.error(f"⚠️ Ошибка анализа: {result.get('error')}")
        st.info("Попробуйте загрузить фото еще раз или проверьте подключение.")
        if st.button("🔄 Попробовать снова", type="primary"):
            st.session_state.uploaded_image = None
            st.session_state.step = 0
            st.rerun()
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎯 Результаты анализа")
        st.write(f"**Объект:** {result.get('object', 'Не определено')}")
        st.write(f"**Бренд/Модель:** {result.get('brand', 'Не определено')}")
        st.write(f"**Проблема:** {result.get('problem', 'Не определено')}")
        st.write(f"**Категория:** {result.get('category', 'Не определено')}")

        danger_level = result.get("danger_level", "medium")
        if danger_level == "high":
            st.error("⚠️ Уровень опасности: ВЫСОКИЙ")
        elif danger_level == "medium":
            st.warning("⚠️ Уровень опасности: Средний")
        else:
            st.success("✅ Уровень опасности: Низкий")

    with col2:
        st.subheader("📋 Детали")
        confidence = result.get("confidence", 0)
        st.metric("Уверенность анализа", f"{confidence}%")

        visible_details = result.get("visible_details", [])
        if visible_details:
            st.write("**Видимые детали:**")
            for detail in visible_details:
                st.write(f"- {detail}")

    if st.button(
        "➡️ Продолжить к диагностике", type="primary", use_container_width=True
    ):
        st.session_state.step = 2
        st.rerun()


def show_questions_step():
    """Step 2: Interactive diagnostic questions."""
    st.header("❓ Шаг 3: Уточняющие вопросы")
    st.write("Ответьте на несколько вопросов для более точной диагностики.")

    agent = DiagnosticAgent()

    # Generate questions if not done
    if not st.session_state.questions:
        with st.spinner("Генерирую вопросы..."):
            questions = agent.generate_questions(
                st.session_state.analysis_result,
                st.session_state.answers if st.session_state.answers else None,
            )
            st.session_state.questions = questions

    # Display questions
    if st.session_state.questions:
        with st.form("diagnostic_questions"):
            answers = {}
            for i, question in enumerate(st.session_state.questions):
                answer = st.text_area(
                    f"**Вопрос {i + 1}:** {question}",
                    key=f"q_{i}",
                    height=80,
                    placeholder="Введите ваш ответ...",
                )
                if answer:
                    answers[question] = answer

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button(
                    "✅ Отправить ответы", type="primary", use_container_width=True
                )
            with col2:
                skip = st.form_submit_button(
                    "⏭️ Пропустить вопросы", use_container_width=True
                )

            if submit and answers:
                st.session_state.answers.update(answers)

                # Analyze answers
                with st.spinner("Анализирую ответы..."):
                    diagnosis = agent.analyze_answers(
                        st.session_state.analysis_result, st.session_state.answers
                    )
                    st.session_state.diagnosis = diagnosis

                st.session_state.step = 3
                st.rerun()

            elif skip:
                # Analyze only by photo
                with st.spinner("Формирую базовый диагноз..."):
                    diagnosis = agent.analyze_answers(
                        st.session_state.analysis_result, {}
                    )
                    st.session_state.diagnosis = diagnosis

                st.session_state.step = 3
                st.rerun()


def show_safety_step():
    """Step 3: Safety check and warnings."""
    st.header("🚨 Шаг 4: Проверка безопасности")

    with st.spinner("Проверяю безопасность ремонта..."):
        checker = SafetyChecker()
        safety_info = checker.check_safety(
            st.session_state.analysis_result, st.session_state.answers
        )
        st.session_state.safety_info = safety_info

    safety_message = checker.format_safety_message(safety_info)

    if safety_info.get("is_dangerous"):
        st.markdown(
            f'<div class="danger-box">{safety_message}</div>', unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="success-box">{safety_message}</div>', unsafe_allow_html=True
        )

    # Show refined diagnosis
    if st.session_state.diagnosis:
        st.subheader("🔬 Уточненный диагноз")
        st.write(f"**Диагноз:** {st.session_state.diagnosis.get('refined_diagnosis')}")

        causes = st.session_state.diagnosis.get("probable_causes", [])
        if causes:
            st.write("**Вероятные причины:**")
            for cause in causes:
                st.write(f"- {cause}")

        confidence = st.session_state.diagnosis.get("confidence", 0)
        st.metric("Уверенность в диагнозе", f"{confidence}%")

    # Warning if professional needed
    if safety_info.get("requires_professional"):
        st.error(
            "⚠️ **ВНИМАНИЕ:** Рекомендуется обратиться к профессионалу для выполнения этого ремонта."
        )
        st.write(
            f"Причина: {safety_info.get('professional_reason', 'Высокая сложность')}"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Я понимаю риски, продолжить", type="primary"):
                st.session_state.step = 4
                st.rerun()
        with col2:
            if st.button("🔄 Начать заново"):
                reset_workflow()
                st.rerun()
    else:
        if st.button("➡️ Получить инструкцию", type="primary", use_container_width=True):
            st.session_state.step = 4
            st.rerun()


def show_instructions_step():
    """Step 4: Generate and display repair instructions."""
    st.header("📖 Шаг 5: Инструкция по ремонту")

    if not st.session_state.instructions:
        with st.spinner("Генерирую инструкцию по ремонту..."):
            generator = InstructionGenerator()
            instructions = generator.generate_instructions(
                st.session_state.diagnosis,
                st.session_state.analysis_result,
                st.session_state.safety_info,
            )
            st.session_state.instructions = instructions

    # Display instructions
    instructions = st.session_state.instructions
    formatted = InstructionGenerator().format_instructions(instructions)
    st.markdown(formatted)

    if st.button(
        "🛒 Перейти к списку покупок", type="primary", use_container_width=True
    ):
        st.session_state.step = 5
        st.rerun()


def show_shopping_step():
    """Step 5: Shopping list and cost estimate."""
    st.header("🛒 Шаг 6: Список покупок и смета")

    if not st.session_state.shopping_list:
        with st.spinner("Составляю список покупок и оцениваю стоимость..."):
            agent = ShoppingAgent()
            shopping_list = agent.generate_shopping_list(st.session_state.instructions)
            cost_estimate = agent.estimate_total_cost(shopping_list)

            st.session_state.shopping_list = {
                "list": shopping_list,
                "cost": cost_estimate,
            }

    # Display shopping list
    shopping_data = st.session_state.shopping_list
    formatted = ShoppingAgent().format_shopping_list(
        shopping_data["list"], shopping_data["cost"]
    )
    st.markdown(formatted)

    st.success("✅ Диагностика завершена! Удачного ремонта!")

    st.divider()
    if st.button("🔄 Начать новую диагностику", type="primary", use_container_width=True):
        reset_workflow()
        st.rerun()


if __name__ == "__main__":
    main()
