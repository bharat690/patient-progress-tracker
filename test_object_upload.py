from pathlib import Path

from app.services.object_storage import upload_file


pdf_files = list(Path("uploads").glob("*.pdf"))

if not pdf_files:
    raise RuntimeError("No PDF files found in uploads/")

pdf_path = pdf_files[0]

object_key = f"test/{pdf_path.name}"

upload_file(
    file_path=str(pdf_path),
    object_key=object_key,
)

print("Upload successful")
print("Local file:", pdf_path)
print("Object key:", object_key)