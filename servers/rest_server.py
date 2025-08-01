# File: servers/rest_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

class Order(BaseModel):
    orderId: str
    userId: int # Usiamo userId per coerenza
    productIds: List[str]
    shippingAddress: str # <-- AGGIUNTO IL CAMPO MANCANTE
    status: str

app = FastAPI(title="Orders API")

FAKE_ORDERS_DB = {
    "ord-001": Order(
        orderId="ord-001", 
        userId=1, 
        productIds=["101", "102"], 
        shippingAddress="Via Roma 1, 10121 Torino TO, Italia", # <-- AGGIUNTO IL DATO
        status="Shipped"
    ),
    "ord-002": Order(
        orderId="ord-002", 
        userId=2, 
        productIds=["101"], 
        shippingAddress="Piazza Duomo 1, 20121 Milano MI, Italia", # <-- AGGIUNTO IL DATO
        status="Processing"
    ),
}

@app.get("/orders/{order_id}", response_model=Order, summary="Recupera i dettagli di un singolo ordine")
def get_order_details(order_id: str):
    """Ottiene i dati completi di un ordine, inclusi l'ID utente, i prodotti e l'indirizzo di spedizione."""
    return FAKE_ORDERS_DB.get(order_id)

@app.get("/orders", response_model=List[Order], summary="Elenca gli ordini, filtrabili per utente")
def list_orders_for_user(user_id: Optional[int] = None):
    """Restituisce una lista di ordini. Se viene fornito un 'user_id' numerico, filtra gli ordini per quel cliente."""
    if user_id:
        return [order for order in FAKE_ORDERS_DB.values() if order.userId == user_id]
    return list(FAKE_ORDERS_DB.values())