from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.deps import get_db
from app.models.rbl import RBLList
from app.models.user import User
from app.schemas.api import RBLListIn, RBLListOut

router = APIRouter()


@router.get("", response_model=list[RBLListOut])
def list_lists(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[RBLListOut]:
    lists = db.execute(select(RBLList).order_by(RBLList.priority.asc(), RBLList.name.asc())).scalars().all()
    return [RBLListOut.model_validate(item) for item in lists]


@router.post("", response_model=RBLListOut)
def create_list(
    payload: RBLListIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> RBLListOut:
    exists = db.execute(select(RBLList).where(RBLList.name == payload.name)).scalars().first()
    if exists:
        raise HTTPException(status_code=409, detail="name_exists")
    rbl = RBLList(**payload.model_dump())
    db.add(rbl)
    db.commit()
    db.refresh(rbl)
    return RBLListOut.model_validate(rbl)


@router.put("/{list_id}", response_model=RBLListOut)
def update_list(
    list_id: int,
    payload: RBLListIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> RBLListOut:
    rbl = db.get(RBLList, list_id)
    if not rbl:
        raise HTTPException(status_code=404, detail="not_found")
    for key, value in payload.model_dump().items():
        setattr(rbl, key, value)
    db.commit()
    db.refresh(rbl)
    return RBLListOut.model_validate(rbl)


@router.delete("/{list_id}")
def delete_list(
    list_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict[str, bool]:
    rbl = db.get(RBLList, list_id)
    if not rbl:
        raise HTTPException(status_code=404, detail="not_found")
    db.delete(rbl)
    db.commit()
    return {"ok": True}
