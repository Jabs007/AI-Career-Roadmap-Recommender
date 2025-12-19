from kafka import KafkaConsumer
import json

# Create Kafka consumer
consumer = KafkaConsumer(
    'kuccps-jobs',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: m.decode('utf-8'),
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='job-consumer',
    consumer_timeout_ms=5000  # <-- Will stop if no messages after 5 seconds
)

print("📥 Listening to messages...")

# Consume messages
for msg in consumer:
    if not msg.value.strip():
        print("⚠️  Skipped empty message.")
        continue
    try:
        job = json.loads(msg.value)
        print(f"📨 Received: {job.get('Job_Title', 'Unknown Title')}")
    except json.JSONDecodeError:
        print(f"⚠️  Skipped invalid JSON message: {msg.value}")

consumer.close()
print("✅ Done consuming messages.")
