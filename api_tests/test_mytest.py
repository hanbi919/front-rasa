import pytest
import openpyxl
import time
from datetime import datetime

import os
import sys
from pathlib import Path
# 将项目根目录添加到Python路径
root_dir = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(root_dir))
from tools.main_agent import main_item_chatbot


def load_test_data(file_path):
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook.active

    test_data = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if row[0] and row[1]:
            primary_item = row[0]
            generalizations = row[1].split(
                '\n') if isinstance(row[1], str) else []
            for query in generalizations:
                if query.strip():
                    test_data.append((primary_item, query.strip()))

    return test_data


class TestChatBotGeneralization:
    @classmethod
    def setup_class(cls):
        cls.api_key = "d091308a8cgtr0h4npng"
        cls.chat_bot = main_item_chatbot
        cls.test_data = load_test_data("api_tests/data/test.xlsx")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cls.report_file = f"test_report_{timestamp}.txt"
        with open(cls.report_file, "w", encoding="utf-8") as f:
            f.write("API泛化测试报告 - 详细版\n")
            f.write(f"测试开始时间: {datetime.now()}\n")
            f.write("="*80 + "\n\n")

    @pytest.mark.parametrize("expected_primary_item,query", load_test_data("api_tests/data/test.xlsx"))
    def test_generalization(self, expected_primary_item, query):
        start_time = time.time()
        response = None
        try:
            response = self.chat_bot.chat(query)
            answer = response["answer"]
            duration = response["duration"]

            assert expected_primary_item in answer, (
                f"响应中未找到预期内容: '{expected_primary_item}'"
            )

            result = "PASS"
            details = f"响应验证成功"

        except Exception as e:
            result = "FAIL"
            details = str(e)
            duration = "{:.2f}".format(time.time() - start_time)
            raise

        finally:
            with open(self.report_file, "a", encoding="utf-8") as f:
                f.write(f"测试查询: '{query}'\n")
                f.write(f"预期结果: '{expected_primary_item}'\n")
                f.write(f"测试状态: {result}\n")
                # 记录完整响应
                f.write(
                    f"实际响应: '{response['answer'] if response else '无响应'}\n")
                f.write(f"响应耗时: {duration}秒\n")
                f.write(f"详细信息: {details}\n")
                f.write("-"*80 + "\n")

    @classmethod
    def teardown_class(cls):
        # 统计测试结果
        with open(cls.report_file, "r", encoding="utf-8") as f:
            content = f.read()

        pass_count = content.count("测试状态: PASS")
        fail_count = content.count("测试状态: FAIL")

        with open(cls.report_file, "a", encoding="utf-8") as f:
            f.write("\n测试结果统计:\n")
            f.write(f"总测试用例: {pass_count + fail_count}\n")
            f.write(f"通过用例: {pass_count}\n")
            f.write(f"失败用例: {fail_count}\n")
            f.write(
                f"通过率: {(pass_count/(pass_count + fail_count))*100:.2f}%\n")
            f.write("\n测试结束时间: {}\n".format(datetime.now()))
            f.write("="*80 + "\n")

        print(f"详细测试报告已生成: {cls.report_file}")


if __name__ == "__main__":
    pytest.main(["-v", __file__])
