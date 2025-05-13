import pandas as pd


def find_differences(file1, file2, field1, field2, output_file):
    """
    比较两个Excel文件中的字段差异
    
    参数:
        file1: 第一个Excel文件路径
        file2: 第二个Excel文件路径
        field1: 第一个文件中要比较的字段名
        field2: 第二个文件中要比较的字段名
        output_file: 结果输出文件路径
    """
    # 读取两个Excel文件
    df1 = pd.read_excel(file1)
    df2 = pd.read_excel(file2)

    # 获取两个字段的唯一值集合
    set1 = set(df1[field1].unique())
    set2 = set(df2[field2].unique())

    # 找出在第一个文件中但不在第二个文件中的值
    differences = list(set1 - set2)

    # 将结果写入新文件
    result_df = pd.DataFrame({f"在{field1}中但不在{field2}中的值": differences})
    result_df.to_excel(output_file, index=False)

    print(f"比较完成，结果已保存到: {output_file}")
    print(f"共找到 {len(differences)} 条差异数据")


# 使用示例
if __name__ == "__main__":
    # 替换为你的实际文件路径和字段名
    file1_path = "tools/泛化.xlsx"
    file2_path = "tools/excel_main0425.xlsx"
    field1_name = "一级事项名称"  # 第一个文件中的字段名
    field2_name = "主项名称"  # 第二个文件中的字段名
    output_path = "差异结果.xlsx"

    find_differences(file1_path, file2_path, field1_name,
                     field2_name, output_path)
