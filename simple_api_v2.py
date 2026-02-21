from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.models.database import get_db, DataPoint
from app.schemas.schemas import DataPoint as DataPointSchema

app = FastAPI()


@app.get("/data-points/", response_model=List[DataPointSchema])
def read_data_points(
    metric_id: Optional[str] = Query(None, description="Filter by metric ID"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(DataPoint)

    if metric_id:
        query = query.filter(DataPoint.metric_id == metric_id)

    data_points = query.offset(skip).limit(limit).all()
    return data_points


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
