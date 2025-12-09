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
    description: str = ""
    description_extra_1: Optional[str] = None
    description_extra_2: Optional[str] = None
    manufacturer_name: str = ""
    purchase_price: str = ""
    image: str = ""
    image_extra_1: str = ""
    image_extra_2: str = ""
    image_extra_3: str = ""
    image_extra_4: str = ""
    image_extra_5: str = ""
    image_extra_6: str = ""
    image_extra_7: str = ""
    image_extra_8: str = ""
    image_extra_9: str = ""
    image_extra_10: str = ""
    image_extra_11: str = ""
    image_extra_12: str = ""
    image_extra_13: str = ""
    image_extra_14: str = ""
    image_extra_15: str = ""
    attributes: List[Attribute] = field(default_factory=list)
    variants: str = ""

    def add_attribute(self, name: str, value: str):
        """
        Upsert an attribute: if an attribute with the given name exists,
        update its value; otherwise, add a new attribute.
        """
        for attr in self.attributes:
            if attr.name == name:
                attr.value = value
                return
        # If not found, add new
        self.attributes.append(Attribute(name=name, value=value))


@dataclass
class ProductWithName(Product):
    man_name: Optional[str] = None
