
# Initialize Meta-Learner on core import
try:
    from kernel.agents.meta_learner import MetaLearner
    _meta = MetaLearner.get_instance()
except ImportError:
    pass
