from pydantic import BaseModel


class Settings(BaseModel):
    db_url: str = "sqlite:///pixelpit.db"
    starting_coins: int = 1000
    art_creation_cost: int = 100
    inspection_cost: int = 0
    art_width: int = 100
    art_height: int = 100


settings = Settings()
