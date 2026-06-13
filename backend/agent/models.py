"""Structured data models for the analysis stage (pydantic).

`Analysis` is what Gemini produces when it reasons about the drawing BEFORE
writing code; its `dimensions` table is also the ground truth the dimension gate
checks the measured B-rep against.
"""

from typing import Literal

from pydantic import BaseModel, Field

# `kind` tells the dimension gate how to match a callout to a measurement.
# bbox_* are overall sizes along the Z-up axes; the rest are feature dimensions.
DimensionKind = Literal[
    "bbox_x",  # overall width  (X, left-right in the front view)
    "bbox_y",  # overall depth  (Y, front-back)
    "bbox_z",  # overall height (Z, up)
    "hole_diameter",
    "hole_count",
    "spacing",  # distance between features (not yet auto-measured)
    "thickness",  # wall/plate thickness (not yet auto-measured)
    "other",
]


class Dimension(BaseModel):
    label: str = Field(description="Human-readable name, e.g. 'overall length'.")
    value: float = Field(description="Nominal value in millimetres.")
    tolerance: float = Field(
        description="Plus/minus tolerance in mm; use 0.5 if the drawing shows none."
    )
    kind: DimensionKind = Field(
        description="What the dimension constrains, for automatic checking."
    )


class Analysis(BaseModel):
    summary: str = Field(description="One-paragraph description of the whole part.")
    guess: str = Field(description="What the part most likely is and its function.")
    per_view: list[str] = Field(description="A detailed description of each view in the drawing.")
    dimensions: list[Dimension] = Field(description="Every dimension callout shown in the drawing.")
