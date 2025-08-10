from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import os
from dotenv import load_dotenv
import uvicorn

# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model and tokenizer will be loaded at startup
model = None
tokenizer = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: str = "tinyllama-finetuned"

@app.on_event("startup")
async def load_model():
    global model, tokenizer
    try:
        model_path = os.getenv("MODEL_PATH", "./models/tinyllama-finetuned")
        base_model = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        
        print("🚀 Starting RohanAI API...")
        print(f"📍 Model path: {model_path}")
        
        print("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(base_model)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        print("Loading base model...")
        model = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype=torch.float32,  # Use float32 for better compatibility
            device_map="cpu",  # Use CPU for stable deployment
            trust_remote_code=True
        )
        
        # Try to load fine-tuned weights if available
        if os.path.exists(model_path):
            print("Loading fine-tuned PEFT adapter...")
            model = PeftModel.from_pretrained(model, model_path)
            model = model.merge_and_unload()
            print("✅ Fine-tuned model loaded successfully!")
        else:
            print(f"⚠️  Fine-tuned model not found at {model_path}, using base model")
        
        model.eval()
        print("✅ RohanAI API is ready!")
        
    except Exception as e:
        print(f"❌ Error loading model: {str(e)}")
        print("⚠️  API will use fallback responses")
        model = None
        tokenizer = None

@app.get("/")
async def health_check():
    return {"status": "ok", "message": "API is running"}

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Format messages for the chat template
        chat_messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Tokenize input
        inputs = tokenizer.apply_chat_template(
            chat_messages,
            return_tensors="pt"
        ).to(model.device)
        
        # Generate response
        with torch.no_grad():
            outputs = model.generate(
                inputs,
                max_new_tokens=150,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Decode and clean up the response
        response = tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
        
        return {
            "response": response,
            "model": request.model
        }
        
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)