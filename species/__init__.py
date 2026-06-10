"""Species anatomy registry — maps database species names to anatomy modules."""

from typing import Optional

from species.base import SpeciesAnatomy, build_anatomy_prompt, build_anatomy_negative

# ── Terrestrial ──────────────────────────────────────────────────────
from species.tyrannosaurus_rex import ANATOMY as _tyrannosaurus_rex
from species.velociraptor     import ANATOMY as _velociraptor
from species.triceratops      import ANATOMY as _triceratops
from species.stegosaurus      import ANATOMY as _stegosaurus
from species.brachiosaurus    import ANATOMY as _brachiosaurus
from species.ankylosaurus     import ANATOMY as _ankylosaurus
from species.parasaurolophus  import ANATOMY as _parasaurolophus
from species.dilophosaurus    import ANATOMY as _dilophosaurus
from species.carnotaurus      import ANATOMY as _carnotaurus

# ── Marine ───────────────────────────────────────────────────────────
from species.mosasaurus       import ANATOMY as _mosasaurus
from species.elasmosaurus     import ANATOMY as _elasmosaurus
from species.ichthyosaurus    import ANATOMY as _ichthyosaurus
from species.liopleurodon     import ANATOMY as _liopleurodon
from species.kronosaurus      import ANATOMY as _kronosaurus
from species.spinosaurus      import ANATOMY as _spinosaurus
from species.megalodon        import ANATOMY as _megalodon
from species.cretoxyrhina     import ANATOMY as _cretoxyrhina
from species.helicoprion      import ANATOMY as _helicoprion
from species.dunkleosteus     import ANATOMY as _dunkleosteus
from species.xiphactinus      import ANATOMY as _xiphactinus
from species.leedsichthys     import ANATOMY as _leedsichthys
from species.archelon         import ANATOMY as _archelon
from species.ammonite         import ANATOMY as _ammonite

# ── Aerial ───────────────────────────────────────────────────────────
from species.pteranodon        import ANATOMY as _pteranodon
from species.quetzalcoatlus    import ANATOMY as _quetzalcoatlus
from species.rhamphorhynchus   import ANATOMY as _rhamphorhynchus
from species.dimorphodon       import ANATOMY as _dimorphodon

# ── Arthropod ────────────────────────────────────────────────────────
from species.meganeura         import ANATOMY as _meganeura
from species.arthropleura      import ANATOMY as _arthropleura
from species.jaekelopterus     import ANATOMY as _jaekelopterus
from species.pulmonoscorpius   import ANATOMY as _pulmonoscorpius
from species.megarachne        import ANATOMY as _megarachne
from species.anomalocaris      import ANATOMY as _anomalocaris
from species.eurypterus        import ANATOMY as _eurypterus
from species.megalograptus     import ANATOMY as _megalograptus

# ── Plant ────────────────────────────────────────────────────────────
from species.lepidodendron     import ANATOMY as _lepidodendron
from species.calamites         import ANATOMY as _calamites
from species.glossopteris      import ANATOMY as _glossopteris
from species.williamsonia      import ANATOMY as _williamsonia
from species.araucaria         import ANATOMY as _araucaria
from species.archaefructus     import ANATOMY as _archaefructus
from species.wattieza          import ANATOMY as _wattieza
from species.sigillaria        import ANATOMY as _sigillaria


# ── Registry ─────────────────────────────────────────────────────────
# Keys must match the `name` column in the species table (setup_db.py).

SPECIES_REGISTRY: dict[str, SpeciesAnatomy] = {
    # Terrestrial
    "Tyrannosaurus rex":   _tyrannosaurus_rex,
    "Velociraptor":        _velociraptor,
    "Triceratops":         _triceratops,
    "Stegosaurus":         _stegosaurus,
    "Brachiosaurus":       _brachiosaurus,
    "Ankylosaurus":        _ankylosaurus,
    "Parasaurolophus":     _parasaurolophus,
    "Dilophosaurus":       _dilophosaurus,
    "Carnotaurus sastrei": _carnotaurus,
    # Marine
    "Mosasaurus":          _mosasaurus,
    "Elasmosaurus":        _elasmosaurus,
    "Ichthyosaurus":       _ichthyosaurus,
    "Liopleurodon":        _liopleurodon,
    "Kronosaurus":         _kronosaurus,
    "Spinosaurus":         _spinosaurus,
    "Megalodon":           _megalodon,
    "Cretoxyrhina":        _cretoxyrhina,
    "Helicoprion":         _helicoprion,
    "Dunkleosteus":        _dunkleosteus,
    "Xiphactinus":         _xiphactinus,
    "Leedsichthys":        _leedsichthys,
    "Archelon":            _archelon,
    "Ammonite":            _ammonite,
    # Aerial
    "Pteranodon":          _pteranodon,
    "Quetzalcoatlus":      _quetzalcoatlus,
    "Rhamphorhynchus":     _rhamphorhynchus,
    "Dimorphodon":         _dimorphodon,
    # Arthropod
    "Meganeura":           _meganeura,
    "Arthropleura":        _arthropleura,
    "Jaekelopterus":       _jaekelopterus,
    "Pulmonoscorpius":     _pulmonoscorpius,
    "Megarachne":          _megarachne,
    "Anomalocaris":        _anomalocaris,
    "Eurypterus":          _eurypterus,
    "Megalograptus":       _megalograptus,
    # Plant
    "Lepidodendron":       _lepidodendron,
    "Calamites":           _calamites,
    "Glossopteris":        _glossopteris,
    "Williamsonia":        _williamsonia,
    "Araucaria":           _araucaria,
    "Archaefructus":       _archaefructus,
    "Wattieza":            _wattieza,
    "Sigillaria":          _sigillaria,
}


def get_anatomy(species_name: str) -> Optional[SpeciesAnatomy]:
    """Look up anatomy data for a species by its database name.

    Returns None if the species has no anatomy module (should not happen
    once all 42 are wired up).
    """
    return SPECIES_REGISTRY.get(species_name)
