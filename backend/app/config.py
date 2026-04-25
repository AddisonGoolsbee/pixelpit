from pydantic import BaseModel


class Settings(BaseModel):
    db_url: str = "sqlite:///pixelpit.db"
    starting_coins: int = 1000
    art_creation_cost: int = 50
    listing_fee: int = 10
    research_cost: int = 20
    art_width: int = 100
    art_height: int = 100
    face_size: int = 32


settings = Settings()
