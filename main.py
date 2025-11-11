from product_processor.operations import Operations
from product_processor.product import Product, ProductWithName
from product_processor.serialization import ProductXMLReader, ProductXMLWriter

if __name__ == "__main__":
    reader = ProductXMLReader("products.xml", ProductWithName)
    writer = ProductXMLWriter("test.xml", Product)
    try:
        pipeline = reader.stream_products()
        pipeline = Operations.fix_amps(pipeline)
        pipeline = Operations.name_to_attrs(pipeline)
        writer.save_products(pipeline)
    except KeyboardInterrupt:
        print("\nParsing stopped by user")
