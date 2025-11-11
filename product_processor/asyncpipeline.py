from typing import TypeVar, Generic, AsyncIterator, Callable, Awaitable

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
        if isinstance(p, ProductWithName) and p.man_name and p.man_name.strip():
            p.add_attribute("Nazwa", p.man_name)
        else:
            p.add_attribute("Nazwa", p.name)
        return p


class AsyncPipeline(Generic[T]):
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
