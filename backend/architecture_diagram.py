"""
Compliance Policy AI - Architecture Diagram
Run this script to generate the architecture diagram as a PNG image.
Requires: pip install matplotlib

Usage: python architecture_diagram.py
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def draw_architecture():
    fig, ax = plt.subplots(1, 1, figsize=(16, 10))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.set_facecolor("#f8f9fa")
    fig.patch.set_facecolor("#f8f9fa")

    # Title
    ax.text(8, 9.5, "Compliance Policy AI - RAG Architecture",
            fontsize=18, fontweight="bold", ha="center", va="center",
            color="#1a1a2e")

    # =========== INGESTION PIPELINE (Top Row) ===========
    ax.text(8, 8.7, "DOCUMENT INGESTION PIPELINE", fontsize=10,
            fontweight="bold", ha="center", color="#e63946", style="italic")

    # Box 1: Documents
    doc_box = mpatches.FancyBboxPatch((0.5, 7.5), 2.5, 1, boxstyle="round,pad=0.15",
                                       facecolor="#457b9d", edgecolor="#1d3557", linewidth=2)
    ax.add_patch(doc_box)
    ax.text(1.75, 8.15, "GDPR / HIPAA", fontsize=9, fontweight="bold", ha="center", color="white")
    ax.text(1.75, 7.85, "Documents", fontsize=8, ha="center", color="#a8dadc")
    ax.text(1.75, 7.6, "(PDF / TXT)", fontsize=7, ha="center", color="#a8dadc")

    # Arrow 1
    ax.annotate("", xy=(3.8, 8), xytext=(3.1, 8),
                arrowprops=dict(arrowstyle="->", color="#e63946", lw=2))

    # Box 2: Chunking
    chunk_box = mpatches.FancyBboxPatch((3.8, 7.5), 2.5, 1, boxstyle="round,pad=0.15",
                                         facecolor="#457b9d", edgecolor="#1d3557", linewidth=2)
    ax.add_patch(chunk_box)
    ax.text(5.05, 8.15, "Sentence Splitter", fontsize=9, fontweight="bold", ha="center", color="white")
    ax.text(5.05, 7.85, "Chunking", fontsize=8, ha="center", color="#a8dadc")
    ax.text(5.05, 7.6, "(512 tokens)", fontsize=7, ha="center", color="#a8dadc")

    # Arrow 2
    ax.annotate("", xy=(7.1, 8), xytext=(6.4, 8),
                arrowprops=dict(arrowstyle="->", color="#e63946", lw=2))

    # Box 3: Embeddings
    embed_box = mpatches.FancyBboxPatch((7.1, 7.5), 2.5, 1, boxstyle="round,pad=0.15",
                                         facecolor="#e76f51", edgecolor="#c4452d", linewidth=2)
    ax.add_patch(embed_box)
    ax.text(8.35, 8.15, "OpenAI", fontsize=9, fontweight="bold", ha="center", color="white")
    ax.text(8.35, 7.85, "Embeddings", fontsize=8, ha="center", color="#fce4d6")
    ax.text(8.35, 7.6, "(ada-002)", fontsize=7, ha="center", color="#fce4d6")

    # Arrow 3
    ax.annotate("", xy=(10.4, 8), xytext=(9.7, 8),
                arrowprops=dict(arrowstyle="->", color="#e63946", lw=2))

    # Box 4: ChromaDB
    chroma_box = mpatches.FancyBboxPatch((10.4, 7.5), 2.5, 1, boxstyle="round,pad=0.15",
                                          facecolor="#2a9d8f", edgecolor="#1a6b5f", linewidth=2)
    ax.add_patch(chroma_box)
    ax.text(11.65, 8.15, "ChromaDB", fontsize=9, fontweight="bold", ha="center", color="white")
    ax.text(11.65, 7.85, "Vector Store", fontsize=8, ha="center", color="#d4f0eb")
    ax.text(11.65, 7.6, "(Persistent)", fontsize=7, ha="center", color="#d4f0eb")

    # =========== QUERY PIPELINE (Bottom Section) ===========
    ax.text(8, 6.2, "QUERY PIPELINE (RAG)", fontsize=10,
            fontweight="bold", ha="center", color="#2a9d8f", style="italic")

    # User Query
    user_box = mpatches.FancyBboxPatch((0.5, 4.2), 2.5, 1.2, boxstyle="round,pad=0.15",
                                        facecolor="#264653", edgecolor="#1a1a2e", linewidth=2)
    ax.add_patch(user_box)
    ax.text(1.75, 5.0, "User Query", fontsize=9, fontweight="bold", ha="center", color="white")
    ax.text(1.75, 4.65, "POST /ask", fontsize=8, ha="center", color="#a8dadc")
    ax.text(1.75, 4.35, '{"question": "..."}', fontsize=7, ha="center", color="#a8dadc")

    # Arrow to FastAPI
    ax.annotate("", xy=(3.8, 4.8), xytext=(3.1, 4.8),
                arrowprops=dict(arrowstyle="->", color="#2a9d8f", lw=2))

    # FastAPI
    api_box = mpatches.FancyBboxPatch((3.8, 4.2), 2.5, 1.2, boxstyle="round,pad=0.15",
                                       facecolor="#457b9d", edgecolor="#1d3557", linewidth=2)
    ax.add_patch(api_box)
    ax.text(5.05, 5.0, "FastAPI", fontsize=9, fontweight="bold", ha="center", color="white")
    ax.text(5.05, 4.65, "Backend Server", fontsize=8, ha="center", color="#a8dadc")
    ax.text(5.05, 4.35, "(uvicorn)", fontsize=7, ha="center", color="#a8dadc")

    # Arrow to Embed Query
    ax.annotate("", xy=(7.1, 4.8), xytext=(6.4, 4.8),
                arrowprops=dict(arrowstyle="->", color="#2a9d8f", lw=2))

    # Embed Query
    eq_box = mpatches.FancyBboxPatch((7.1, 4.2), 2.5, 1.2, boxstyle="round,pad=0.15",
                                      facecolor="#e76f51", edgecolor="#c4452d", linewidth=2)
    ax.add_patch(eq_box)
    ax.text(8.35, 5.0, "Embed Query", fontsize=9, fontweight="bold", ha="center", color="white")
    ax.text(8.35, 4.65, "OpenAI", fontsize=8, ha="center", color="#fce4d6")
    ax.text(8.35, 4.35, "(ada-002)", fontsize=7, ha="center", color="#fce4d6")

    # Arrow to Vector Search
    ax.annotate("", xy=(10.4, 4.8), xytext=(9.7, 4.8),
                arrowprops=dict(arrowstyle="->", color="#2a9d8f", lw=2))

    # Vector Search
    vs_box = mpatches.FancyBboxPatch((10.4, 4.2), 2.5, 1.2, boxstyle="round,pad=0.15",
                                      facecolor="#2a9d8f", edgecolor="#1a6b5f", linewidth=2)
    ax.add_patch(vs_box)
    ax.text(11.65, 5.0, "Vector Search", fontsize=9, fontweight="bold", ha="center", color="white")
    ax.text(11.65, 4.65, "ChromaDB", fontsize=8, ha="center", color="#d4f0eb")
    ax.text(11.65, 4.35, "(Top-K=5)", fontsize=7, ha="center", color="#d4f0eb")

    # Arrow down from Vector Search to LLM
    ax.annotate("", xy=(11.65, 3.4), xytext=(11.65, 4.1),
                arrowprops=dict(arrowstyle="->", color="#2a9d8f", lw=2))
    ax.text(12.3, 3.75, "relevant\nchunks", fontsize=7, ha="center", color="#555", style="italic")

    # LLM Box
    llm_box = mpatches.FancyBboxPatch((7.1, 2.2), 5.8, 1.1, boxstyle="round,pad=0.15",
                                       facecolor="#e76f51", edgecolor="#c4452d", linewidth=2)
    ax.add_patch(llm_box)
    ax.text(10, 2.95, "LLM - OpenAI GPT-3.5-Turbo", fontsize=10, fontweight="bold", ha="center", color="white")
    ax.text(10, 2.55, "Generates answer grounded in retrieved regulation chunks",
            fontsize=8, ha="center", color="#fce4d6")

    # Arrow from LLM back to Response
    ax.annotate("", xy=(6.4, 2.75), xytext=(7.0, 2.75),
                arrowprops=dict(arrowstyle="->", color="#e63946", lw=2))

    # Response Box
    resp_box = mpatches.FancyBboxPatch((3.8, 2.2), 2.5, 1.1, boxstyle="round,pad=0.15",
                                        facecolor="#264653", edgecolor="#1a1a2e", linewidth=2)
    ax.add_patch(resp_box)
    ax.text(5.05, 2.95, "JSON Response", fontsize=9, fontweight="bold", ha="center", color="white")
    ax.text(5.05, 2.55, "answer + sources", fontsize=8, ha="center", color="#a8dadc")

    # Arrow from Response to User
    ax.annotate("", xy=(3.1, 2.75), xytext=(3.7, 2.75),
                arrowprops=dict(arrowstyle="->", color="#e63946", lw=2))

    # User Response
    ur_box = mpatches.FancyBboxPatch((0.5, 2.2), 2.5, 1.1, boxstyle="round,pad=0.15",
                                      facecolor="#264653", edgecolor="#1a1a2e", linewidth=2)
    ax.add_patch(ur_box)
    ax.text(1.75, 2.95, "User", fontsize=9, fontweight="bold", ha="center", color="white")
    ax.text(1.75, 2.55, "Gets cited answer", fontsize=8, ha="center", color="#a8dadc")

    # =========== TECH STACK LEGEND ===========
    ax.text(14.5, 5.8, "Tech Stack", fontsize=10, fontweight="bold", ha="center", color="#1a1a2e")

    legend_items = [
        ("#457b9d", "Python / FastAPI"),
        ("#e76f51", "OpenAI API"),
        ("#2a9d8f", "ChromaDB"),
        ("#264653", "LlamaIndex"),
    ]
    for i, (color, label) in enumerate(legend_items):
        y = 5.3 - i * 0.4
        rect = mpatches.FancyBboxPatch((13.5, y - 0.1), 0.3, 0.2,
                                        boxstyle="round,pad=0.05",
                                        facecolor=color, edgecolor="none")
        ax.add_patch(rect)
        ax.text(14.0, y, label, fontsize=8, va="center", color="#333")

    # Dotted line separator
    ax.plot([0.3, 15.7], [6.8, 6.8], linestyle="--", color="#ccc", lw=1)

    # Footer
    ax.text(8, 1.5, "scripts/ingest.py → Ingestion Pipeline  |  main.py → Query Pipeline",
            fontsize=8, ha="center", color="#888", style="italic")

    plt.tight_layout()
    plt.savefig("architecture.png", dpi=150, bbox_inches="tight", facecolor="#f8f9fa")
    print("Saved: architecture.png")
    plt.show()


if __name__ == "__main__":
    draw_architecture()
