class OnlineAnomalyDetector:
    def __init__(self, threshold):
        self.previous_value = None
        self.threshold = threshold
        self.anomalies = []

    def process(self, timestamp, current_value):
        # 首次处理时没有前一个值
        if self.previous_value is None:
            self.previous_value = current_value
            return

        # 检测电量消耗递减
        if current_value < self.previous_value:
            self.anomalies.append((timestamp, 'Consumption Decrease'))

        # 检测电量消耗差距过大
        if abs(current_value - self.previous_value) > self.threshold:
            self.anomalies.append((timestamp, 'Excessive Consumption Difference'))

        # 更新前一个值
        self.previous_value = current_value

    def get_anomalies(self):
        return self.anomalies

# 实例化检测器，假设阈值为10
detector = OnlineAnomalyDetector(threshold=10)

# 模拟接收实时数据点
import pandas as pd

# 示例数据流
data_stream = {
    'timestamp': pd.date_range(start='2024-08-30 00:00', periods=10, freq='15T'),
    'consumption': [100, 105, 110, 108, 115, 130, 125, 150, 160, 155]
}

# 实时处理数据
for i in range(len(data_stream['timestamp'])):
    timestamp = data_stream['timestamp'][i]
    consumption = data_stream['consumption'][i]
    detector.process(timestamp, consumption)

# 输出检测到的异常
print("Detected anomalies:")
for anomaly in detector.get_anomalies():
    print(f"Timestamp: {anomaly[0]}, Anomaly Type: {anomaly[1]}")
