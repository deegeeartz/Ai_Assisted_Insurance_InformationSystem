from app.schemas.underwrite import CoverageBlock

AVAILABLE_PRODUCTS = [
    # ─── Heirs Life Assurance ──────────────────────────────
    CoverageBlock(
        id="life_basic",
        name="Life Protection",
        description="Lump sum payout to your beneficiaries.",
        base_price=5000.0,
        icon="Heart",
        insurer_name="Heirs Life Assurance",
        category="life"
    ),
    CoverageBlock(
        id="critical_illness",
        name="Critical Illness",
        description="Coverage for cancer, stroke, and heart attack.",
        base_price=3000.0,
        icon="Activity",
        insurer_name="Heirs Life Assurance",
        category="life"
    ),
    CoverageBlock(
        id="funeral_cover",
        name="Funeral Expenses",
        description="Immediate cash for funeral costs.",
        base_price=1000.0,
        icon="Umbrella",
        insurer_name="Heirs Life Assurance",
        category="life"
    ),
    # ─── Heirs General Insurance ───────────────────────────
    CoverageBlock(
        id="auto_comprehensive",
        name="Auto Comprehensive",
        description="Full vehicle coverage including theft, fire & third-party.",
        base_price=8000.0,
        icon="Car",
        insurer_name="Heirs General Insurance",
        category="auto"
    ),
    CoverageBlock(
        id="auto_third_party",
        name="Auto Third-Party",
        description="Mandatory third-party liability for all vehicles.",
        base_price=3500.0,
        icon="Shield",
        insurer_name="Heirs General Insurance",
        category="auto"
    ),
    CoverageBlock(
        id="home_protection",
        name="Home Protection",
        description="Fire, flood, and burglary cover for your property.",
        base_price=4500.0,
        icon="Home",
        insurer_name="Heirs General Insurance",
        category="home"
    ),
    # ─── Heirs Gadget Insurance ────────────────────────────
    CoverageBlock(
        id="gadget_shield",
        name="Gadget Shield",
        description="Comprehensive device cover: theft, damage & liquid spills.",
        base_price=2500.0,
        icon="Smartphone",
        insurer_name="Heirs Gadget Insurance",
        category="gadget"
    ),
    CoverageBlock(
        id="screen_protect",
        name="Screen Protect",
        description="Accidental screen crack and display replacement.",
        base_price=1200.0,
        icon="Monitor",
        insurer_name="Heirs Gadget Insurance",
        category="gadget"
    ),
    CoverageBlock(
        id="extended_warranty",
        name="Extended Warranty",
        description="Manufacturer warranty extension up to 3 additional years.",
        base_price=1800.0,
        icon="Clock",
        insurer_name="Heirs Gadget Insurance",
        category="gadget"
    ),
]
