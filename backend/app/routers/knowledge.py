from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_active_user
from app.db import get_db
from app.knowledge.parser import ParserError
from app.knowledge.service import (
    FileTooLargeError,
    UnsupportedFileTypeError,
    delete_document,
    replace_document,
    upload_document,
)
from app.models import KnowledgeDocument, User
from app.schemas import DocumentOut

router = APIRouter()


def _get_document_or_404(db: Session, document_id: int) -> KnowledgeDocument:
    document = db.get(KnowledgeDocument, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.post("/documents/upload", response_model=DocumentOut, status_code=201)
async def upload(
    file: UploadFile = File(...),
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db),
) -> DocumentOut:
    try:
        document = await upload_document(db, file)
    except (UnsupportedFileTypeError, FileTooLargeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return document


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> list[DocumentOut]:
    stmt = select(KnowledgeDocument).order_by(KnowledgeDocument.uploaded_at.desc())
    return list(db.execute(stmt).scalars().all())


@router.get("/documents/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> DocumentOut:
    return _get_document_or_404(db, document_id)


@router.put("/documents/{document_id}", response_model=DocumentOut)
async def replace(
    document_id: int,
    file: UploadFile = File(...),
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db),
) -> DocumentOut:
    document = _get_document_or_404(db, document_id)
    try:
        return await replace_document(db, document, file)
    except (UnsupportedFileTypeError, FileTooLargeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ParserError as exc:
        raise HTTPException(status_code=502, detail=f"Failed to parse replacement file: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to replace document: {exc}") from exc


@router.delete("/documents/{document_id}", status_code=204)
def delete(
    document_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> None:
    document = _get_document_or_404(db, document_id)
    delete_document(db, document)
