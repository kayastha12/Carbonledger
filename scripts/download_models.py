# Script to pre-download and cache Hugging Face models for CarbonLedger
import os
import sys

# Standard paths matching the application services configuration
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRETRAINED_DIR = os.path.join(ROOT, "models/pretrained")

MODELS_CONFIG = {
    "distilbert-base-uncased": {
        "type": "nlp_classifier",
        "repo": "distilbert-base-uncased",
        "cache_dir": os.path.join(PRETRAINED_DIR, "distilbert-base-uncased")
    },
    "layoutlmv3": {
        "type": "ocr_layout",
        "repo": "microsoft/layoutlmv3-base",
        "cache_dir": os.path.join(PRETRAINED_DIR, "layoutlmv3")
    },
    "table_transformer": {
        "type": "object_detection",
        "repo": "microsoft/table-transformer-detection",
        "cache_dir": os.path.join(PRETRAINED_DIR, "table_transformer")
    },
    "all-MiniLM-L6-v2": {
        "type": "sentence_transformer",
        "repo": "sentence-transformers/all-MiniLM-L6-v2",
        "cache_dir": os.path.join(PRETRAINED_DIR, "all-MiniLM-L6-v2")
    },
    "bge-small-en-v1.5": {
        "type": "sentence_transformer",
        "repo": "BAAI/bge-small-en-v1.5",
        "cache_dir": os.path.join(PRETRAINED_DIR, "bge-small-en-v1.5")
    },
    "qwen": {
        "type": "causal_llm",
        "repo": "Qwen/Qwen2.5-0.5B-Instruct",
        "cache_dir": os.path.join(PRETRAINED_DIR, "qwen2.5-0.5b-instruct")
    }
}

def download_all():
    print("=" * 60)
    print("CarbonLedger AI Pretrained Models Downloader")
    print("=" * 60)
    
    # Import inside function to verify dependencies are present
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoProcessor, AutoModel, AutoModelForObjectDetection, AutoModelForCausalLM
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        print(f"Error: Required libraries not found. Run 'pip install -r requirements.txt' first. Details: {e}")
        sys.exit(1)
        
    for name, config in MODELS_CONFIG.items():
        repo = config["repo"]
        cache = config["cache_dir"]
        model_type = config["type"]
        
        print(f"\n[+] Downloading {name} ({repo}) to cache dir: {cache}...")
        os.makedirs(cache, exist_ok=True)
        
        try:
            if model_type == "nlp_classifier":
                AutoTokenizer.from_pretrained(repo, cache_dir=cache)
                AutoModelForSequenceClassification.from_pretrained(repo, cache_dir=cache)
            elif model_type == "ocr_layout":
                AutoProcessor.from_pretrained(repo, apply_ocr=False, cache_dir=cache)
                AutoModel.from_pretrained(repo, cache_dir=cache)
            elif model_type == "object_detection":
                AutoProcessor.from_pretrained(repo, cache_dir=cache)
                AutoModelForObjectDetection.from_pretrained(repo, cache_dir=cache)
            elif model_type == "sentence_transformer":
                SentenceTransformer(repo, cache_folder=cache)
            elif model_type == "causal_llm":
                AutoTokenizer.from_pretrained(repo, cache_dir=cache)
                AutoModelForCausalLM.from_pretrained(repo, cache_dir=cache)
            print(f"[-] Successfully downloaded and cached {name}.")
        except Exception as e:
            print(f"[!] Error downloading {name}: {e}")
            
    print("\n" + "=" * 60)
    print("All pretrained models are successfully downloaded and cached.")
    print("=" * 60)

if __name__ == "__main__":
    download_all()
