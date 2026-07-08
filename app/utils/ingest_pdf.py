from pathlib import Path
import uuid

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_tenant
from app.services.vectorstore import upsert_document


BASE_DIR = Path(__file__).resolve().parents[2]  # project root
DOCS_DIR = BASE_DIR / "docs"

def extract_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text


async def ingest_pdf(
    org_id: str,
    branch_id: str,
    pdf_path: str,
):
    tenant = get_tenant(org_id, branch_id)

    text = extract_text(pdf_path)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
    )

    chunks = splitter.split_text(text)

    for i, chunk in enumerate(chunks):
        await upsert_document(
            tenant=tenant,
            doc_id=str(uuid.uuid4()),
            text=chunk,
            source=Path(pdf_path).name,
        )

    print(f"Uploaded {len(chunks)} chunks.")
    
if __name__ == "__main__":
    import asyncio
    
    pdf = DOCS_DIR / "1015en_product_catalog.pdf"
    
    asyncio.run(
        ingest_pdf(
            org_id="org_2",
            branch_id="branch_a",
            pdf_path=pdf,
        )
    )