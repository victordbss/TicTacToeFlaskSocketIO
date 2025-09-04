from __future__ import annotations
from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit, join_room as sio_join_room, leave_room as sio_leave_room
from dataclasses import dataclass, field
from typing import Dict, Optional, List
import os, time, random, string

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv('SECRET_KEY', 'dev-secret')
socketio = SocketIO(app, cors_allowed_origins="*")

def generate_code(lenght : int = 6) -> str:
    new_code = ''
    for _ in range(lenght):
        new_code += random.choice(string.ascii_uppercase + string.digits)
    return new_code

@dataclass
class Player:
    sid: str
    name: str
    joined_at: float = field(default_factory=time.time)

@dataclass
class Room:
    code: str
    max_players: int = 3
    players: Dict[str, Player] = field(default_factory=dict)
    created_at : float = field(default_factory=time.time)

    def add(self, player : Player) -> None:
        if self.is_full():
            raise ValueError("Room is full")
        self.players[player.sid] = player
    
    def remove_sid(self, sid : str) -> None:
        self.players.pop(sid, None)

    def is_full(self) -> bool:
        return len(self.players) >= self.max_players

    def is_empty(self) -> bool:
        return len(self.players) == 0
    
    def list_names(self) -> List[str]:
        return [p.name for p in self.players.values()]

    def to_public(self) -> dict:
        return {
            "code": self.code,
            "players": self.list_names(),
            "max_players": self.max_players,
            "is_full" : self.is_full(),
            "created_at": self.created_at
        }

class TicTacToeGame:
    def __init__(self) -> None:
        self.board : List[Optional[str]] = [None] * 9
        self.current_turn : str = "X"
        self.winner : Optional[str] = None
        self.is_draw : bool = False
    
    def play_move(self, index : int) -> bool:
        if self.winner or self.is_draw:
            return False
        if index < 0 or index >= 9:
            return False
        if self.board[index] is not None:
            return False
        
        self.board[index] = self.current_turn

        if self._check_winner():
            self.winner = self.current_turn
        elif all(cell is not None for cell in self.board):
            self.is_draw = True
        
        if not(self.winner or self.is_draw):
            self.current_turn = "O" if self.current_turn == "X" else "X"
        
        return True

    def _check_winner(self) -> bool:
        win_combos = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8], # Lignes
            [0, 3, 6], [1, 4, 7], [2, 5, 8], # colonnes
            [0, 4, 8], [2, 4, 5], # diagonales
        ]

        for a, b, c in win_combos:
            if self.board[a] == self.board[b] == self.board[c] and self.board[a] is not None:
                return True
            
        return False
    
    def to_public(self) -> Dict:
        return {
            "board" : self.board,
            "current_turn": self.current_turn,
            "winner": self.winner,
            "is_draw": self.is_draw,
        }
    
    def reset(self) -> None:
        self.board = [None] * 9
        self.current_turn = "X"
        self.winner = None
        self.is_draw = False

class Registry:
    def __init__(self) -> None:
        self.rooms: Dict[str, Room] = {}
        self.sid_to_code: Dict[str, List[str]] = {}
    
    def create_room(self) -> Room:
        for _ in range(100):
            code = generate_code()
            if code not in self.rooms:
                room = Room(code=code)
                self.rooms[code] = room
                return room

        raise RuntimeError("Unable to generate unique room code")
    
    def get(self, code: str) -> Optional[Room]:
        return self.rooms.get(code)
    
    def link(self, sid: str, code: str) -> None:
        self.sid_to_code.setdefault(sid, []).append(code)
    
    def unlink(self, sid:str, code:str) -> None:
        codes = self.sid_to_code.get(sid, [])
        if code in codes:
            codes.remove(code)
        if not codes and sid in self.sid_to_code:
            del self.sid_to_code[sid]
    
    def leave_everything(self, sid: str) -> List[str]:
        impacted: List[str] = []
        for code in list(self.sid_to_code.get(sid, [])):
            room = self.rooms[code]
            if not room:
                continue

            room.remove_sid(sid)
            self.unlink(sid, code)
            if room.is_empty():
                del self.rooms[code]
            
            impacted.append(code)
        return impacted

registry = Registry()

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("connect")
def on_connect():
    print(f"[connect] client : {request.sid}")
    emit("server_message", {"msg" : "Bienvenue! Connexion établie"})

@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    impacted_codes = registry.leave_everything(sid)
    for code in impacted_codes:
        emit("room_update", registry.get(code).to_public if registry.get(code) else {"code": code, "players": []}, room=code)

@socketio.on("ping_from_client")
def handle_ping(data):
    client_time = data.get("when")
    emit("pong_from_server", {"client_time" : client_time})

@socketio.on("create_room")
def on_create_room(data):
    username = (data or {}).get('username', 'Anonyme')
    sid = request.sid

    room = registry.create_room()
    player = Player(sid=sid, name=username)
    room.add(player)

    sio_join_room(room.code)
    registry.link(sid, room.code)

    print(f"{username} created a room {room.code}")
    emit("room_joined", room.to_public(), to=sid)
    emit("room_update", room.to_public(), room=room.code)

@socketio.on("join_room_code")
def on_join_room_code(data):
    username = (data or {}).get('username', 'Anonyme')
    code = (data or {}).get('code', '').upper()
    sid = request.sid

    room = registry.get(code)
    if not room:
        emit("error_message", {'msg': f"Room {code} inexistante"}, to=sid)
        return
    if room.is_full():
        emit("error_message", {'msg' : f"Room {code} est pleine"}, to=sid)
        return
    
    player = Player(sid=sid, name=username)
    room.add(player)

    sio_join_room(room.code)
    registry.link(sid, code)

    print(f"{username} joined the room {code}")
    emit("room_joined", room.to_public(), to=sid)
    emit("room_update", room.to_public(), room=room.code)

@socketio.on("leave_room_code")
def on_leave_room_code(data):
    code = (data or {}).get('code', '').upper()
    sid = request.sid

    room = registry.get(code)
    if not room:
        return
    
    room.remove_sid(sid)
    registry.unlink(sid, code)
    sio_leave_room(code)

    if room.is_empty():
        del registry.rooms[code]
        emit("room_deleted", {'code': code}, to=sid)
    else:
        emit("room_update", room.to_public(), room=code)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080, debug=True)