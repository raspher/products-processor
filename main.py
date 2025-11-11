from dataclasses import replace
from typing import Iterable

from product_processor.product import Product
from product_processor.serialization import ProductXMLReader, ProductXMLWriter


def fix_amps(ps: Iterable[Product]) -> Iterable[Product]:
    """
    Modify a Product in any way you need.
    You can change fields, filter, or enrich data here.
    """

    def _fix_amps(text: str) -> str:
        return (text
                .replace("&amp;nbsp;", " ")
                .replace("&amp;amp;", "&")
                .replace("&amp;", "&"))

    # Example modifications
    for p in ps:
        p.description = _fix_amps(p.description)
        p.description_extra_1 = _fix_amps(p.description_extra_1)
        p.description_extra_2 = _fix_amps(p.description_extra_2)
        p.name = _fix_amps(p.name)
        yield p


if __name__ == "__main__":
    reader = ProductXMLReader("products.xml")
    writer = ProductXMLWriter("test.xml")
    try:
        pipeline = reader.stream_products()
        pipeline = fix_amps(pipeline)
        writer.save_products(pipeline)
    except KeyboardInterrupt:
        print("\nParsing stopped by user")
