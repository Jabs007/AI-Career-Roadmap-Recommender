import json
from kafka import KafkaProducer

# Load your scraped JSON file
with open('scraped_jobs.json', 'r', encoding='utf-8') as f:
    job_data = json.load(f)

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Send each job to the topic
topic_name = 'kuccps-jobs'
for job in job_data:
    print(f"Sending job: {job.get('Job_Title')}")
    producer.send(topic_name, value=job)

producer.flush()
print("✅ All jobs sent to Kafka topic.")
