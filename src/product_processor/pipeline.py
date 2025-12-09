import re
from typing import TypeVar, Generic, AsyncIterator, Callable, Awaitable, Optional

from product_processor.product import Product, ProductWithName

T = TypeVar("T", bound=Product)


class Operation(Generic[T]):
    """Base async operation on a Product."""

    async def __call__(self, p: T) -> T:
        raise NotImplementedError


class FixAmpersands(Operation[T]):
    async def __call__(self, p: T) -> T:
        def _fix_amps(text: str | None) -> str:
            if not text:
                return ""
            return (text
                    .replace("&amp;nbsp;", " ")
                    .replace("&amp;amp;", "&")
                    .replace("&amp;", "&"))

        p.description = _fix_amps(p.description)
        p.description_extra_1 = _fix_amps(p.description_extra_1)
        p.description_extra_2 = _fix_amps(p.description_extra_2)
        p.name = _fix_amps(p.name)
        return p


class CopyNameToAttrs(Operation[T]):
    async def __call__(self, p: T) -> T:
        for att in p.attributes:
            if att.name == "Nazwa":
                return p

        if isinstance(p, ProductWithName) and p.man_name and p.man_name.strip():
            p.add_attribute("Nazwa", p.man_name)
        else:
            p.add_attribute("Nazwa", p.name)
        return p


class ProducedBefore13122024(Operation[T]):
    async def __call__(self, p: T) -> T:
        try:
            for att in p.attributes:
                if att.name == "Wprowadzony przed 13.12.2024":
                    return p

            year: Optional[int] = None
            for att in p.attributes:
                if att.name == "Rok wydania":
                    year = int(att.value)
                    break
            if year and year != 2024:
                p.add_attribute("Wprowadzony przed 13.12.2024", "Tak" if year < 2024 else "Nie")
            return p
        except Exception:
            pass
        finally:
            return p


class FindPiecesCount(Operation[T]):
    async def __call__(self, p: T) -> T:
        for att in p.attributes:
            if att.name == "Całkowita liczba elementów":
                return p

        match = re.search(r'(\d+)\s+elementów', p.name)

        if match:
            p.add_attribute("Całkowita liczba elementów", match.group(1))
            return p

        match = re.search(r'(\d+)\s+elem', p.name)

        if match:
            p.add_attribute("Całkowita liczba elementów", match.group(1))
            return p

        match = re.search(r'(\d+)\s+el\.', p.name)

        if match:
            p.add_attribute("Całkowita liczba elementów", match.group(1))

        return p


class CollectManufacturers(Operation[T]):
    manufacturers: dict[str, int] = dict()

    async def __call__(self, p: T) -> T:
        if p.manufacturer_name in self.manufacturers:
            self.manufacturers[p.manufacturer_name] += 1
        else:
            self.manufacturers[p.manufacturer_name] = 1
        return p

    def get_stats(self) -> dict[str, int]:
        return dict(self.manufacturers)


class AsyncPipelineBuilder(Generic[T]):
    """Composable async pipeline for transforming streamed products."""

    def __init__(self):
        self.steps: list[Callable[[T], Awaitable[T]]] = []

    def add(self, step: Operation[T] | Callable[[T], Awaitable[T]]):
        """Add an async step (Operation or plain async function)."""
        self.steps.append(step)
        return self

    async def run(self, items: AsyncIterator[T]) -> AsyncIterator[T]:
        """Run all steps sequentially for each product."""
        async for p in items:
            for step in self.steps:
                p = await step(p)
            yield p
