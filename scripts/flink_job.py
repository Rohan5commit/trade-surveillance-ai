"""
Example PyFlink job skeleton for streaming detection in production.
This file is intentionally standalone and can be adapted for a managed Flink cluster.
"""

from pyflink.common import Types
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import KafkaSource
from pyflink.datastream.formats.json import JsonRowDeserializationSchema
from pyflink.datastream.watermark_strategy import WatermarkStrategy


def build_job() -> None:
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(16)

    source = KafkaSource.builder() \
        .set_bootstrap_servers("kafka:9092") \
        .set_topics("order-stream") \
        .set_group_id("surveillance") \
        .set_value_only_deserializer(
            JsonRowDeserializationSchema.builder().type_info(
                Types.ROW_NAMED(
                    ["account_id", "symbol", "side", "quantity", "price", "event_type"],
                    [Types.STRING(), Types.STRING(), Types.STRING(), Types.FLOAT(), Types.FLOAT(), Types.STRING()],
                )
            ).build()
        ) \
        .build()

    stream = env.from_source(source, WatermarkStrategy.no_watermarks(), "kafka-source")

    # Placeholder detection transform
    alerts = stream.filter(lambda row: row[5] == "cancel" and row[3] > 10_000)

    alerts.print()
    env.execute("trade-surveillance-flink")


if __name__ == "__main__":
    build_job()
