import spacy
import structlog
from typing import Dict, List, Any, Optional

logger = structlog.get_logger()

# Global cache to avoid reloading heavy models
LOADED_MODELS: Dict[str, spacy.language.Language] = {}

import contextlib
import io

def get_nlp(model_name: str = "en_core_web_sm") -> spacy.language.Language:
    """Get or load a spacy model."""
    if model_name not in LOADED_MODELS:
        try:
            # First attempt to load
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                LOADED_MODELS[model_name] = spacy.load(model_name)
        except OSError:
            # Attempt download
            try:
                import subprocess
                import sys
                
                # 1. Try to determine the best installer (uv or pip)
                installer_cmd = None
                
                # Check for uv
                try:
                    subprocess.run(["uv", "--version"], capture_output=True, check=True)
                    installer_cmd = ["uv", "pip", "install"]
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # Check for pip
                    try:
                        subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, check=True)
                        installer_cmd = [sys.executable, "-m", "pip", "install"]
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        pass

                if installer_cmd:
                    logger.info("downloading_spacy_model", model=model_name, tool=installer_cmd[0])
                    
                    if installer_cmd[0] == "uv":
                        # For uv, we try to install the PyPI package version.
                        # Naming convention: usually en-core-web-sm (dashes)
                        pypi_names = [
                            model_name.replace("_", "-"),  # en-core-web-sm
                            model_name                      # en_core_web_sm
                        ]
                        
                        success = False
                        for name in pypi_names:
                            try:
                                subprocess.run([*installer_cmd, name], check=True, capture_output=True)
                                success = True
                                break
                            except subprocess.CalledProcessError:
                                continue
                        
                        if not success:
                            raise OSError(f"Could not find a valid package for '{model_name}' on PyPI using 'uv'.")
                    else:
                        # Fallback to spacy's own downloader if pip is present
                        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                            spacy.cli.download(model_name)
                    
                    LOADED_MODELS[model_name] = spacy.load(model_name)
                else:
                    raise OSError(f"Neither 'uv' nor 'pip' are available to download '{model_name}'.")

            except Exception as e:
                logger.error("failed_to_download_model", model=model_name, error=str(e))
                raise OSError(f"Failed to download model '{model_name}': {str(e)}. "
                             "Please install it manually or ensure 'uv' or 'pip' is available.")
    return LOADED_MODELS[model_name]

def load_model(model_name: str = "en_core_web_sm") -> str:
    """Explicitly load a model into cache."""
    nlp = get_nlp(model_name)
    return f"Successfully loaded '{model_name}' (Pipelines: {nlp.pipe_names})"

def get_model_meta(model_name: str = "en_core_web_sm") -> Dict[str, Any]:
    """Get metadata about a loaded model."""
    nlp = get_nlp(model_name)
    return nlp.meta

def get_pipe_names(model_name: str = "en_core_web_sm") -> List[str]:
    """Get active pipeline components."""
    nlp = get_nlp(model_name)
    return nlp.pipe_names

def has_pipe(model_name: str, pipe_name: str) -> bool:
    """Check if model has specific pipe."""
    nlp = get_nlp(model_name)
    return nlp.has_pipe(pipe_name)

def remove_pipe(model_name: str, pipe_name: str) -> str:
    """Remove a pipe component."""
    nlp = get_nlp(model_name)
    if nlp.has_pipe(pipe_name):
        nlp.remove_pipe(pipe_name)
        return f"Removed '{pipe_name}'"
    return f"Pipe '{pipe_name}' not found."

def add_pipe(model_name: str, pipe_name: str, before: Optional[str] = None, after: Optional[str] = None) -> str:
    """Add a standard pipe component."""
    nlp = get_nlp(model_name)
    try:
        nlp.add_pipe(pipe_name, before=before, after=after)
        return f"Added '{pipe_name}'"
    except Exception as e:
        return f"Error adding pipe: {str(e)}"

def explain_term(term: str) -> str:
    """Get explanation for a Spacy label/tag."""
    return spacy.explain(term) or "No explanation found."
