"""Sample CadQuery script (the shape an LLM would generate).

Convention: assign the model to `result` (or call show_object(model)).
"""

import cadquery as cq

result = (
    cq.Workplane("XY")
    .box(40, 30, 10)
    .faces(">Z")
    .workplane()
    .hole(12)
    .edges("|Z")
    .fillet(3)
)
