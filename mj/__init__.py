"""prompt-crafter agent: Generate Midjourney prompts from species + parameters.

Public API:
  - PromptResult: Output dataclass
  - assemble_prompt(): Core prompt generation function
  - load_refs(): Load reference image library
  - get_refs_for_species(): Get refs for a species
"""

from mj.prompt_engine import PromptResult, assemble_prompt
from mj.refs import load_refs, get_refs_for_species

__all__ = [
    "PromptResult",
    "assemble_prompt",
    "load_refs",
    "get_refs_for_species",
]
