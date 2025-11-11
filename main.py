import asyncio

from product_processor.asyncpipeline import AsyncPipeline, FixAmpersands, CopyNameToAttrs
from product_processor.product import Product, ProductWithName
from product_processor.serialization import AsyncProductXMLReader, AsyncProductXMLWriter


async def main():
    reader = AsyncProductXMLReader("products.xml", ProductWithName)
    writer = AsyncProductXMLWriter("test.xml", Product)

    pipeline = AsyncPipeline[ProductWithName]()
    pipeline.add(FixAmpersands()).add(CopyNameToAttrs())

    async for product in pipeline.run(reader.stream_products()):
        await writer.save_products([product])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPipeline interrupted by user.")
