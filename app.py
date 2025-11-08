from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os

app = Flask(__name__, static_folder='.')

DB = 'goal_ach.db'

# Initialize database
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # Goal table
    c.execute('''CREATE TABLE IF NOT EXISTS goal (
                    id INTEGER PRIMARY KEY, 
                    target_amount REAL DEFAULT 1000, 
                    current_amount REAL DEFAULT 1000
                 )''')
    # Achievement table
    c.execute('''CREATE TABLE IF NOT EXISTS achievement (
                    id INTEGER PRIMARY KEY, 
                    amount REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                 )''')
    # Deduction table
    c.execute('''CREATE TABLE IF NOT EXISTS deduction (
                    id INTEGER PRIMARY KEY, 
                    amount REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                 )''')
    # History table
    c.execute('''CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY, 
                    type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                 )''')
    # Insert default goal if empty
    c.execute('SELECT COUNT(*) FROM goal')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO goal (target_amount, current_amount) VALUES (1000, 1000)')
    conn.commit()
    conn.close()

init_db()

# Serve HTML
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Get current state
@app.route('/api/state', methods=['GET'])
def get_state():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT target_amount, current_amount FROM goal WHERE id=1')
    goal = c.fetchone()
    c.execute('SELECT SUM(amount) FROM achievement')
    ach = c.fetchone()[0] or 0
    # Fetch histories
    c.execute("SELECT type, amount, created_at FROM history ORDER BY created_at DESC")
    history = [{'type': t, 'amount': a, 'created_at': d} for t, a, d in c.fetchall()]
    conn.close()
    return jsonify({
        'target': goal[0],
        'goal': goal[1],
        'achievement': ach,
        'history': history
    })

# Deduct from goal
@app.route('/api/deduct', methods=['POST'])
def deduct():
    amount = float(request.json['amount'])
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # Update goal
    c.execute('UPDATE goal SET current_amount = current_amount - ? WHERE id=1', (amount,))
    # Save history
    c.execute('INSERT INTO deduction (amount) VALUES (?)', (amount,))
    c.execute('INSERT INTO history (type, amount) VALUES (?, ?)', ('deduct', amount))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# Add achievement
@app.route('/api/add', methods=['POST'])
def add_achievement():
    amount = float(request.json['amount'])
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('INSERT INTO achievement (amount) VALUES (?)', (amount,))
    c.execute('INSERT INTO history (type, amount) VALUES (?, ?)', ('add', amount))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
