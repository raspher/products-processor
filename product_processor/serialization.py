import asyncio
import logging
from dataclasses import fields
from typing import AsyncIterator, Type, TypeVar, Generic, cast, get_origin, List, get_args

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
        kwargs: dict[str, object] = {}

        for field in fields(self.product_cls):
            field_name = field.name
            field_type = field.type
            child = elem.find(field_name)

            if child is None:
                # For list fields (images, attributes), initialize empty
                origin = get_origin(field_type)
                if origin in (list, List):
                    kwargs[field_name] = []
                continue

            # --- Handle attributes list ---
            origin = get_origin(field_type)
            args = get_args(field_type)
            if origin in (list, List) and args and args[0] is Attribute:
                attrs: list[Attribute] = []
                for attr_elem in child.findall("attribute"):
                    name_el = attr_elem.find("name")
                    value_el = attr_elem.find("value")
                    if name_el is not None and value_el is not None and name_el.text and value_el.text:
                        attrs.append(Attribute(name=name_el.text.strip(), value=value_el.text.strip()))
                kwargs[field_name] = attrs
                continue

            # --- Handle basic types ---
            if child.text is None:
                continue

            text = child.text.strip()
            if field_type is int:
                kwargs[field_name] = int(text)
            elif field_type is float:
                kwargs[field_name] = float(text)
            elif field_type is bool:
                kwargs[field_name] = text.lower() in {"1", "true", "yes"}
            else:
                kwargs[field_name] = text

        return cast(T, self.product_cls(**kwargs))


class AsyncProductXMLWriter(Generic[T]):
    """Asynchronous writer for Product-like objects using aiofiles."""

    def __init__(self, xml_file: str, product_cls: Type[T]):
        self.xml_file = xml_file
        self.product_cls = product_cls

    def _product_to_element(self, product: Product) -> etree._Element:
        elem = etree.Element("product")

        # Simple fields
        for field in fields(self.product_cls):
            value = getattr(product, field.name)
            if value is None:
                continue

            child: etree.Element = etree.SubElement(elem, field.name)

            if field.name.startswith("description") and isinstance(value, str):
                child.text = etree.CDATA(value)
                continue

            if field.name.startswith("image"):
                child.text = value
                continue

            if field.name.startswith("attributes") and isinstance(value, list):
                for attr in product.attributes:
                    attr_elem = etree.SubElement(child, "attribute")
                    etree.SubElement(attr_elem, "name").text = attr.name
                    etree.SubElement(attr_elem, "value").text = attr.value
                continue

            child.text = str(value)

        return cast(etree._Element, cast(object, elem))

    async def save_products(self, products: AsyncIterator[T]) -> AsyncIterator[T]:
        """Write products asynchronously to an XML file."""
        async with aiofiles.open(self.xml_file, "wb") as f:
            await f.write(b"<?xml version='1.0' encoding='utf-8'?>\n<products>\n")

            async for product in products:
                elem = self._product_to_element(product)
                xml_bytes = etree.tostring(elem, pretty_print=True, encoding="utf-8")
                await f.write(xml_bytes)
                elem.clear()

                yield product

            await f.write(b"</products>\n")
