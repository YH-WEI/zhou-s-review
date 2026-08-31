from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

from .common import RESULTS_DIR, load_yaml, read_csv


CODE_VALUE = {"": 0, "I": 1, "M": 2, "D": 3}
CODE_COLOUR = ["#FFFFFF", "#D9D9D9", "#E69F00", "#0072B2"]
SERVICE_LABELS = {
    "frequency_response_regulation": "Frequency\nresponse",
    "demand_response_peak_management": "Demand response\n& peak",
    "renewable_energy_integration": "Renewable\nintegration",
    "local_energy_sharing_distribution_support": "Local/distribution\nsupport",
    "resilience_emergency_operation": "Resilience &\nemergency",
    "other": "Other",
}


def render_fig4() -> tuple[Path, Path]:
    rows = read_csv(RESULTS_DIR / "tables" / "fig4_mechanism_service_matrix.csv")
    rules = load_yaml(Path(__file__).resolve().parents[1] / "config" / "schema_rules.yml")
    services = [value for value in rules["service_families"] if value != "other"]
    mechanisms = []
    for row in rows:
        key = (row["mechanism_id"], row["asset_class"], row["flexibility_mechanism"])
        if key not in mechanisms:
            mechanisms.append(key)
    mechanisms.sort()
    lookup = {(row["mechanism_id"], row["service_family"]): row for row in rows}
    values = np.zeros((len(mechanisms), len(services)), dtype=int)
    labels = [["" for _ in services] for _ in mechanisms]
    for row_index, (mechanism_id, _, _) in enumerate(mechanisms):
        for column_index, service in enumerate(services):
            row = lookup[(mechanism_id, service)]
            values[row_index, column_index] = CODE_VALUE[row["evidence_code"]]
            labels[row_index][column_index] = row["cell_label"]

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "svg.hashsalt": "zhou-review-evidence-map-fig4",
        }
    )
    height = max(3.8, 0.72 * len(mechanisms) + 2.2)
    fig, ax = plt.subplots(figsize=(11.5, height), constrained_layout=True)
    ax.imshow(values, cmap=ListedColormap(CODE_COLOUR), vmin=0, vmax=3, aspect="auto")
    ax.set_xticks(range(len(services)), [SERVICE_LABELS[value] for value in services])
    y_labels = [f"{asset}: {mechanism}" for _, asset, mechanism in mechanisms]
    ax.set_yticks(range(len(mechanisms)), y_labels)
    ax.tick_params(axis="x", top=True, labeltop=True, bottom=False, labelbottom=False, length=0, pad=8)
    ax.tick_params(axis="y", length=0, pad=8)
    ax.set_xticks(np.arange(-0.5, len(services), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(mechanisms), 1), minor=True)
    ax.grid(which="minor", color="#6F6F6F", linewidth=0.8)
    ax.tick_params(which="minor", bottom=False, left=False)
    for row_index in range(len(mechanisms)):
        for column_index in range(len(services)):
            label = labels[row_index][column_index]
            if label:
                colour = "white" if values[row_index, column_index] == 3 else "black"
                ax.text(column_index, row_index, label.replace(" ", "\n", 1), ha="center", va="center", color=colour, fontweight="bold", fontsize=8)
    ax.set_title("Mechanism-service evidence identified within the included corpus", loc="left", fontsize=14, fontweight="bold", pad=18)
    ax.set_xlabel("Blank = no eligible evidence identified under this bounded protocol (not technical impossibility)", labelpad=12)
    legend = [
        Patch(facecolor=CODE_COLOUR[3], edgecolor="#333333", label="D: demonstrated (E3-E5)"),
        Patch(facecolor=CODE_COLOUR[2], edgecolor="#333333", label="M: modelled/replayed (E1-E2)"),
        Patch(facecolor=CODE_COLOUR[1], edgecolor="#333333", label="I: inferred/proposed (E0)"),
        Patch(facecolor=CODE_COLOUR[0], edgecolor="#333333", label="Not identified in corpus"),
    ]
    ax.legend(handles=legend, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=4, frameon=False)

    figure_dir = RESULTS_DIR / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    png = figure_dir / "fig4_mechanism_service_matrix.png"
    svg = figure_dir / "fig4_mechanism_service_matrix.svg"
    fig.savefig(png, dpi=320, bbox_inches="tight", facecolor="white", metadata={"Software": "zhou-review-evidence-map"})
    fig.savefig(svg, bbox_inches="tight", facecolor="white", metadata={"Date": None, "Creator": "zhou-review-evidence-map"})
    plt.close(fig)
    caption = figure_dir / "fig4_caption.md"
    caption.write_text(
        "# Fig. 4 caption note\n\n"
        "Mechanism-service evidence identified within the included corpus. Cell labels show the evidence category "
        "(`D`, `M` or `I`) and the number of unique studies (`n`). Colour encodes the same ordered categories using "
        "distinct lightness, while printed codes preserve meaning in greyscale. The highest setting is displayed for "
        "each populated cell but does not characterize all evidence in that cell. A blank cell means that no eligible "
        "evidence was identified under this bounded protocol, not that the mechanism-service link is impossible. Source "
        "rows and locators are in `results/audit/fig4_source_ledger.csv`.\n",
        encoding="utf-8",
    )
    return png, svg
