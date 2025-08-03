import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from typing import List, Optional

# --- DATI FINTI COMPLESSI ---

FAKE_SUPPLIERS = {
    "s1": {"id": "s1", "name": "TechGlobal", "contactEmail": "sales@techglobal.com"},
    "s2": {"id": "s2", "name": "BookWorm Inc.", "contactEmail": "orders@bookworm.inc"},
}

FAKE_CATEGORIES = {
    "c1": {"id": "c1", "name": "Elettronica", "parentId": None},
    "c2": {"id": "c2", "name": "Libri", "parentId": None},
    "c1a": {"id": "c1a", "name": "Computer", "parentId": "c1"},
    "c1b": {"id": "c1b", "name": "Accessori", "parentId": "c1a"},
}

FAKE_WAREHOUSES = {
    "wh1": {"id": "wh1", "name": "Magazzino Principale", "location": "Milano"},
    "wh2": {"id": "wh2", "name": "Deposito Nord", "location": "Torino"},
}

FAKE_PRODUCTS = {
    "p1": {"id": "p1", "name": "Tastiera Meccanica RGB", "description": "Tastiera da gaming retroilluminata.", "basePrice": 89.90, "categoryId": "c1b", "supplierId": "s1"},
    "p2": {"id": "p2", "name": "Guida Galattica per Autostoppisti", "description": "Un classico della fantascienza.", "basePrice": 12.50, "categoryId": "c2", "supplierId": "s2"},
}

FAKE_VARIANTS = {
    "v1": {"id": "v1", "sku": "TKL-RGB-ITA", "productId": "p1", "name": "Tastiera Layout Italiano", "priceModifier": 0.0, "attributes": [{"key": "Layout", "value": "ITA"}]},
    "v2": {"id": "v2", "sku": "TKL-RGB-US", "productId": "p1", "name": "Tastiera Layout Americano", "priceModifier": -5.0, "attributes": [{"key": "Layout", "value": "US"}]},
}

FAKE_STOCK = {
    ("p1", "wh1"): 50,
    ("p1", "wh2"): 15,
    ("p2", "wh1"): 200,
}

NEXT_PRODUCT_ID = 3

# --- DEFINIZIONE DEI TIPI STRAWBERRY ---

@strawberry.type
class Attribute:
    key: str
    value: str

@strawberry.type
class ProductVariant:
    id: strawberry.ID
    sku: str
    name: str
    priceModifier: float
    attributes: List[Attribute]

@strawberry.type
class Supplier:
    id: strawberry.ID
    name: str
    contactEmail: Optional[str]
    
    @strawberry.field
    def products(self) -> List["Product"]:
        return [Product(**p) for p in FAKE_PRODUCTS.values() if p["supplierId"] == self.id]

@strawberry.type
class Warehouse:
    id: strawberry.ID
    name: str
    location: str

@strawberry.type
class Category:
    id: strawberry.ID
    name: str
    
    @strawberry.field
    def parent(self) -> Optional["Category"]:
        parent_id = FAKE_CATEGORIES[self.id].get("parentId")
        return Category(**FAKE_CATEGORIES[parent_id]) if parent_id else None

    @strawberry.field
    def children(self) -> List["Category"]:
        return [Category(**c) for c in FAKE_CATEGORIES.values() if c.get("parentId") == self.id]

    @strawberry.field
    def products(self, inStockOnly: bool = False) -> List["Product"]:
        prods = [Product(**p) for p in FAKE_PRODUCTS.values() if p["categoryId"] == self.id]
        if not inStockOnly:
            return prods
        return [p for p in prods if any(s.quantity > 0 for s in p.stockLevels)]


