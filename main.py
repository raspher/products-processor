import asyncio

from product_processor.pipeline import AsyncPipeline, CollectManufacturers
from product_processor.product import Product, ProductWithName
from product_processor.serialization import AsyncProductXMLReader, AsyncProductXMLWriter


async def main():
    reader = AsyncProductXMLReader("products.xml", ProductWithName)
    writer = AsyncProductXMLWriter("test.xml", Product)

    pipeline = AsyncPipeline[ProductWithName]()
    man_collector = CollectManufacturers()
    pipeline.add(man_collector)

    async for _ in writer.save_products(pipeline.run(reader.stream_products())):
        pass

    for man, count in sorted(man_collector.manufacturers.items(), key=lambda m: m[1], reverse=True):
        print(f"{man}: {count}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPipeline interrupted by user.")
