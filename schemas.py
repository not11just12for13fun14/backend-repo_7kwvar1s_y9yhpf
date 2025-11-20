"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Add your own schemas here:
# --------------------------------------------------

class Lead(BaseModel):
    """
    Leads collection schema for parents interested in Kids/Mini Kids summer courses
    Collection name: "lead"
    """
    parent_name: str = Field(..., description="Parent or guardian full name")
    parent_email: EmailStr = Field(..., description="Parent email address")
    parent_phone: str = Field(..., description="Contact phone number")

    child_name: str = Field(..., description="Child full name")
    child_age: int = Field(..., ge=3, le=17, description="Child age")

    program: str = Field(..., description="Program selected: Mini Kids (4-6) or Kids (7-13)")
    sede: str = Field(..., description="Selected Lima location: San Isidro, La Molina, Pueblo Libre, Breña, San Miguel")

    courses: List[str] = Field(default_factory=list, description="Selected courses of interest")
    message: Optional[str] = Field(None, description="Additional message or questions")
    source: Optional[str] = Field(None, description="Marketing source or campaign tag")
