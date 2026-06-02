from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.deps import get_db
from app.models.user import AlertChannel, User
from app.schemas.api import AlertChannelIn, AlertChannelOut

router = APIRouter()


@router.get("", response_model=list[AlertChannelOut])
def list_channels(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[AlertChannelOut]:
    channels = db.execute(select(AlertChannel).where(AlertChannel.user_id == user.id)).scalars().all()
    return [AlertChannelOut.model_validate(item) for item in channels]


@router.post("", response_model=AlertChannelOut)
def create_channel(
    payload: AlertChannelIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AlertChannelOut:
    channel = AlertChannel(user_id=user.id, **payload.model_dump())
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return AlertChannelOut.model_validate(channel)


@router.put("/{channel_id}", response_model=AlertChannelOut)
def update_channel(
    channel_id: int,
    payload: AlertChannelIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AlertChannelOut:
    channel = db.get(AlertChannel, channel_id)
    if not channel or channel.user_id != user.id:
        raise HTTPException(status_code=404, detail="not_found")
    for key, value in payload.model_dump().items():
        setattr(channel, key, value)
    db.commit()
    db.refresh(channel)
    return AlertChannelOut.model_validate(channel)


@router.delete("/{channel_id}")
def delete_channel(
    channel_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, bool]:
    channel = db.get(AlertChannel, channel_id)
    if not channel or channel.user_id != user.id:
        raise HTTPException(status_code=404, detail="not_found")
    db.delete(channel)
    db.commit()
    return {"ok": True}
