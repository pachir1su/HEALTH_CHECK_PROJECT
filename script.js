const chatBox = document.getElementById("chat-box");
const input = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const typing = document.getElementById("typing");

// 엔터키로도 전송
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    sendBtn.click();
  }
});

sendBtn.onclick = async () => {
  const text = input.value.trim();
  if (!text) return;

  appendMessage(text, "user");
  input.value = "";
  sendBtn.disabled = true;
  typing.hidden = false;

  try {
    console.log("▶ 요청 보냄:", text);
    const resp = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symptom: text }),
    });
    const data = await resp.json();
    console.log("◀ 응답 받음:", data);

    // 심박수도 업데이트
    document.getElementById("pulse").innerText = data.pulse;

    typing.hidden = true;
    appendMessage(data.reply, "ai");
    sendBtn.disabled = false;
    speak(data.reply);
  } catch (e) {
    console.error("⛔ 서버 요청 중 오류:", e);
    typing.hidden = true;
    appendMessage("서버 통신 오류가 발생했습니다.", "ai");
    sendBtn.disabled = false;
  }
};

function appendMessage(msg, who) {
  const div = document.createElement("div");
  div.className = `message ${who}`;
  div.innerText = msg;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function speak(text) {
  const u = new SpeechSynthesisUtterance(text);
  u.rate = 1;
  speechSynthesis.speak(u);
}
