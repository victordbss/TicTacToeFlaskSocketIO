# Tic Tac Toe Online (en développement)

Un jeu de **Tic Tac Toe multijoueur en temps réel**, développé avec **Flask** et **Socket.IO**.  
Chaque joueur peut créer une salle privée, partager le code avec un ami et jouer en direct.

---

## 🚀 Fonctionnalités actuelles

- Création de salles avec code unique.  
- Rejoindre et quitter une salle existante.  
- Limitation du nombre de joueurs par salle (2 joueurs).  
- Mise à jour en temps réel de l’état des salles.  

---

## 🛠️ Installation

### 1. Cloner le dépôt
```bash
git clone https://github.com/tonpseudo/nom-du-repo.git
cd nom-du-repo
```
### 2. Créer un environnement virtuel
```bash
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```
### 3. Installer les dépendances
```bash
pip install flask flask-socketio
```

## ▶️ Lancer le serveur
```bash
python app.py
```
