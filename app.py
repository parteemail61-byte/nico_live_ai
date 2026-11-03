
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nico LIVE AI</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#101018;color:white;font-family:Arial,sans-serif;text-align:center;padding:18px}
h1{color:#8b7cff}
.panel{max-width:500px;margin:auto;background:#1c1c29;padding:18px;border-radius:18px}
img{width:180px;height:180px;object-fit:cover;border-radius:50%;border:3px solid #8b7cff}
#messages{height:260px;overflow:auto;text-align:left;background:#11111a;padding:12px;border-radius:12px;margin:15px 0}
.msg{padding:9px;margin:7px 0;background:#29293b;border-radius:9px;overflow-wrap:anywhere}
input,select{width:100%;padding:13px;border:0;border-radius:9px;margin:6px 0;font-size:16px}
button{padding:13px;border:0;border-radius:9px;background:#7665ff;color:white;font-weight:bold;margin:5px;cursor:pointer}
label{display:block;margin:12px}
.status{color:#aaa;font-size:13px}
</style>
</head>
<body>
<div class="panel">
<h1>🎙️ NICO LIVE AI</h1>
<img src="/watermarked_img_9725052891330264212.jpg" alt="Nico">
<p>Seu parceiro de LIVE 🤙</p>

<div id="messages">
<div class="msg">Sistema: Nico está pronto para conversar!</div>
</div>

<input id="message" placeholder="Digite uma mensagem...">
<button onclick="sendMessage()">ENVIAR</button>

<label>
<input type="checkbox" id="autoSpeak" checked style="width:auto">
Falar respostas automaticamente
</label>

<select id="voiceSelect">
<option value="">Voz padrão do celular</option>
</select>

<button onclick="testVoice()">🔊 TESTAR VOZ</button>
<button onclick="stopVoice()">⏹ PARAR VOZ</button>

<p class="status" id="status">Aguardando...</p>
</div>

<script>
const messages = document.getElementById("messages");
const statusText = document.getElementById("status");
const voiceSelect = document.getElementById("voiceSelect");

let voices = [];

function loadVoices(){
  if(!("speechSynthesis" in window)){
    statusText.textContent = "Seu navegador não oferece voz automática.";
    return;
  }

  voices = speechSynthesis.getVoices();
  voiceSelect.innerHTML = '<option value="">Voz padrão do celular</option>';

  voices.forEach((voice,index)=>{
    const option = document.createElement("option");
    option.value = index;
    option.textContent = voice.name + " (" + voice.lang + ")";
    voiceSelect.appendChild(option);
  });
}

if("speechSynthesis" in window){
  loadVoices();
  speechSynthesis.onvoiceschanged = loadVoices;
}

function addMessage(text){
  const div = document.createElement("div");
  div.className = "msg";
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

function speak(text){
  if(!("speechSynthesis" in window)){
    statusText.textContent = "Voz não disponível neste navegador.";
    return;
  }

  speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "pt-BR";
  utterance.rate = 1;
  utterance.pitch = 0.9;
  utterance.volume = 1;

  const selected = voiceSelect.value;
  if(selected !== "" && voices[selected]){
    utterance.voice = voices[selected];
  } else {
    const portuguese = voices.find(v => v.lang.toLowerCase().startsWith("pt-br"))
      || voices.find(v => v.lang.toLowerCase().startsWith("pt"));
    if(portuguese) utterance.voice = portuguese;
  }

  utterance.onstart = () => statusText.textContent = "Nico está falando...";
  utterance.onend = () => statusText.textContent = "Nico está pronto!";
  utterance.onerror = () => statusText.textContent = "Não consegui reproduzir a voz.";

  speechSynthesis.speak(utterance);
}

function testVoice(){
  speak("E aí, família! Aqui é o Nico! Sejam todos muito bem-vindos à nossa live!");
}

function stopVoice(){
  if("speechSynthesis" in window) speechSynthesis.cancel();
  statusText.textContent = "Voz parada.";
}

async function sendMessage(){
  const input = document.getElementById("message");
  const message = input.value.trim();
  if(!message) return;

  addMessage("Você: " + message);
  input.value = "";
  statusText.textContent = "Nico está pensando...";

  try{
    const response = await fetch("/chat",{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({message})
    });

    const data = await response.json();

    if(!response.ok) throw new Error(data.error || "Erro na resposta");

    addMessage("Nico: " + data.reply);

    if(document.getElementById("autoSpeak").checked){
      speak(data.reply);
    } else {
      statusText.textContent = "Resposta recebida.";
    }

  }catch(error){
    addMessage("Sistema: " + error.message);
    statusText.textContent = "Erro ao conversar.";
  }
}

document.getElementById("message").addEventListener("keydown",e=>{
  if(e.key === "Enter") sendMessage();
});
</script>
</body>
</html>
