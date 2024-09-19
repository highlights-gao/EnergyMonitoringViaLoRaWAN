import pandas as pd

"""
Assuming that the maximum domestic power is XkW, the meter reports data every Y minutes
Then threshold = X*Y/60 kWh
"""
class OnlineAnomalyDetector:
    def __init__(self, threshold):
        self.previous_value = None
        self.threshold = threshold
        self.anomalies = []

    def process(self, timestamp, current_value):
        
        if self.previous_value is None:
            self.previous_value = current_value
            return

        # Detecting decreasing power consumption
        if current_value < self.previous_value:
            self.anomalies.append((timestamp, 'Consumption Decrease'))

        # Detection of excessive power consumption gap
        if abs(current_value - self.previous_value) > self.threshold:
            self.anomalies.append((timestamp, 'Excessive Consumption Difference'))

        # Update the previous value
        self.previous_value = current_value

    def get_anomalies(self):
        return self.anomalies

"""
simple test
"""
# data stream example, only consumption is considered.
data_stream = {
    'timestamp': pd.date_range(start='2024-08-30 00:00', periods=10, freq='15T'),
    'consumption': [100, 105, 110, 108, 115, 130, 125, 150, 160, 155]
}

# Instantiate the detector, assuming a threshold of 10
#i.e. maximum consumption should not exceed 10kWh every fifteen minutes.
detector = OnlineAnomalyDetector(threshold=10)


# processing the data on line
for i in range(len(data_stream['timestamp'])):
    timestamp = data_stream['timestamp'][i]
    consumption = data_stream['consumption'][i]
    detector.process(timestamp, consumption)

# get detected anomalies
print("Detected anomalies:")
for anomaly in detector.get_anomalies():
    print(f"Timestamp: {anomaly[0]}, Anomaly Type: {anomaly[1]}")
