#!/usr/bin/env python3

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from diagrams import Cluster, Diagram, Edge
from diagrams.custom import Custom


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "asset" / "reference" / "architecture"
ICON_DIR = Path("/tmp/euclid-diagram-icons")
ICON_DIR.mkdir(parents=True, exist_ok=True)


def load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/liberation-sans/LiberationSans-Bold.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def make_icon(filename: str, title: str, short: str, fill: str) -> str:
    path = ICON_DIR / filename
    if path.exists():
        return str(path)

    image = Image.new("RGBA", (256, 256), "white")
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((10, 10, 246, 246), radius=34, fill=fill, outline="#0f172a", width=6)
    draw.rounded_rectangle((26, 150, 230, 226), radius=18, fill="white")

    short_font = load_font(92)
    title_font = load_font(24)

    draw.text((128, 88), short, font=short_font, fill="white", anchor="mm")
    draw.text((128, 188), title, font=title_font, fill="#0f172a", anchor="mm")

    image.save(path)
    return str(path)


def node(label: str, filename: str, title: str, short: str, fill: str) -> Custom:
    return Custom(label, make_icon(filename, title, short, fill))


def main() -> None:
    graph_attr = {
        "bgcolor": "white",
        "pad": "0.4",
        "nodesep": "0.7",
        "ranksep": "0.8",
        "splines": "spline",
        "fontname": "Helvetica",
        "fontsize": "22",
        "labelloc": "t",
        "label": "Euclid Haskell Architecture",
    }
    node_attr = {
        "fontname": "Helvetica",
        "fontsize": "13",
    }
    edge_attr = {
        "color": "#334155",
        "penwidth": "1.8",
        "fontname": "Helvetica",
        "fontsize": "11",
    }

    with Diagram(
        "",
        filename=str(OUTPUT),
        outformat="png",
        show=False,
        direction="LR",
        graph_attr=graph_attr,
        node_attr=node_attr,
        edge_attr=edge_attr,
    ):
        with Cluster("Interfaces", graph_attr={"bgcolor": "#f8fafc", "color": "#cbd5e1"}):
            cli = node("CLI Entry\noptparse-applicative", "cli.png", "optparse", "CLI", "#2563eb")
            repl = node("REPL\ninteractive shell", "repl.png", "repl", "REPL", "#f59e0b")
            lsp = node("LSP Server\nAeson JSON-RPC", "lsp.png", "aeson", "LSP", "#059669")
            tui = node("Brick TUI\nBrick + Vty", "tui.png", "brick/vty", "TUI", "#7c3aed")

        with Cluster("Language Core", graph_attr={"bgcolor": "#f8fafc", "color": "#cbd5e1"}):
            parser = node("Parser\nMegaparsec", "parser.png", "megaparsec", "MP", "#0f766e")
            ast = node("AST\nEuclid.Lang.AST", "ast.png", "haskell", "AST", "#4c1d95")
            evaluator = node("Evaluator\nEuclid.Core.Eval", "eval.png", "haskell", "EVAL", "#5b21b6")
            world = node(
                "World Model\nTimelines / Entities /\nRelationships / Functions",
                "world.png",
                "haskell",
                "WORLD",
                "#1d4ed8",
            )
            validation = node("Validation\nDiagnostics", "validation.png", "diagnostics", "VAL", "#dc2626")
            diff = node("Semantic Diff\nWorld vs World", "diff.png", "diff", "DIFF", "#9333ea")

        with Cluster("Imports & Config", graph_attr={"bgcolor": "#f8fafc", "color": "#cbd5e1"}):
            csv = node("CSV Import", "csv.png", "csv", "CSV", "#ea580c")
            gedcom = node("GEDCOM Import", "gedcom.png", "gedcom", "GED", "#be185d")
            jsonld = node("JSON-LD Import\nAeson", "jsonld.png", "json-ld", "JSON", "#0891b2")
            config = node("Config Loader\nTomland", "config.png", "tomland", "TOML", "#16a34a")

        with Cluster("Rendering", graph_attr={"bgcolor": "#f8fafc", "color": "#cbd5e1"}):
            layout = node("Layout Engine", "layout.png", "layout", "LAY", "#2563eb")
            svg = node("SVG Renderer", "svg.png", "svg", "SVG", "#0ea5e9")

        cli >> Edge(label="load / run / check / export") >> parser
        repl >> Edge(label="parse statements") >> parser
        lsp >> Edge(label="diagnostics / hover") >> parser

        csv >> Edge(label="emit .euclid") >> parser
        gedcom >> Edge(label="emit .euclid") >> parser
        jsonld >> Edge(label="emit .euclid") >> parser

        parser >> ast >> evaluator >> world
        world >> validation
        world >> diff
        world >> layout >> svg
        world >> layout >> tui

        config >> Edge(label="theme / export defaults") >> cli
        config >> Edge(label="theme") >> svg
        validation >> Edge(label="reports") >> cli
        validation >> Edge(label="reports") >> repl
        validation >> Edge(label="reports") >> lsp


if __name__ == "__main__":
    main()
