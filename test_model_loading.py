import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def test_model_loading():
    print("Testing TinyLlama model loading...")
    
    # Configuration
    model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    
    # Detect device
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"\nUsing device: {device.upper()}")
    
    # Test tokenizer
    print("\nLoading tokenizer...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        print("✅ Tokenizer loaded successfully!")
    except Exception as e:
        print(f"❌ Error loading tokenizer: {str(e)}")
        return
    
    # Test model loading
    print("\nLoading model (this may take a minute)...")
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if device != "cpu" else torch.float32,
            device_map="auto",
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        print("✅ Model loaded successfully!")
        print(f"\nModel device: {next(model.parameters()).device}")
        print(f"Model dtype: {next(model.parameters()).dtype}")
        
        # Test a small inference
        print("\nTesting model with a small prompt...")
        prompt = "Hello, my name is"
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=20,
                do_sample=True,
                temperature=0.7
            )
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"\nPrompt: {prompt}")
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"❌ Error loading model: {str(e)}")
        return

if __name__ == "__main__":
    test_model_loading()
