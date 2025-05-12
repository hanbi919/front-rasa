from tqdm import tqdm  # 导入进度条库
from check_agent import check_chatbot
import pandas as pd
import json
import time
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置日志文件路径
LOG_FILE = "error.log"


class Chatbot:
    def analyze(self, main_item):
        # 这里模拟API调用延迟
        time.sleep(0.5)

        # 模拟返回结果 - 实际使用时替换为真实的API调用
        # 示例返回结构保持与您提供的一致
        return {
            "分析结果": [{
                "一级事项名称": main_item,
                "不符合的泛化项": [
                    f"模拟泛化项1-{main_item}",
                    f"模拟泛化项2-{main_item}"
                ],
                "不符项解释": f"这是关于'{main_item}'的不符项解释示例",
                "整体建议": f"针对'{main_item}'的整体建议示例"
            }]
        }


def format_list_items(items):
    return "\n".join([f"{k}: {v}" for item in items for k, v in item.items()])


def process_excel(input_file, output_file):
    # 读取输入Excel文件
    df = pd.read_excel(input_file)
    df = df.iloc[799:899]  # 包含第100行，不包含第200行

    # 确保有一级事项名称列
    if '一级事项名称' not in df.columns:
        raise ValueError("输入文件中缺少'一级事项名称'列")

    # 初始化Chatbot
    bot = check_chatbot

    # 准备结果列表
    results = []

    # 遍历每一行
    for index, row in tqdm(df.iterrows(), total=len(df), desc="处理进度"):
        main_item = row['一级事项名称']

        # 调用Chatbot分析
        try:
            response = bot.chat(main_item)
            data = response['answer']  # 取第一个分析结果
            analysis = json.loads(data)
            # 添加到结果列表
            results.append({
                "一级事项名称": analysis['一级事项名称'],
                "不符合的泛化项": format_list_items(analysis['不符合的泛化项']),
                "整体建议": analysis['整体建议']
            })

            print(f"已处理: {main_item}")

        except Exception as e:
            error_msg = f"处理'{main_item}'时出错: {str(e)}\n"
            print(error_msg)
            # 将错误信息写入日志文件
            with open(LOG_FILE, "a", encoding="utf-8") as log_file:
                log_file.write(error_msg)
            continue

    # 转换为DataFrame
    result_df = pd.DataFrame(results)

    # 保存到Excel
    result_df.to_excel(output_file, index=False)
    print(f"分析结果已保存到: {output_file}")


# 使用示例
if __name__ == "__main__":
    input_excel = "tools/泛化.xlsx"  # 替换为您的输入文件路径
    output_excel = "analysis_results900.xlsx"  # 输出文件路径

    process_excel(input_excel, output_excel)
