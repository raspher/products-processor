from typing import Iterator, Iterable
from lxml import etree

from product_processor.product import Product, Attribute


class ProductXMLReader:
    """Streaming reader for <product> elements using lxml, memory-safe."""

    def __init__(self, xml_file: str):
        self.xml_file = xml_file

    def stream_products(self) -> Iterator[Product]:
        """Yield Product objects one by one from XML."""
        try:
            context = etree.iterparse(self.xml_file, events=("end",), tag="product")

            for _, elem in context:
                try:
                    product = self._element_to_product(elem)
                    yield product
                except Exception as e:
                    print(e)
                finally:
                    elem.clear()
                    while elem.getprevious() is not None:
                        del elem.getparent()[0]
        except Exception:
            print("Something went wrong!")

    @staticmethod
    def _element_to_product(elem: etree._Element) -> Product:
        """Convert <product> element to Product dataclass."""
        kwargs = {}

        # Simple fields
        for field in [
            "product_id", "name", "quantity", "ean", "sku",
            "category_name", "manufacturer_name", "price",
            "tax_rate", "weight", "width", "height", "length",
            "description", "description_extra_1", "description_extra_2"
        ]:
            child = elem.find(field)
            if child is not None and child.text is not None:
                text = child.text
                if field in ("product_id", "quantity"):
                    kwargs[field] = int(text)
                elif field in ("price", "weight", "width", "height", "length"):
                    kwargs[field] = float(text)
                else:
                    kwargs[field] = text

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
                name = attr_elem.findtext("name") or ""
                value = attr_elem.findtext("value") or ""
                attributes.append(Attribute(name=name, value=value))
        kwargs["attributes"] = attributes

        return Product(**kwargs)


class ProductXMLWriter:
    """Streaming writer for Product objects using lxml, memory-efficient."""

    def __init__(self, xml_file: str, indent: int = 4):
        self.xml_file = xml_file
        self.indent = indent

    @staticmethod
    def _product_to_element(product: Product) -> etree.Element:
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
                # Wrap description fields in CDATA
                if field.startswith("description") and isinstance(value, str):
                    child.text = etree.CDATA(value)
                else:
                    child.text = str(value)

        # Images
        if product.images:
            images_elem = etree.SubElement(elem, "images")
            for img in product.images:
                img_elem = etree.SubElement(images_elem, "image")
                img_elem.text = str(img)

        # Attributes
        if product.attributes:
            attrs_elem = etree.SubElement(elem, "attributes")
            for attr in product.attributes:
                attr_elem = etree.SubElement(attrs_elem, "attribute")
                name_elem = etree.SubElement(attr_elem, "name")
                name_elem.text = attr.name
                val_elem = etree.SubElement(attr_elem, "value")
                val_elem.text = attr.value

        return elem

    def save_products(self, products: Iterable[Product]) -> None:
        """Write products to XML file, one at a time."""
        with open(self.xml_file, "wb") as f:
            f.write(b"<?xml version='1.0' encoding='utf-8'?>\n")
            f.write(b"<products>\n")

            for product in products:
                elem = self._product_to_element(product)
                xml_bytes = etree.tostring(elem, pretty_print=True, encoding="utf-8")
                f.write(xml_bytes)
                elem.clear()

            f.write(b"</products>\n")
