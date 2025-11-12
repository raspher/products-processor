import asyncio
import logging
from dataclasses import fields
from typing import AsyncIterator, Type, TypeVar, Generic, cast

import aiofiles
from lxml import etree

from product_processor.product import Product, Attribute

T = TypeVar("T", bound=Product)


class AsyncProductXMLReader(Generic[T]):
    """
    Asynchronous streaming XML reader for <product> elements.
    Uses a thread for CPU-bound parsing but yields results asynchronously.
    """

    def __init__(self, xml_file: str, product_cls: Type[T]):
        self.xml_file = xml_file
        self.product_cls = product_cls

    async def stream_products(self) -> AsyncIterator[T]:
        """Yield Product objects asynchronously, one at a time."""

        def blocking_iter():
            context = etree.iterparse(self.xml_file, events=("end",), tag="product")
            for _, elem in context:
                try:
                    yield self._element_to_product(elem)
                finally:
                    elem.clear()
                    while elem.getprevious() is not None:
                        del elem.getparent()[0]

        try:
            # Wrap the blocking iterator in an async generator
            for product in await asyncio.to_thread(lambda: blocking_iter()):
                yield product
        except Exception as e:
            logging.error(f"Error while parsing XML: {e}")

    def _element_to_product(self, elem: etree._Element) -> T:
        kwargs = {}
        # Parse simple fields
        for field in fields(self.product_cls):
            child = elem.find(field.name)
            if child is not None and child.text is not None:
                text = child.text
                if Type[field.type] == Type[int]:
                    kwargs[field.name] = int(text)
                elif Type[field.type] == Type[float]:
                    kwargs[field.name] = float(text)
                else:
                    kwargs[field.name] = text

        # Images
        images: list[str] = []
        images_elem = elem.find("images")
        if images_elem is not None:
            for img_elem in images_elem.findall("image"):
                if img_elem.text:
                    images.append(img_elem.text)
        kwargs["images"] = images

        # Attributes
        attributes: list[Attribute] = []
        attrs_elem = elem.find("attributes")
        if attrs_elem is not None:
            for attr_elem in attrs_elem.findall("attribute"):
                name = attr_elem.find("attribute_name").text or ""
                value = attr_elem.find("attribute_value").text or ""
                if name and value:
                    attributes.append(Attribute(name=name, value=value))
        kwargs["attributes"] = attributes

        return self.product_cls(**kwargs)


class AsyncProductXMLWriter(Generic[T]):
    """Asynchronous writer for Product-like objects using aiofiles."""

    def __init__(self, xml_file: str, product_cls: Type[T]):
        self.xml_file = xml_file
        self.product_cls = product_cls

    @staticmethod
    def _product_to_element(product: Product) -> etree._Element:
        elem = etree.Element("product")

        # Simple fields
        for field in [
            "product_id", "name", "quantity", "ean", "sku",
            "category_name", "manufacturer_name", "price",
            "tax_rate", "weight", "width", "height", "length",
            "description", "description_extra_1", "description_extra_2"
        ]:
            value = getattr(product, field)
            if value is not None:
                child = etree.SubElement(elem, field)
                if field.startswith("description") and isinstance(value, str):
                    child.text = etree.CDATA(value)
                else:
                    child.text = str(value)

        # Images
        if product.images:
            images_elem = etree.SubElement(elem, "images")
            for img in product.images:
                etree.SubElement(images_elem, "image").text = str(img)

        # Attributes
        if product.attributes:
            attrs_elem = etree.SubElement(elem, "attributes")
            for attr in product.attributes:
                attr_elem = etree.SubElement(attrs_elem, "attribute")
                etree.SubElement(attr_elem, "name").text = attr.name
                etree.SubElement(attr_elem, "value").text = attr.value

        return cast(etree._Element, cast(object, elem))

    async def save_products(self, products: AsyncIterator[T]) -> AsyncIterator[T]:
        """Write products asynchronously to an XML file."""
        async with aiofiles.open(self.xml_file, "wb") as f:
            await f.write(b"<?xml version='1.0' encoding='utf-8'?>\n<products>\n")

            loop = asyncio.get_running_loop()

            async for product in products:
                elem = self._product_to_element(product)
                xml_bytes = etree.tostring(elem, pretty_print=True, encoding="utf-8")
                await f.write(xml_bytes)
                elem.clear()

                yield product

            await f.write(b"</products>\n")
