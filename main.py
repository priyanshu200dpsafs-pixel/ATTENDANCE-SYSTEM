from apscheduler.schedulers.blocking import BlockingScheduler
from recognize import scan_and_mark, SCAN_INTERVAL_MINS
from datetime import datetime

scheduler = BlockingScheduler()

# Run immediately when class starts, then every N minutes
scheduler.add_job(
    scan_and_mark,
    'interval',
    minutes=SCAN_INTERVAL_MINS,
    next_run_time=datetime.now()   # run immediately on start
)

print(f"Attendance system running. Scanning every {SCAN_INTERVAL_MINS} minutes.")
print("Press Ctrl+C to stop.\n")

try:
    scheduler.start()
except KeyboardInterrupt:
    print("System stopped.")