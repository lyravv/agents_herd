import sqlite3
import json
import threading
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

DB_PATH = os.getenv("WHITEBOARD_DB", "whiteboard.db")
_lock = threading.Lock()  

class Whiteboard:
    def __init__(self, board_id: str):
        if not board_id or not isinstance(board_id, str):
            raise ValueError("board_id must be a non-empty string")
        self.board_id = board_id
        self._init_db()

    def _init_db(self):
        with _lock:
            conn = sqlite3.connect(DB_PATH, timeout=10)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS message_boards (
                    board_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp REAL DEFAULT (strftime('%s', 'now')),
                    seq INTEGER
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS board_seq (
                    board_id TEXT PRIMARY KEY,
                    next_seq INTEGER DEFAULT 0
                )
            """)
            conn.commit()
            conn.close()

    def append(self, message: dict):
        """
        追加一条消息（如 {"role": "assistant", "content": "..."}）
        """
        if not isinstance(message, dict):
            raise TypeError("message must be a dict")
        serialized = json.dumps(message, ensure_ascii=False)

        with _lock:
            conn = sqlite3.connect(DB_PATH, timeout=10)
            cursor = conn.cursor()

            cursor.execute("INSERT OR IGNORE INTO board_seq (board_id, next_seq) VALUES (?, 0)", (self.board_id,))
            cursor.execute("UPDATE board_seq SET next_seq = next_seq + 1 WHERE board_id = ?", (self.board_id,))
            cursor.execute("SELECT next_seq FROM board_seq WHERE board_id = ?", (self.board_id,))
            seq = cursor.fetchone()[0]

            cursor.execute(
                "INSERT INTO message_boards (board_id, message, seq) VALUES (?, ?, ?)",
                (self.board_id, serialized, seq)
            )
            conn.commit()
            conn.close()

    def read(self) -> list[dict]:
        """
        返回按顺序排列的消息列表
        """
        with _lock:
            conn = sqlite3.connect(DB_PATH, timeout=10)
            cursor = conn.execute(
                "SELECT message FROM message_boards WHERE board_id = ? ORDER BY seq ASC",
                (self.board_id,)
            )
            rows = cursor.fetchall()
            conn.close()
            return [json.loads(row[0]) for row in rows]

    def clear(self):
        """清空该 board_id 的所有消息"""
        with _lock:
            conn = sqlite3.connect(DB_PATH, timeout=10)
            conn.execute("DELETE FROM message_boards WHERE board_id = ?", (self.board_id,))
            conn.execute("UPDATE board_seq SET next_seq = 0 WHERE board_id = ?", (self.board_id,))
            conn.commit()
            conn.close()

    def __len__(self):
        with _lock:
            conn = sqlite3.connect(DB_PATH, timeout=10)
            cursor = conn.execute("SELECT COUNT(*) FROM message_boards WHERE board_id = ?", (self.board_id,))
            count = cursor.fetchone()[0]
            conn.close()
            return count

if __name__ == "__main__":
    whiteboard = Whiteboard("test_board")
    whiteboard.append({"role": "user", "content": "英伟达当前的股价"})
    whiteboard.append({
        "role": "assistant", 
        "content": None,
        "tool_calls": [
            {
                "id": "call_web_search_001",
                "type": "function",
                "function": {
                    "name": "web_search",
                    "arguments": '{"query": "英伟达股价"}'
                }
            }
        ]
    })
    whiteboard.append({
        "role": "tool",
        "tool_call_id": "call_web_search_001",
        "content": "英伟达当前的股价是120美元"
    })
    print(whiteboard.read())
    print(len(whiteboard))
    # whiteboard.clear()
    print(whiteboard.read())
    print(len(whiteboard))
