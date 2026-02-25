"""
Production-oriented PyFlink pipeline template:
- Event-time watermarks
- Checkpointing for fault tolerance
- Keyed stateful detection example
- Kafka source + sink placeholders
"""

from __future__ import annotations

from datetime import timedelta

from pyflink.common import Configuration, Duration, Time, Types
from pyflink.common.restart_strategy import RestartStrategies
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.checkpointing_mode import CheckpointingMode
from pyflink.datastream.connectors.kafka import KafkaRecordSerializationSchema, KafkaSink, KafkaSource
from pyflink.datastream.formats.json import JsonRowDeserializationSchema, JsonRowSerializationSchema
from pyflink.datastream.functions import KeyedProcessFunction, RuntimeContext
from pyflink.datastream.state import ValueStateDescriptor
from pyflink.datastream.watermark_strategy import TimestampAssigner, WatermarkStrategy


class TsAssigner(TimestampAssigner):
    def extract_timestamp(self, value, record_timestamp) -> int:
        # Expect `ts_epoch_ms` in the row payload
        return int(value[6])


class SpoofingKeyedProcess(KeyedProcessFunction):
    """Minimal stateful CEP-style detector for large-order quick-cancel behavior."""

    def open(self, runtime_context: RuntimeContext):
        self.large_order_ts = runtime_context.get_state(ValueStateDescriptor("large_order_ts", Types.LONG()))

    def process_element(self, value, ctx: "KeyedProcessFunction.Context"):
        account_id, symbol, side, qty, price, event_type, ts_ms = value

        if event_type == "new_order" and qty >= 10_000:
            self.large_order_ts.update(ts_ms)

        if event_type == "cancel":
            prior = self.large_order_ts.value()
            if prior is not None and ts_ms - prior <= int(timedelta(seconds=10).total_seconds() * 1000):
                # Emit alert row: (account, symbol, pattern, score, ts_ms)
                yield (account_id, symbol, "spoofing", 0.9, ts_ms)


def build_job() -> None:
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(16)

    env.enable_checkpointing(30_000, CheckpointingMode.EXACTLY_ONCE)
    cp = env.get_checkpoint_config()
    cp.set_min_pause_between_checkpoints(10_000)
    cp.set_checkpoint_timeout(120_000)
    cp.set_tolerable_checkpoint_failure_number(3)
    cp.enable_externalized_checkpoints(True)

    env.set_restart_strategy(RestartStrategies.fixed_delay_restart(3, 10_000))

    cfg = Configuration()
    cfg.set_string("pipeline.name", "trade-surveillance-flink")
    cfg.set_string("execution.checkpointing.incremental", "true")

    source = (
        KafkaSource.builder()
        .set_bootstrap_servers("kafka:9092")
        .set_topics("order-stream")
        .set_group_id("surveillance")
        .set_value_only_deserializer(
            JsonRowDeserializationSchema.builder()
            .type_info(
                Types.ROW_NAMED(
                    ["account_id", "symbol", "side", "quantity", "price", "event_type", "ts_epoch_ms"],
                    [
                        Types.STRING(),
                        Types.STRING(),
                        Types.STRING(),
                        Types.FLOAT(),
                        Types.FLOAT(),
                        Types.STRING(),
                        Types.LONG(),
                    ],
                )
            )
            .build()
        )
        .build()
    )

    watermark = WatermarkStrategy.for_bounded_out_of_orderness(Duration.of_seconds(2)).with_timestamp_assigner(TsAssigner())

    stream = env.from_source(source, watermark, "order-source")

    alerts = (
        stream.key_by(lambda row: row[0], key_type=Types.STRING())
        .process(
            SpoofingKeyedProcess(),
            output_type=Types.ROW_NAMED(
                ["account_id", "symbol", "pattern", "score", "ts_epoch_ms"],
                [Types.STRING(), Types.STRING(), Types.STRING(), Types.FLOAT(), Types.LONG()],
            ),
        )
    )

    sink = (
        KafkaSink.builder()
        .set_bootstrap_servers("kafka:9092")
        .set_record_serializer(
            KafkaRecordSerializationSchema.builder()
            .set_topic("alert-stream")
            .set_value_serialization_schema(
                JsonRowSerializationSchema.builder()
                .with_type_info(
                    Types.ROW_NAMED(
                        ["account_id", "symbol", "pattern", "score", "ts_epoch_ms"],
                        [Types.STRING(), Types.STRING(), Types.STRING(), Types.FLOAT(), Types.LONG()],
                    )
                )
                .build()
            )
            .build()
        )
        .build()
    )

    alerts.sink_to(sink)
    env.execute("trade-surveillance-flink")


if __name__ == "__main__":
    build_job()
