"""
FastAPI service for AI models
Handles spam detection and place recognition
"""
from urllib import request
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import uvicorn
from sqlalchemy.orm import Session
from uuid import UUID
from registry import get_model
from database import get_db
from models import PlaceSummary, TextAnalysis, MediaAnalysis, AnalysisStatus

app = FastAPI(title="Team 8 AI Service", version="1.0.0")


class textRequest(BaseModel):
    post_id: int
    content: str


class textResponse(BaseModel):
    post_id : int
    classification: dict


class imageRequest(BaseModel):
    media_id: int
    file_path: str


class imageResponse(BaseModel):
    media_id: int
    tag: dict
    nsfw: dict

class summarizeRequest(BaseModel):
    post_id : int
    comments: list[str]

class summarizeResponse(BaseModel):
    resualt: dict

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ai-service"}


@app.post("/textClassify", response_model=textResponse)
async def detect_spam(request: textRequest, db: Session = Depends(get_db)):
    text_analysis = TextAnalysis(
        post_ref_id=request.post_id,
        status=AnalysisStatus.PROCESSING
    )
    db.add(text_analysis)
    db.commit()
    db.refresh(text_analysis)
    
    try:
        id = request.post_id
        content = request.content
        model = get_model("comment_classifier")
        classification = model.predict(content)
        
        max = -1
        class_ = None
        for key, value in classification.items():
            if max < value:
                max = value
                class_ = key
                
        text_analysis.tags = class_
        text_analysis.sentiment_score = max 

        text_analysis.status = AnalysisStatus.COMPLETED
        db.commit()
        return textResponse(post_id=id, classification=classification)

    except Exception as e:
        text_analysis.status = AnalysisStatus.FAILED
        text_analysis.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/imageClassify", response_model=imageResponse)
async def recognize_place(request: imageRequest, db: Session = Depends(get_db)):
    media_analysis = MediaAnalysis(
        media_ref_id=UUID(request.media_id),
        status=AnalysisStatus.PROCESSING
    )
    db.add(media_analysis)
    db.commit()
    db.refresh(media_analysis)
    
    try : 
        id = request.media_id
        file_path = request.file_path
        model = get_model("image_tagger")
        tag =  model.predict(file_path)
        model = get_model("nsfw_detector")
        nsfw_result = model.detect(file_path)
        nsfw_score = nsfw_result.get('nsfw')
        media_analysis.detected_location = tag.get('label')
        media_analysis.confidence_score_location = tag.get('confidence')
        media_analysis.is_safe_media = nsfw_score < 0.5
        media_analysis.confidence_score_nsfw = nsfw_score
        media_analysis.status = AnalysisStatus.COMPLETED
        db.commit()
        
        return imageResponse(media_id=id, tag=tag, nsfw=nsfw_result)
    except Exception as e:
        media_analysis.status = AnalysisStatus.FAILED
        media_analysis.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e)) 
        

@app.post("/summarizeComments", response_model=summarizeResponse)
async def summarize_comments(request: summarizeRequest, db: Session = Depends(get_db)):
    place_summary = db.query(PlaceSummary).filter(
        PlaceSummary.place_ref_id == request.post_id
    ).first()
    
    if not place_summary:
        place_summary = PlaceSummary(
            place_ref_id=request.post_id,
        )
        db.add(place_summary)
        db.commit()
        db.refresh(place_summary)
    
    try:
        model = get_model("comment_summarizer")
        summary = model.summarize(request.comments)
        place_summary.summary_text = str(summary)
        place_summary.is_active = True
        db.commit()
        return summarizeResponse(resualt=summary)
    

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
