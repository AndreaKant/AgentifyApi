import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

# Dati finti per il nostro server
FAKE_PRODUCTS = {
    "101": {"id": "101", "name": "Libro di Fantascienza", "price": 19.99, "inStock": True},
    "102": {"id": "102", "name": "Tastiera Meccanica", "price": 89.50, "inStock": False},
}
NEXT_ID = 103

@strawberry.type
class Product:
    id: strawberry.ID
    name: str
    price: float
    inStock: bool

@strawberry.type
class Query:
    @strawberry.field
    def getProduct(self, productId: strawberry.ID) -> Product | None:
        print(f"Richiesta GraphQL ricevuta per il prodotto ID: {productId}")
        product_data = FAKE_PRODUCTS.get(productId)
        if product_data:
            return Product(**product_data)
        return None

@strawberry.type
class Mutation:
    @strawberry.mutation
    def createProduct(self, name: str, price: float) -> Product:
        global NEXT_ID
        print(f"Richiesta GraphQL ricevuta per creare il prodotto: {name}")
        new_product = {
            "id": str(NEXT_ID),
            "name": name,
            "price": price,
            "inStock": True
        }
        FAKE_PRODUCTS[str(NEXT_ID)] = new_product
        NEXT_ID += 1
        return Product(**new_product)


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")

print("Avvio del server GraphQL sulla porta 8000...")