from product_processor.pipeline import AsyncPipelineBuilder, FixAmpersands, CopyNameToAttrs, ProducedBefore13122024
from product_processor.product import ProductWithName, Product
from product_processor.serialization import AsyncProductXMLReader, AsyncProductXMLWriter


class Processor:
    PIPELINE_STEPS = {
        "ampersands": FixAmpersands,
        "name": CopyNameToAttrs,
        "before": ProducedBefore13122024,
    }

    def _build_pipeline(self, step_names):
        builder = AsyncPipelineBuilder[ProductWithName]()
        for step_name in step_names:
            cls = self.PIPELINE_STEPS.get(step_name)
            if cls is None:
                raise NotImplementedError(f"Unknown step: {step_name}")
            builder.add(cls())
        return builder

    async def async_detect(self, input_file, output_file, steps):
        builder = self._build_pipeline(steps)

        reader = AsyncProductXMLReader(input_file, ProductWithName)
        writer = AsyncProductXMLWriter(output_file, Product)

        async for _ in writer.save_products(builder.run(reader.stream_products())):
            pass
