import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson.objectid import ObjectId

from database import db, create_document, get_documents
from schemas import Product, Order

app = FastAPI(title="Mens Aesthetic Store API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Mens Aesthetic Store Backend Running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


# Utility to convert Mongo _id to string

def serialize_doc(doc: dict):
    if not doc:
        return doc
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc


# Seed products endpoint (one-time seeding for demo)

class SeedResponse(BaseModel):
    inserted: int


@app.post("/seed", response_model=SeedResponse)
def seed_products():
    existing = db["product"].count_documents({}) if db else 0
    if existing > 0:
        return {"inserted": 0}

    demo_products: List[Product] = [
        Product(
            title="Minimalist Black Tee",
            description="Premium cotton tee with a tailored fit.",
            price=29.0,
            category="tops",
            in_stock=True,
            images=[
                "https://images.unsplash.com/photo-1512436991641-6745cdb1723f?q=80&w=1200&auto=format&fit=crop"
            ],
            sizes=["S", "M", "L", "XL"],
            colors=["black"],
            tags=["minimal", "tee", "black"]
        ),
        Product(
            title="Cream Overshirt",
            description="Structured overshirt with clean lines.",
            price=69.0,
            category="outerwear",
            in_stock=True,
            images=[
                "https://images.unsplash.com/photo-1520975922284-4bdf4a4cf7bd?q=80&w=1200&auto=format&fit=crop"
            ],
            sizes=["S", "M", "L"],
            colors=["cream"],
            tags=["overshirt", "neutral"]
        ),
        Product(
            title="Tapered Wool Trousers",
            description="Ankle length smart casual fit.",
            price=89.0,
            category="bottoms",
            in_stock=True,
            images=[
                "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?q=80&w=1200&auto=format&fit=crop"
            ],
            sizes=["28", "30", "32", "34"],
            colors=["charcoal"],
            tags=["trousers", "wool", "tapered"]
        ),
        Product(
            title="White Leather Sneakers",
            description="Low-profile minimalist sneakers.",
            price=99.0,
            category="footwear",
            in_stock=True,
            images=[
                "https://images.unsplash.com/photo-1519741497674-611481863552?q=80&w=1200&auto=format&fit=crop"
            ],
            sizes=["8", "9", "10", "11"],
            colors=["white"],
            tags=["sneakers", "leather", "white"]
        ),
    ]

    inserted = 0
    for p in demo_products:
        create_document("product", p)
        inserted += 1
    return {"inserted": inserted}


# Product listing and detail

@app.get("/products")
def list_products(q: Optional[str] = None, category: Optional[str] = None):
    filter_dict = {}
    if q:
        filter_dict["title"] = {"$regex": q, "$options": "i"}
    if category:
        filter_dict["category"] = category
    docs = get_documents("product", filter_dict)
    return [serialize_doc(d) for d in docs]


@app.get("/products/{product_id}")
def get_product(product_id: str):
    try:
        doc = db["product"].find_one({"_id": ObjectId(product_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Product not found")
        return serialize_doc(doc)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product id")


# Orders

@app.post("/orders")
def create_order(order: Order):
    order_id = create_document("order", order)
    return {"id": order_id, "status": "created"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
