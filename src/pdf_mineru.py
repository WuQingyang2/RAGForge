import requests
import time
import zipfile
import os
from pathlib import Path

api_key = os.environ.get('MINERU_API_KEY')

def get_task_id(file_name):
    if not api_key:
        raise RuntimeError("请设置环境变量 MINERU_API_KEY")
    url='https://mineru.net/api/v4/extract/task'
    header = {
        'Content-Type':'application/json',
        "Authorization":f"Bearer {api_key}".format(api_key)
    }
    pdf_url = 'https://vl-image.oss-cn-shanghai.aliyuncs.com/pdf/' + file_name
    data = {
        'url':pdf_url,
        'is_ocr':True,
        'enable_formula': False,
    }

    res = requests.post(url, headers=header, json=data, timeout=60)
    res.raise_for_status()
    print(res.status_code)
    print(res.json())
    print(res.json()["data"])
    task_id = res.json()["data"]['task_id']
    return task_id

def get_result(task_id, output_dir=None):
    url = f'https://mineru.net/api/v4/extract/task/{task_id}'
    header = {
        'Content-Type':'application/json',
        "Authorization":f"Bearer {api_key}".format(api_key)
    }

    while True:
        res = requests.get(url, headers=header, timeout=60)
        res.raise_for_status()
        result = res.json()["data"]
        print(result)
        state = result.get('state')
        err_msg = result.get('err_msg', '')
        # 如果任务还在进行中，等待后重试
        if state in ['pending', 'running', 'converting']:
            print("任务未完成，等待5秒后重试...")
            time.sleep(5)
            continue
        # 如果有错误，输出错误信息
        if err_msg:
            raise RuntimeError(f"MinerU 任务失败: {err_msg}")
        # 如果任务完成，下载文件
        if state == 'done':
            full_zip_url = result.get('full_zip_url')
            if full_zip_url:
                result_root = Path(output_dir or ".")
                result_root.mkdir(parents=True, exist_ok=True)
                local_filename = result_root / f"{task_id}.zip"
                print(f"开始下载: {full_zip_url}")
                r = requests.get(full_zip_url, stream=True, timeout=120)
                r.raise_for_status()
                with open(local_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                print(f"下载完成，已保存到: {local_filename}")
                # 下载完成后自动解压
                return Path(unzip_file(local_filename))
            else:
                raise RuntimeError("MinerU 未返回 full_zip_url")
            return
        # 其他未知状态
        raise RuntimeError(f"MinerU 任务状态异常: {state}")

# 解压zip文件的函数
def unzip_file(zip_path, extract_dir=None):
    """
    解压指定的zip文件到目标文件夹。
    :param zip_path: zip文件路径
    :param extract_dir: 解压目标文件夹，默认为zip同名目录
    """
    if extract_dir is None:
        extract_dir = Path(zip_path).with_suffix('')
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        root = Path(extract_dir).resolve()
        for member in zip_ref.namelist():
            if not (root / member).resolve().is_relative_to(root):
                raise ValueError(f'ZIP 包含非法路径: {member}')
        zip_ref.extractall(extract_dir)
    print(f"已解压到: {extract_dir}")
    return extract_dir

if __name__ == "__main__":
    file_name = '【财报】中芯国际：中芯国际2024年年度报告.pdf'
    task_id = get_task_id(file_name)
    print('task_id:',task_id)
    get_result(task_id)
