const statusEl = document.getElementById("status");
const logEl = document.getElementById("log");
const pingBtn = document.getElementById("pingBtn");

const usernameInput = document.getElementById("username");
const roomCodeInput = document.getElementById("roomCode");
const createBtn = document.getElementById("createBtn");
const joinBtn = document.getElementById("joinBtn");
const roomInfo = document.getElementById("roomInfo");

const log = (msg) => {
    const line = document.createElement("div");
    const ts = new Date().toLocaleDateString();
    line.textContent = `[${ts}] : ${msg}`;
    logEl.prepend(line);
};

const setStatus = (text) => {
    statusEl.textContent = text;
}

const socket = io({autoConnect : true});

socket.on("connect", () => {
    setStatus(`Connecté (id : ${socket.id})`);
    pingBtn.disabled = false;
    log("Client connecté");
});

socket.on("disconnect", () => {
    setStatus(`Déconnecté`);
    pingBtn.disabled = true;
    log("Client déconnecté");
})

socket.on("sever_message", (data) => {
    log(`Server : ${data.msg}`);
});

socket.on("pong_from_server", (data) => {
    const clientSend = data.client_time;
    const clientReceive = Date.now();
    
    const latence = clientReceive - clientSend;
    log(`PONG reçu, latence : ${latence}`);
});

socket.on("error_message", (data) => {
    log(`Erreur : ${data.msg}`);
});

socket.on("room_update", (data) => {
    renderRoom(data);
});

socket.on("room_joined", (data) => {
    renderRoom(data);
    log(`Rejoint la room ${data.code} (${data.players.length}/${data.max_players})`);
});

socket.on("room_deleted", (data) => {
    roomInfo.innerHTML = `<div>Room ${data.code} supprimée (vide).</div>`;
});

pingBtn.addEventListener("click", () => {
    log("Ping envoyé au server...");
    socket.emit("ping_from_client", {when : Date.now()});
})

createBtn?.addEventListener("click", () => {
    const username = usernameInput?.value || 'Anonyme';
    socket.emit("create_room", { username });
});

joinBtn?.addEventListener("click", () => {
    const username = usernameInput?.value || 'Anonyme';
    const code = (roomCodeInput?.value || '').trim().toUpperCase();
    socket.emit("join_room_code", { username, code});
});

function renderRoom(data) {
    if (!data) return;
    const { code, players, max_players, is_full, created_at } = data;
    roomInfo.innerHTML = `
    <div><strong>Room:</strong> ${code}</div>
    <div><strong>Joueurs (${players.length}/${max_players}):</strong> ${players.join(', ') || '-'}</div>
    <div><strong>Status:</strong> ${is_full ? 'Complet' : 'En attente'}</div>
    <div style="margin-top:8px;">
        <button class="btn" onclick="leaveCurrentRoom('${code}')">Quitter la room </button>
    </div>
    `
}

window.leaveCurrentRoom = function(code){
    socket.emit("leave_room_code", { code });
};