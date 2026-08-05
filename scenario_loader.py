"""
scenario_loader.py - Trình nạp kịch bản Generic từ File Markdown (.md)

Nhiệm vụ:
- Sử dụng thư viện `python-frontmatter` để đọc và tách biệt giữa YAML Frontmatter (metadata cấu hình) 
  và Markdown Content (nội dung hướng dẫn chi tiết).
- Ánh xạ dữ liệu vào `ScenarioSchema` sử dụng Pydantic.
- Đảm bảo tính an toàn cao (Robustness & Fallback): Nhờ Pydantic `Field(default=...)`, hệ thống 
  sẽ tự động bù đắp dữ liệu thiếu mà KHÔNG BAO GIỜ bị crash ứng dụng.
"""

import os
import frontmatter
from models import ScenarioSchema


def load_scenario_from_md(file_path: str) -> ScenarioSchema:
    """
    Đọc file .md, phân tách YAML Frontmatter và Markdown Body, 
    trả về đối tượng ScenarioSchema đã qua kiểm duyệt Pydantic.

    Args:
        file_path (str): Đường dẫn tuyệt đối hoặc tương đối tới file kịch bản .md

    Returns:
        ScenarioSchema: Đối tượng kịch bản hoàn chỉnh với dữ liệu fallback an toàn.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy file kịch bản tại đường dẫn: {file_path}")

    # Đọc file markdown bằng python-frontmatter
    post = frontmatter.load(file_path)
    metadata = dict(post.metadata)

    # Đưa nội dung phần Markdown Body vào trường instructions
    instructions_text = post.content.strip() if post.content else ""
    metadata["instructions"] = instructions_text

    # Pydantic model_validate tự động xử lý ép kiểu và bù dữ liệu thiếu từ default values
    scenario = ScenarioSchema.model_validate(metadata)
    return scenario


def list_available_scenarios(scenarios_dir: str = "scenarios") -> dict[str, str]:
    """
    Quét thư mục kịch bản và trả về dictionary {Tên hiển thị: Đường dẫn file .md}.

    Args:
        scenarios_dir (str): Đường dẫn thư mục chứa các file kịch bản .md

    Returns:
        dict[str, str]: Bản đồ tên kịch bản -> đường dẫn file
    """
    if not os.path.exists(scenarios_dir):
        os.makedirs(scenarios_dir, exist_ok=True)
        return {}

    scenario_files = {}
    for filename in os.listdir(scenarios_dir):
        if filename.endswith(".md"):
            full_path = os.path.join(scenarios_dir, filename)
            try:
                sc = load_scenario_from_md(full_path)
                display_name = f"{sc.title} ({sc.role})"
                scenario_files[display_name] = full_path
            except Exception as e:
                # Nếu file hỏng nặng không đọc được YAML, lấy tên file làm fallback
                scenario_files[f"Lỗi: {filename}"] = full_path

    return scenario_files
