import os
import sys
import argparse
import traceback

import config
from cache import make_cache_root
from logger import ok, error
from notes_parser import parse_sermon_notes
from propresenter import load_pb2_from_procore, Pro7Compiler
from reader import read_input_text
from renderer import slide_items_to_render_slides


def load_dotenv(path):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def refresh_config_from_env():
    config.AI_PROVIDER = os.environ.get("AI_PROVIDER", config.AI_PROVIDER).lower()
    config.GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", config.GEMINI_API_KEY)
    config.GEMINI_MODEL = os.environ.get("GEMINI_MODEL", config.GEMINI_MODEL)
    config.OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", config.OPENROUTER_API_KEY)
    config.OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", config.OPENROUTER_MODEL)


def default_paths():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, ".."))
    
    # Try local ProCore first (self-contained), then fallback to parent directory ProCore
    procore = os.path.join(current_dir, "ProCore")
    if not os.path.exists(procore):
        procore = os.path.join(project_root, "ProCore")

    return (
        current_dir,
        project_root,
        procore,
        os.path.join(current_dir, "Matthew3.docx"),
        os.path.join(current_dir, "SermonScripture.pro"),
    )


def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        try:
            import sys
            enc = sys.stdout.encoding or "ascii"
            print(text.encode(enc, errors="replace").decode(enc))
        except Exception:
            print(text.encode("ascii", errors="replace").decode("ascii"))


def main():
    current_dir, project_root, default_procore, default_input, default_output = default_paths()
    load_dotenv(os.path.join(current_dir, ".env"))
    refresh_config_from_env()

    parser = argparse.ArgumentParser(description="Generate ProPresenter sermon slides.")
    parser.add_argument("--input", default=default_input)
    parser.add_argument("--output", default=default_output)
    parser.add_argument("--procore", default=default_procore)
    parser.add_argument("--translation", default=None)
    parser.add_argument("--provider", default=config.AI_PROVIDER, choices=["gemini", "openrouter"])
    parser.add_argument("--gemini-model", default=config.GEMINI_MODEL)
    parser.add_argument("--ai-model", default=config.OPENROUTER_MODEL)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--use-ai", action="store_true", help="Use AI splitter. Manual curated splitter is default.")
    parser.add_argument("--no-ai", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--location", default="midtown", choices=["midtown", "downtown"], help="Select location theme: midtown or downtown.")
    parser.add_argument("--json-out", default=None, help="Path to write JSON metadata report.")
    args = parser.parse_args()

    config.set_location_theme(args.location)

    config.AI_PROVIDER = args.provider
    config.GEMINI_MODEL = args.gemini_model

    if args.api_key:
        if config.AI_PROVIDER == "gemini":
            config.GEMINI_API_KEY = args.api_key
        else:
            config.OPENROUTER_API_KEY = args.api_key

    # Default is curated manual splitter. AI is opt-in now.
    config.USE_AI_SPLITTER = bool(args.use_ai)
    config.USE_AI_PARSER = bool(args.use_ai)
    if args.no_ai:
        config.USE_AI_SPLITTER = False
        config.USE_AI_PARSER = False

    input_path = os.path.abspath(args.input)
    output_path = os.path.abspath(args.output)
    procore_path = os.path.abspath(args.procore)
    cache_root = make_cache_root(current_dir)

    try:
        load_pb2_from_procore(procore_path)
        ok("Protobuf module loaded successfully.")
    except Exception as e:
        error(f"Could not load protobuf module: {e}")
        print(f"Expected ProCore location:\n{procore_path}")
        raise SystemExit(1)

    print(f"Location Theme: {config.SELECTED_LOCATION.upper()}")
    print(f"Input Path: {input_path}")
    print(f"ProCore/PB2 Path: {procore_path}")
    print(f"Output Path: {output_path}")
    print(f"Cache Path: {cache_root}")
    print(f"Bible translation override: {args.translation or '(use notes/default)'}")
    print(f"Splitter: {'AI ' + config.AI_PROVIDER if config.USE_AI_SPLITTER else 'curated manual'}")
    print(f"Notes Parser: {'AI ' + config.AI_PROVIDER if config.USE_AI_PARSER else 'heuristics'}")
    print(f"Gemini model: {config.GEMINI_MODEL}")
    print(f"OpenRouter model: {args.ai_model}")
    print(f"AI timeout: {config.AI_TIMEOUT_SECONDS}s, retries: {config.AI_MAX_RETRIES}")

    if not os.path.exists(input_path):
        error(f"Input file not found: {input_path}")
        raise SystemExit(1)

    try:
        raw_text = read_input_text(input_path)
        items = parse_sermon_notes(
            raw_text,
            cache_root=cache_root,
            translation_override=args.translation,
            ai_model=(config.GEMINI_MODEL if config.AI_PROVIDER == "gemini" else args.ai_model),
            debug=args.debug,
        )

        slides = slide_items_to_render_slides(
            items,
            cache_root,
            args.translation,
            (config.GEMINI_MODEL if config.AI_PROVIDER == "gemini" else args.ai_model),
            args.debug,
        )

        print(f"\nParsed {len(items)} sermon items.")
        for item in items:
            safe_print(f"- {item.kind.upper()}: {item.reference or item.text} {item.translation or ''}")

        print(f"\nGenerated {len(slides)} slides.\n")
        for i, slide in enumerate(slides, 1):
            safe_print(f"Slide {i} [{slide.kind.upper()}] {slide.name}")
            safe_print(slide.body[:300])
            print()

        presentation = Pro7Compiler.build_presentation(slides)

        with open(output_path, "wb") as f:
            f.write(presentation.SerializeToString())

        print(f"SUCCESS! File written to:\n{output_path}")

        # Write JSON metadata report if requested
        if args.json_out:
            import json
            report = {
                "location": config.SELECTED_LOCATION,
                "input_path": input_path,
                "output_path": output_path,
                "items": [
                    {
                        "kind": item.kind,
                        "text": item.text,
                        "reference": item.reference,
                        "translation": item.translation,
                        "point_number": item.point_number
                    }
                    for item in items
                ],
                "slides": [
                    {
                        "kind": slide.kind,
                        "name": slide.name,
                        "body": slide.body,
                        "label": slide.label,
                        "point_number": slide.point_number
                    }
                    for slide in slides
                ],
                "media_notes": [
                    {
                        "kind": item.kind,
                        "text": item.text,
                        "reference": item.reference,
                        "translation": item.translation,
                        "point_number": item.point_number
                    }
                    for item in items if item.kind == "media_note"
                ]
            }
            with open(os.path.abspath(args.json_out), "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"JSON report written to:\n{args.json_out}")

        # Extract and print media notes/graphics/tables report
        media_notes = [item for item in items if item.kind == "media_note"]
        if media_notes:
            print("\n" + "=" * 60)
            print("DETECTED MEDIA, GRAPHICS, AND SIDE NOTES FOR USER:")
            print("=" * 60)
            for note in media_notes:
                lines = note.text.splitlines()
                safe_print(f"- {lines[0]}")
                for line in lines[1:]:
                    safe_print(f"  {line}")
            print("=" * 60 + "\n")

    except Exception:
        error("Error encountered:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
