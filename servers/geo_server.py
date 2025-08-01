# servers/geo_server.py
from fastapi import FastAPI
from pydantic import BaseModel

class Coordinates(BaseModel):
    latitude: float
    longitude: float

app = FastAPI(title="Geolocation Utility API")

# Nota: questi indirizzi corrispondono a quelli nel server degli ordini
ADDRESS_COORDINATES = {
    "Via Roma 1, 10121 Torino TO, Italia": Coordinates(latitude=45.0703, longitude=7.6869),
    "Piazza Duomo 1, 20121 Milano MI, Italia": Coordinates(latitude=45.4642, longitude=9.1895),
}

@app.get("/geocode", response_model=Coordinates, summary="Converte un indirizzo stradale in coordinate GPS")
def geocode_address(address: str):
    """Prende un indirizzo stradale completo e restituisce le sue coordinate geografiche (latitudine e longitudine)."""
    for addr, coords in ADDRESS_COORDINATES.items():
        if address.lower() == addr.lower():
            return coords
    return None