@strawberry.type
class Product:
    id: strawberry.ID
    name: str
    description: str
    basePrice: float
    
    @strawberry.field
    def category(self) -> Category:
        cat_id = FAKE_PRODUCTS[self.id]["categoryId"]
        return Category(**FAKE_CATEGORIES[cat_id])

    @strawberry.field
    def supplier(self) -> Supplier:
        sup_id = FAKE_PRODUCTS[self.id]["supplierId"]
        return Supplier(**FAKE_SUPPLIERS[sup_id])

    @strawberry.field
    def variants(self) -> List[ProductVariant]:
        return [ProductVariant(**v) for v in FAKE_VARIANTS.values() if v["productId"] == self.id]
    
    @strawberry.field
    def stockLevels(self) -> List["StockLevel"]:
        levels = []
        for (prod_id, wh_id), qty in FAKE_STOCK.items():
            if prod_id == self.id:
                levels.append(StockLevel(
                    product=self,
                    warehouse=Warehouse(**FAKE_WAREHOUSES[wh_id]),
                    quantity=qty
                ))
        return levels

@strawberry.type
class StockLevel:
    product: Product
    warehouse: Warehouse
    quantity: int

# --- DEFINIZIONE DI QUERY E MUTATION ---

@strawberry.type
class Query:
    @strawberry.field
    def product(self, id: strawberry.ID) -> Optional[Product]:
        print(f"Richiesta GraphQL per il prodotto ID: {id}")
        return Product(**FAKE_PRODUCTS[id]) if id in FAKE_PRODUCTS else None

    @strawberry.field
    def productsByCategory(self, categoryId: strawberry.ID) -> List[Product]:
        return [Product(**p) for p in FAKE_PRODUCTS.values() if p["categoryId"] == categoryId]

    @strawberry.field
    def searchProducts(self, query: str) -> List[Product]:
        query_lower = query.lower()
        return [Product(**p) for p in FAKE_PRODUCTS.values() if query_lower in p["name"].lower() or query_lower in p["description"].lower()]

    @strawberry.field
    def allCategories(self) -> List[Category]:
        return [Category(**c) for c in FAKE_CATEGORIES.values()]

    @strawberry.field
    def warehouseStock(self, warehouseId: strawberry.ID) -> List[StockLevel]:
        levels = []
        for (prod_id, wh_id), qty in FAKE_STOCK.items():
            if wh_id == warehouseId:
                levels.append(StockLevel(
                    product=Product(**FAKE_PRODUCTS[prod_id]),
                    warehouse=Warehouse(**FAKE_WAREHOUSES[wh_id]),
                    quantity=qty
                ))
        return levels


@strawberry.type
class Mutation:
    @strawberry.mutation
    def createProduct(self, name: str, description: str, basePrice: float, categoryId: strawberry.ID, supplierId: strawberry.ID) -> Product:
        global NEXT_PRODUCT_ID
        print(f"Richiesta GraphQL per creare il prodotto: {name}")
        
        if categoryId not in FAKE_CATEGORIES or supplierId not in FAKE_SUPPLIERS:
            raise ValueError("Categoria o Fornitore non validi.")

        new_id = f"p{NEXT_PRODUCT_ID}"
        new_product_data = {
            "id": new_id, "name": name, "description": description, 
            "basePrice": basePrice, "categoryId": categoryId, "supplierId": supplierId
        }
        FAKE_PRODUCTS[new_id] = new_product_data
        NEXT_PRODUCT_ID += 1
        return Product(**new_product_data)
        
    @strawberry.mutation
    def updateStock(self, productId: strawberry.ID, warehouseId: strawberry.ID, newQuantity: int) -> StockLevel:
        if productId not in FAKE_PRODUCTS or warehouseId not in FAKE_WAREHOUSES:
            raise ValueError("Prodotto o Magazzino non validi.")
        
        FAKE_STOCK[(productId, warehouseId)] = newQuantity
        return StockLevel(
            product=Product(**FAKE_PRODUCTS[productId]),
            warehouse=Warehouse(**FAKE_WAREHOUSES[warehouseId]),
            quantity=newQuantity
        )


# --- AVVIO DEL SERVER ---
schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")

print("Avvio del server GraphQL (complesso) sulla porta 8000...")