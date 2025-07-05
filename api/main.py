# Update your chat endpoint to use Ollama
@app.post("/api/chat")
async def chat(message: dict, request: Request):
    try:
        if not message or 'content' not in message or not message['content'].strip():
            raise HTTPException(status_code=400, detail="No content provided in the request")
        
        content = message['content']
        # Use one of your fine-tuned models, e.g., rohan-style-chunk40
        model_name = message.get('model', 'rohan-style-chunk40')
        
        # Ollama API endpoint
        OLLAMA_API_URL = "http://localhost:11434/api/generate"
        
        data = {
            "model": model_name,
            "prompt": content,
            "stream": True
        }
        
        async def generate():
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream('POST', OLLAMA_API_URL, json=data, timeout=60.0) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.strip():
                            chunk = json.loads(line)
                            if 'response' in chunk:
                                yield f"data: {json.dumps({'response': chunk['response']})}\n\n"
                            if chunk.get('done', False):
                                yield "data: [DONE]\n\n"
                                
        return StreamingResponse(generate(), media_type="text/event-stream")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))