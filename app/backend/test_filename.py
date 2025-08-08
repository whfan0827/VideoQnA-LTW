import re
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename

# Test function
def test_filename_processing(original_filename):
    file_extension = Path(original_filename).suffix.lower()
    if re.search(r'[\u4e00-\u9fff]', original_filename):
        safe_filename = f'{uuid.uuid4().hex[:12]}{file_extension}'
        print(f'Chinese: "{original_filename}" -> "{safe_filename}"')
    else:
        safe_filename = secure_filename(original_filename)
        print(f'English: "{original_filename}" -> "{safe_filename}"')

# Test cases
print("Testing filename processing:")
test_filename_processing('中文影片.mp4')
test_filename_processing('我的影片檔案.avi')
test_filename_processing('English Video.mp4')
test_filename_processing('I-INV-001 Instruction.mp4')
test_filename_processing('mixed中英文.mp4')
