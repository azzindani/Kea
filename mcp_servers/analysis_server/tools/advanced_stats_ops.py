import pandas as pd
import structlog
from typing import Dict, List, Any, Optional

logger = structlog.get_logger()

# Assuming statsmodels is available as per previous update
try:
    import statsmodels.api as sm
    from statsmodels.formula.api import ols, logit, probit, glm, mixedlm
except ImportError:
    pass

def _run_sm(model_func, formula, file_path, **kwargs) -> Dict[str, Any]:
    try:
        df = pd.read_csv(file_path)
        model = model_func(formula, data=df, **kwargs).fit()
        return {
            "summary": str(model.summary2() if hasattr(model, 'summary2') else model.summary()),
            "params": model.params.to_dict(),
            "pvalues": model.pvalues.to_dict()
        }
    except Exception as e:
        return {"error": str(e)}

def stat_anova_oneway(file_path: str, formula: str) -> Dict[str, Any]:
    """RUNS One-Way ANOVA. [DATA]"""
    try:
        df = pd.read_csv(file_path)
        model = ols(formula, data=df).fit()
        anova_table = sm.stats.anova_lm(model, typ=2)
        return {"anova_table": anova_table.to_json()}
    except Exception as e:
        return {"error": str(e)}

def stat_logit(file_path: str, formula: str) -> Dict[str, Any]:
    """RUNS Logistic Regression (Logit). [DATA]"""
    return _run_sm(logit, formula, file_path)

def stat_probit(file_path: str, formula: str) -> Dict[str, Any]:
    """RUNS Probit Regression. [DATA]"""
    return _run_sm(probit, formula, file_path)

def stat_glm(file_path: str, formula: str, family: str = 'Gaussian') -> Dict[str, Any]:
    """RUNS Generalized Linear Model. [DATA]"""
    try:
        fam = getattr(sm.families, family)()
        return _run_sm(glm, formula, file_path, family=fam)
    except Exception as e:
        return {"error": str(e)}

def stat_mixedlm(file_path: str, formula: str, group_col: str) -> Dict[str, Any]:
    """RUNS Mixed Linear Model (LMM). [DATA]"""
    try:
        df = pd.read_csv(file_path)
        model = mixedlm(formula, df, groups=df[group_col]).fit()
        return {
            "summary": str(model.summary()),
            "params": model.params.to_dict()
        }
    except Exception as e:
        return {"error": str(e)}

def stat_tukey_hsd(file_path: str, endog: str, groups: str) -> Dict[str, Any]:
    """RUNS Tukey HSD Post-hoc. [DATA]"""
    try:
        from statsmodels.stats.multicomp import pairwise_tukeyhsd
        df = pd.read_csv(file_path)
        m_comp = pairwise_tukeyhsd(endog=df[endog], groups=df[groups], alpha=0.05)
        return {"summary": str(m_comp)}
    except Exception as e:
        return {"error": str(e)}
