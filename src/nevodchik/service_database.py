import logging

import aiosqlite as SQLite

logger = logging.getLogger(__name__)


class ServiceDatabase:
    def __init__(self, db_file: str = "./data/nevodchik.db"):
        self.db_file = db_file
        self.db: SQLite.Connection | None = None

    async def connect(self):
        self.db = await SQLite.connect(self.db_file)
        await self._init_db()
        logger.info(f"DB connected: {self.db_file}")

    async def disconnect(self):
        if self.db:
            await self.db.close()
            logger.info(f"DB disconnected: {self.db_file}")

    async def _init_db(self):
        # Start with node list table
        await self.db.execute(
            """CREATE TABLE IF NOT EXISTS nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            addr TEXT NOT NULL,
            proto TEXT NOT NULL,

            name_full TEXT,
            name_short TEXT,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE (addr, proto));
            """
        )
        # Then go with messages table
        await self.db.execute(
            """CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            msg_ref TEXT NOT NULL,
            proto TEXT NOT NULL,
            
            chan_name TEXT,
            sent_by_id INTEGER,
            heard_by_id INTEGER,
            reply_to_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

            rx_rssi INTEGER,
            rx_snr REAL,

            text TEXT,

            UNIQUE (proto, msg_ref)),

            FOREIGN KEY(sent_by_id) REFERENCES nodes(id) ON DELETE SET NULL,
            FOREIGN KEY(heard_by_id) REFERENCES nodes(id) ON DELETE SET NULL,
            FOREIGN KEY(reply_to_id) REFERENCES messages(id) ON DELETE CASCADE);
            """
        )
        # Positions. Because why not?
        await self.db.execute(
            """CREATE TABLE IF NOT EXISTS positions (
            node_id INTEGER PRIMARY KEY,

            lat REAL,
            lon REAL,
            alt INT,
            
            FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE);
            """
        )

        await self.db.commit()
