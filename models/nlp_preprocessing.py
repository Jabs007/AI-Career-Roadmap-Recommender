import nltk
import re
import torch
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from transformers import DistilBertTokenizer, DistilBertModel

# Download required NLTK data
nltk.download('stopwords', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('wordnet', quiet=True)

# Global cache for BERT model and tokenizer
_MODEL_CACHE = {}

# Module-level cache for fallback vocabulary
_FALLBACK_VOCAB = None

def get_fallback_vector(text: str):
    """Keyword-based vectorizer as fallback when BERT fails"""
    global _FALLBACK_VOCAB
    
    if _FALLBACK_VOCAB is None:
        try:
            from .interest_vectorizer import department_keywords
            vocab = set()
            for keywords in department_keywords.values():
                for k in keywords:
                    # Avoid recursive preprocess_text if possible, but keywords are usually clean
                    processed_k = k.lower()
                    if processed_k:
                        vocab.update(processed_k.split())
            _FALLBACK_VOCAB = {word: i for i, word in enumerate(sorted(list(vocab)))}
        except Exception:
            _FALLBACK_VOCAB = {}

    # BERT (DistilBERT) hidden size is 768. 
    # We must return a vector of this size to avoid RuntimeError during similarity calculation
    # if some embeddings succeed with BERT and others use the fallback.
    target_dim = 768
    vec = torch.zeros(target_dim)
    
    words = preprocess_text(text).split()
    for w in words:
        if w in _FALLBACK_VOCAB:
            idx = _FALLBACK_VOCAB[w]
            if idx < target_dim:
                vec[idx] = 1.0
            
    # Normalize
    norm = torch.norm(vec)
    return vec / (norm + 1e-9) if norm > 0 else vec

@torch.no_grad()
def get_bert_embedding(text: str, model_name: str = 'distilbert-base-uncased'):
    """
    Get embedding for text. Defaults to keyword vectorizer if BERT fails.
    """
    try:
        # Try to load model/tokenizer only once
        if not hasattr(get_bert_embedding, "_cached_assets"):
            from transformers import AutoTokenizer, AutoModel
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModel.from_pretrained(model_name, low_cpu_mem_usage=False)
            model.eval()
            get_bert_embedding._cached_assets = (tokenizer, model)
        
        tokenizer, model = get_bert_embedding._cached_assets
        device = torch.device('cpu')
        
        inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=512)
        outputs = model(**inputs)
        embedding = outputs.last_hidden_state.mean(dim=1).squeeze()
        
        # Safety check: if result is still a meta tensor, trigger fallback
        if embedding.device.type == 'meta':
            return get_fallback_vector(text)
            
        return embedding
        
    except Exception as e:
        # If ANYTHING goes wrong (OSError, ImportError, etc), do not crash.
        return get_fallback_vector(text)

def preprocess_text(text: str) -> str:
    """
    Preprocess student input text for NLP analysis.

    Steps:
    - Lowercase
    - Remove punctuation and numbers
    - Tokenize
    - Remove stopwords
    - Lemmatize

    Args:
        text (str): Raw student input

    Returns:
        str: Preprocessed text
    """
    if not text:
        return ""

    # Lowercase
    text = text.lower()

    # Remove punctuation and numbers
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)

    # Tokenize
    tokens = word_tokenize(text)

    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]

    # Lemmatize
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]

    # Join back to string
    return ' '.join(tokens)