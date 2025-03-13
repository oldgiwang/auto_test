import pandas as pd
import os

# 使用完整路径
test_cases_path = r"C:\Users\19461\Documents\visual_studio\auto_test\data\test_cases.xlsx"
print(f"测试用例文件路径: {test_cases_path}")
print(f"文件是否存在: {os.path.exists(test_cases_path)}")

# 尝试读取
df = pd.read_excel(test_cases_path)
print(df.columns)
print(df.head())