from typing import Dict, Any, List, Optional
import structlog

logger = structlog.get_logger()

def _app_config(name: str, input_shape: List[int], include_top: bool, weights: str) -> Dict[str, Any]:
    return {
        "class_name": name,
        "config": {
            "input_shape": input_shape,
            "include_top": include_top,
            "weights": weights
        }
    }

def app_xception(input_shape: List[int] = (299, 299, 3), include_top: bool = False, weights: str = 'imagenet') -> Dict[str, Any]:
    """CONFIGURES Xception Model. [DATA]"""
    return _app_config("Xception", input_shape, include_top, weights)

def app_vgg16(input_shape: List[int] = (224, 224, 3), include_top: bool = False, weights: str = 'imagenet') -> Dict[str, Any]:
    """CONFIGURES VGG16 Model. [DATA]"""
    return _app_config("VGG16", input_shape, include_top, weights)

def app_vgg19(input_shape: List[int] = (224, 224, 3), include_top: bool = False, weights: str = 'imagenet') -> Dict[str, Any]:
    """CONFIGURES VGG19 Model. [DATA]"""
    return _app_config("VGG19", input_shape, include_top, weights)

def app_resnet50(input_shape: List[int] = (224, 224, 3), include_top: bool = False, weights: str = 'imagenet') -> Dict[str, Any]:
    """CONFIGURES ResNet50 Model. [DATA]"""
    return _app_config("ResNet50", input_shape, include_top, weights)

def app_inception_v3(input_shape: List[int] = (299, 299, 3), include_top: bool = False, weights: str = 'imagenet') -> Dict[str, Any]:
    """CONFIGURES InceptionV3 Model. [DATA]"""
    return _app_config("InceptionV3", input_shape, include_top, weights)

def app_inception_resnet_v2(input_shape: List[int] = (299, 299, 3), include_top: bool = False, weights: str = 'imagenet') -> Dict[str, Any]:
    """CONFIGURES InceptionResNetV2 Model. [DATA]"""
    return _app_config("InceptionResNetV2", input_shape, include_top, weights)

def app_mobilenet(input_shape: List[int] = (224, 224, 3), include_top: bool = False, weights: str = 'imagenet') -> Dict[str, Any]:
    """CONFIGURES MobileNet Model. [DATA]"""
    return _app_config("MobileNet", input_shape, include_top, weights)

def app_densenet121(input_shape: List[int] = (224, 224, 3), include_top: bool = False, weights: str = 'imagenet') -> Dict[str, Any]:
    """CONFIGURES DenseNet121 Model. [DATA]"""
    return _app_config("DenseNet121", input_shape, include_top, weights)

def app_nasnet_large(input_shape: List[int] = (331, 331, 3), include_top: bool = False, weights: str = 'imagenet') -> Dict[str, Any]:
    """CONFIGURES NASNetLarge Model. [DATA]"""
    return _app_config("NASNetLarge", input_shape, include_top, weights)

def app_efficientnet_b0(input_shape: List[int] = (224, 224, 3), include_top: bool = False, weights: str = 'imagenet') -> Dict[str, Any]:
    """CONFIGURES EfficientNetB0 Model. [DATA]"""
    return _app_config("EfficientNetB0", input_shape, include_top, weights)
