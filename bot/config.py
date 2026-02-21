import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str = ""
    database_url: str = ""
    admin_ids: list[int] = field(default_factory=list)

    def __post_init__(self):
        self.bot_token = os.getenv("BOT_TOKEN", "")
        self.database_url = os.getenv("DATABASE_URL", "")
        raw_ids = os.getenv("ADMIN_IDS", "")
        self.admin_ids = [int(x.strip()) for x in raw_ids.split(",") if x.strip()]


config = Config()
