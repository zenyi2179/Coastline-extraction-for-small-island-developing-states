import shutil

def delete_folder(folder_path):
    try:
        # 删除文件夹
        shutil.rmtree(folder_path)
        print(f"文件夹 {folder_path} 已成功删除！")
    except FileNotFoundError:
        print(f"文件夹 {folder_path} 不存在！")
    except PermissionError:
        print(f"没有权限删除文件夹 {folder_path}，请检查文件夹的权限！")
    except Exception as e:
        print(f"删除文件夹时出错：{e}")

def read_txt_to_list(file_path: str) -> list[str]:
    """
    读取文本文件内容为列表
    :param file_path: 文本文件路径
    :return: 行内容组成的字符串列表
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file.readlines()]
    except Exception as e:
        print(f"[ERROR] 读取文件失败 {file_path}: {e}")
        return []

if __name__ == '__main__':
    # 全局环境设置
    year_list = [2000, 2010, 2015, 2020]
    # year_list = [2020]
    list_sids = read_txt_to_list(file_path=fr"SIDS_37.txt")
    # sids_cou_list = ['SGP']
    for sid in list_sids:
        for year in year_list:
            # 使用示例
            folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\{sid}\{year}"
            delete_folder(folder_path)