# servers/reviews_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

class Review(BaseModel):
    reviewId: str
    productId: str
    userId: int
    rating: int
    comment: str

class CreateReviewRequest(BaseModel):
    productId: str
    userId: int
    rating: int  # Dovrebbe essere tra 1 e 5
    comment: str

app = FastAPI(title="Product Reviews API")

FAKE_REVIEWS_DB = [
    Review(reviewId="rev-01", productId="prod-123", userId=1, rating=5, comment="Fantastico!"),
    Review(reviewId="rev-02", productId="prod-456", userId=2, rating=2, comment="Non mi è piaciuto."),
    Review(reviewId="rev-03", productId="prod-123", userId=2, rating=4, comment="Buon prodotto, consigliato."),
]

# In servers/reviews_server.py

@app.get("/reviews", response_model=List[Review], summary="Ottiene recensioni, filtrabili per prodotto O per utente")
def get_reviews(product_id: Optional[str] = None, user_id: Optional[int] = None):
    """
    Restituisce una lista di recensioni.
    Eventualmente puoi filtrare o per 'product_id' o per 'user_id'.
    """
    if product_id:
        return [r for r in FAKE_REVIEWS_DB if r.productId == product_id]
    if user_id:
        return [r for r in FAKE_REVIEWS_DB if r.userId == user_id]
    
    return FAKE_REVIEWS_DB
    
    # Se nessuno dei due è fornito, restituisci un errore
    raise HTTPException(status_code=400, detail="Devi fornire o 'product_id' o 'user_id'.")

# Aggiungiamo l'endpoint che mancava!
@app.get("/reviews/{review_id}", response_model=Review, summary="Ottiene una singola recensione dal suo ID")
def get_review_by_id(review_id: str):
    """Restituisce i dettagli di una singola recensione dato il suo 'review_id' (es. 'rev-02')."""
    for review in FAKE_REVIEWS_DB:
        if review.reviewId == review_id:
            return review
    raise HTTPException(status_code=404, detail="Recensione non trovata.")

@app.post("/reviews", response_model=Review, summary="Crea una nuova recensione")
def create_review(review_data: CreateReviewRequest):
    """
    Crea una nuova recensione per un prodotto.
    Il rating deve essere tra 1 e 5.
    """
    # Validazione del rating
    if review_data.rating < 1 or review_data.rating > 5:
        raise HTTPException(
            status_code=400, 
            detail="Il rating deve essere tra 1 e 5"
        )
    
    # Genera un nuovo ID recensione
    # In produzione useresti un UUID o un ID dal database
    next_review_number = len(FAKE_REVIEWS_DB) + 1
    new_review_id = f"rev-{next_review_number:02d}"
    
    # Crea la nuova recensione
    new_review = Review(
        reviewId=new_review_id,
        productId=review_data.productId,
        userId=review_data.userId,
        rating=review_data.rating,
        comment=review_data.comment
    )
    
    # Aggiungi al "database" fake
    FAKE_REVIEWS_DB.append(new_review)
    
    return new_review