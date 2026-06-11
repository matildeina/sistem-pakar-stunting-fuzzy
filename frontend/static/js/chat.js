document.addEventListener("DOMContentLoaded", () => {
    let conversationHistory = [];
    let isLoading = false;

    const chatInput = document.getElementById("chat-input");
    const btnSend = document.getElementById("btn-send");
    const btnNewChat = document.getElementById("btn-new-chat");

    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    chatInput.addEventListener("input", () => {
        chatInput.style.height = "auto";
        chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + "px";
    });

    btnSend.addEventListener("click", sendMessage);
    btnNewChat.addEventListener("click", newChat);

    // Bind event delegation untuk suggestion buttons & chips (Mencegah Inline XSS Event)
    document.getElementById("sidebar-suggestions").addEventListener("click", (e) => {
        if (e.target.classList.contains("suggest-btn")) useSuggestion(e.target.textContent);
    });

    document.getElementById("messages-box").addEventListener("click", (e) => {
        if (e.target.classList.contains("chip")) useSuggestion(e.target.textContent);
    });

    function useSuggestion(text) {
        chatInput.value = text.trim();
        sendMessage();
    }

    function hideWelcome() {
        const w = document.getElementById("welcome-state");
        if (w) w.remove();
    }

    function formatText(text) {
        let html = text
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
            .replace(/^[-•]\s(.+)$/gm, "<li>$1</li>")
            .replace(/\n/g, "<br>");
        return html.startsWith("<") ? html : `<p>${html}</p>`;
    }

    function appendMessage(role, text) {
        hideWelcome();
        const container = document.getElementById("messages-box");
        const msg = document.createElement("div");
        msg.className = `msg ${role}`;
        
        msg.innerHTML = `
            <div class="msg-avatar">${role === "ai" ? "🌿" : "👤"}</div>
            <div style="display:flex; flex-direction:column; gap:2px; ${role === 'user' ? 'align-items:flex-end' : ''}">
                <div class="msg-bubble">${formatText(text)}</div>
                <div class="msg-time">${new Date().toLocaleTimeString("id-ID", {hour: "2-digit", minute:"2-digit"})}</div>
            </div>`;
        container.appendChild(msg);
        container.scrollTop = container.scrollHeight;
    }

    async function sendMessage() {
        if (isLoading) return;
        const text = chatInput.value.trim();
        if (!text) return;

        chatInput.value = "";
        chatInput.style.height = "auto";
        chatInput.disabled = true;
        btnSend.disabled = true;
        isLoading = true;

        appendMessage("user", text);
        conversationHistory.push({ role: "user", content: text });

        // Show typing indicator
        const container = document.getElementById("messages-box");
        const typing = document.createElement("div");
        typing.className = "msg ai";
        typing.id = "typing-indicator";
        typing.innerHTML = `<div class="msg-avatar">🌿</div><div class="msg-bubble typing-bubble"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>`;
        container.appendChild(typing);
        container.scrollTop = container.scrollHeight;

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({ pesan: text, history: conversationHistory }),
            });
            const data = await response.json();
            document.getElementById("typing-indicator").remove();

            if (response.ok) {
                appendMessage("ai", data.jawaban);
                conversationHistory.push({ role: "assistant", content: data.jawaban });
            } else {
                throw new Error(data.error);
            }
        } catch (err) {
            if(document.getElementById("typing-indicator")) document.getElementById("typing-indicator").remove();
            appendMessage("ai", "Terjadi kesalahan koneksi internal server.");
        } finally {
            chatInput.disabled = false;
            btnSend.disabled = false;
            isLoading = false;
            chatInput.focus();
        }
    }

    function newChat() {
        conversationHistory = [];
        window.location.reload();
    }
});