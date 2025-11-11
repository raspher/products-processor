from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Attribute:
    name: str
    value: str


@dataclass
class Product:
    product_id: int
    name: str
    quantity: int
    ean: str
    sku: str
    category_name: str
    price: float
    tax_rate: str
    weight: float
    width: float
    height: float
    length: float
    description: str
    manufacturer_name: str = ""
    description_extra_1: Optional[str] = None
    description_extra_2: Optional[str] = None
    images: List[str] = field(default_factory=list)
    attributes: List[Attribute] = field(default_factory=list)


@dataclass
class ProductWithName(Product):
    man_name: Optional[str] = None
