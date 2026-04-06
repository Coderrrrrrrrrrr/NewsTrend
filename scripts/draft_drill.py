import sys
import os
sys.path.append(os.getcwd())
from src.engine.formatter import OmniFormatter

def generate_drill_drafts():
    formatter = OmniFormatter()
    ids = [109, 153]
    for mid in ids:
        print(f">>> [兵部] 为素材 ID {mid} 生成跨平台草稿...")
        draft = formatter.create_omni_draft(mid)
        if draft:
            print(f">>> [成功] ID {mid} 草稿已生成于 drafts 表。")

if __name__ == "__main__":
    generate_drill_drafts()
