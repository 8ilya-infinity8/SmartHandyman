import os

import streamlit as st

# Публичный URL backend-а для браузера (по умолчанию localhost:8000).
PUBLIC_BACKEND_URL = os.getenv("PUBLIC_BACKEND_URL", "http://localhost:8000")


def _build_attachment_badge(filename: str | None) -> str:
    if not filename:
        label = "file"
        ext = ""
    else:
        if "." in filename:
            base, ext = filename.rsplit(".", 1)
            ext = "." + ext
        else:
            base, ext = filename, ""
        short = base[:5] + "..." if len(base) > 5 else base
        label = f"{short}{ext}"

    return f"""
    <div style="
        display:flex;
        align-items:center;
        gap:8px;
        padding:8px 10px;
        border-radius:10px;
        background:rgba(15,23,42,0.9);
        border:1px solid rgba(148,163,184,0.7);
        font-size:0.82rem;
        color:#e5e7eb;
        max-width:260px;
    ">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
             xmlns="http://www.w3.org/2000/svg">
            <path d="M7 13L12 8L17 13" stroke="#f97316" stroke-width="1.6"
                  stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 8V20" stroke="#f97316" stroke-width="1.6"
                  stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
            {label}
        </span>
    </div>
    """


def render_message(msg: dict):
    """Display a single message dict using Streamlit's built-in chat wrapper.

    Поддерживаем специальный формат content:
    [ATTACHMENT]filename.ext|произвольный текст сообщения
    """
    role = msg.get("role") or "assistant"
    raw_content = msg.get("content")
    # приводим к строке и нормализуем, чтобы любые числовые значения (0, 1 и т.п.)
    # не появлялись случайно
    content = "" if raw_content is None else str(raw_content)
    attachment = msg.get("attachment_url")

    # Достаём имя файла, если оно зашито в content маркером
    attachment_filename = None
    attachment_marker = "[ATTACHMENT]"
    if content.startswith(attachment_marker):
        rest = content[len(attachment_marker) :].strip()
        if "|" in rest:
            name_part, text_part = rest.split("|", 1)
            attachment_filename = name_part.strip() or None
            content = text_part
        else:
            attachment_filename = rest or None
            content = ""

    streamlit_role = "user" if role == "user" else "assistant"

    # Если нет ни текста, ни вложения (или сообщение содержит только "0"),
    # просто ничего не рендерим — это убирает паразитную строку "0".
    if (not content or content.strip() == "0") and not attachment:
        return

    with st.chat_message(streamlit_role):
        # если есть вложение и "контент" равен "0" или пустой строке,
        # считаем, что это служебное значение и не показываем его.
        if content and not (attachment and content.strip() == "0"):
            st.markdown(content)

        if attachment:
            # badge с названием файла
            badge_html = _build_attachment_badge(attachment_filename)
            st.markdown(badge_html, unsafe_allow_html=True)

            # attachment_url приходит как относительный путь (/api/v1/storage/object/{id}),
            # поэтому для браузера собираем полный URL до backend, доступный с хоста.
            if attachment.startswith("http://") or attachment.startswith("https://"):
                img_url = attachment
            else:
                img_url = f"{PUBLIC_BACKEND_URL}{attachment}"

            st.image(img_url, width=360)
