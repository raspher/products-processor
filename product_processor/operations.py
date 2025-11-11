from typing import Iterable, TypeVar

from product_processor.product import Product, ProductWithName, Attribute

T = TypeVar("T", bound=Product)

class Operations:
    @staticmethod
    def fix_amps(ps: Iterable[T]) -> Iterable[T]:
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

    @staticmethod
    def name_to_attrs(ps: Iterable[T]) -> Iterable[T]:
        for p in ps:
            if isinstance(p, ProductWithName) and p.man_name and p.man_name.strip():
                p.add_attribute("Nazwa", p.man_name)
            else:
                p.add_attribute("Nazwa", p.name)
            yield p
