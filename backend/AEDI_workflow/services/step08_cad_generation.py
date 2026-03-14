"""
Step 8: CAD Generation (Mock)
Placeholder for future CAD integration. Returns mock geometry metadata.
"""

from ..models.output import RankedCandidate


def mock_cad_generation(top_candidate: RankedCandidate) -> dict:
    """Generate mock CAD metadata for the top candidate.

    In production, this would call a CAD engine (e.g. OpenSCAD, FreeCAD API)
    to generate a 3D pack layout.

    Args:
        top_candidate: The #1 ranked candidate

    Returns:
        Dictionary with mock CAD metadata
    """
    cell = top_candidate.variant.base_candidate.cell
    s = top_candidate.variant.base_candidate.series_count
    p = top_candidate.variant.parallel_count

    # Estimate pack dimensions based on cell format
    if cell.format in ("cylindrical", "18650", "21700", "38120", "40152") and cell.width_diameter_mm and cell.height_mm:
        # Hexagonal packing with 2mm gaps
        gap = 2.0
        d = cell.width_diameter_mm + gap
        # Arrange P cells in a row, S layers stacked
        pack_width_mm = p * d + 10  # +10mm for enclosure walls
        pack_length_mm = s * d + 10
        pack_height_mm = cell.height_mm + 20  # +20mm for BMS + enclosure top/bottom
    else:
        # Generic estimate
        pack_width_mm = 300
        pack_length_mm = 400
        pack_height_mm = 150

    return {
        "status": "mock",
        "message": "CAD generation is mocked. Integrate with OpenSCAD/FreeCAD for production.",
        "cell_model": cell.cell_name,
        "configuration": f"{s}S{p}P",
        "total_cells": top_candidate.variant.total_cells,
        "estimated_dimensions_mm": {
            "width": round(pack_width_mm, 1),
            "length": round(pack_length_mm, 1),
            "height": round(pack_height_mm, 1),
        },
        "estimated_volume_l": round(
            pack_width_mm * pack_length_mm * pack_height_mm / 1e6, 2
        ),
        "packing_method": "hexagonal" if cell.format in ("cylindrical", "18650", "21700", "38120", "40152") else "rectangular",
    }
