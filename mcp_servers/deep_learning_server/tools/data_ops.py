from typing import Dict, Any, List, Optional, Union
import numpy as np
import pandas as pd
import structlog
from io import BytesIO
import base64

logger = structlog.get_logger()

def _response(status: str, data: Any = None, error: str = None) -> Dict[str, Any]:
    if error:
        return {"status": "error", "error": error}
    return {"status": status, "data": data}

def sequence_pad(sequences: List[List[int]], maxlen: int, padding: str = 'pre', truncating: str = 'pre', value: float = 0.0) -> Dict[str, Any]:
    """PADS sequences to same length. [DATA]"""
    try:
        from tensorflow.keras.preprocessing.sequence import pad_sequences
        padded = pad_sequences(sequences, maxlen=maxlen, padding=padding, truncating=truncating, value=value)
        return _response("success", padded.tolist())
    except Exception as e:
        return _response("error", error=str(e))

def text_tokenize(texts: List[str], num_words: int = 10000, oov_token: str = "<OOV>") -> Dict[str, Any]:
    """TOKENIZES text list. [DATA]"""
    try:
        from tensorflow.keras.preprocessing.text import Tokenizer
        tokenizer = Tokenizer(num_words=num_words, oov_token=oov_token)
        tokenizer.fit_on_texts(texts)
        sequences = tokenizer.texts_to_sequences(texts)
        return _response("success", {
            "sequences": sequences,
            "word_index": dict(list(tokenizer.word_index.items())[:100]) # Limit output
        })
    except Exception as e:
        return _response("error", error=str(e))

def image_load_from_url(url: str, target_size: List[int] = (224, 224)) -> Dict[str, Any]:
    """LOADS image from URL for DL. [DATA]"""
    try:
        import requests
        from tensorflow.keras.preprocessing.image import img_to_array, load_img
        from io import BytesIO
        
        response = requests.get(url)
        img = load_img(BytesIO(response.content), target_size=tuple(target_size))
        img_array = img_to_array(img)
        # Normalize to [0, 1]
        img_array /= 255.0
        return _response("success", {"shape": img_array.shape, "sample_stats": {
            "mean": float(np.mean(img_array)),
            "std": float(np.std(img_array))
        }})
    except Exception as e:
        return _response("error", error=str(e))

def labels_to_categorical(labels: List[int], num_classes: int = None) -> Dict[str, Any]:
    """CONVERTS labels to one-hot. [DATA]"""
    try:
        from tensorflow.keras.utils import to_categorical
        categorical = to_categorical(labels, num_classes=num_classes)
        return _response("success", categorical.tolist())
    except Exception as e:
        return _response("error", error=str(e))

def time_series_generator(data: List[float], lookback: int, delay: int, min_index: int = 0, max_index: int = None, shuffle: bool = False, batch_size: int = 128, step: int = 6) -> Dict[str, Any]:
    """GENERATES timeseries batches. [DATA]"""
    try:
        # returns metadata about the generator configuration
        # Actual generation would be too large to pass via JSON
        return _response("success", {
            "config": locals()
        })
    except Exception as e:
        return _response("error", error=str(e))

def split_train_val_test(data_url: str, target_col: str, train_ratio: float = 0.7, val_ratio: float = 0.15) -> Dict[str, Any]:
    """SPLITS dataset for DL training. [DATA]"""
    try:
        df = pd.read_csv(data_url)
        n = len(df)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))
        
        return _response("success", {
            "train_size": train_end,
            "val_size": val_end - train_end,
            "test_size": n - val_end
        })
    except Exception as e:
        return _response("error", error=str(e))

def generator_image_augmentation(rotation_range: int = 20, width_shift: float = 0.2, height_shift: float = 0.2, horizontal_flip: bool = True) -> Dict[str, Any]:
    """CONFIGURES ImageDataGenerator. [DATA]"""
    return _response("success", {
        "class_name": "ImageDataGenerator",
        "config": {
            "rotation_range": rotation_range,
            "width_shift_range": width_shift,
            "height_shift_range": height_shift,
            "horizontal_flip": horizontal_flip
        }
    })
