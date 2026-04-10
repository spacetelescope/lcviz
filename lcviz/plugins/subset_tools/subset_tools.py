from jdaviz.configs.default.plugins import SubsetTools

__all__ = []

# Enable the freeze button and set lcviz-specific docs link without subclassing SubsetTools.
# These class-level mutations take effect for all instances created after this import.
SubsetTools._default_can_freeze = True
SubsetTools._docs_link_fmt = (
    'https://lcviz.readthedocs.io/en/{vdocs}/plugins.html#subset-tools'
)
