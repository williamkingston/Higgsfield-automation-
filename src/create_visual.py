#!/usr/bin/env python3
"""Create a visual (image/video) from a Blotato template."""
import argparse
import json
from client import create_visual, list_visual_templates


def main():
    parser = argparse.ArgumentParser(description="Create a visual via Blotato")
    parser.add_argument("--prompt", required=True, help="Description of the visual to generate")
    parser.add_argument("--template-id", help="Template ID (fetches first available if omitted)")
    parser.add_argument(
        "--brand-instructions",
        default=(
            "Dark backgrounds, bold white or metallic typography, "
            "moody cinematic lighting, high contrast. "
            "Brand: Wrich Velvyt. Aesthetic: streetwear editorial."
        ),
        help="Brand style instructions appended to the prompt",
    )
    parser.add_argument("--no-render", action="store_true", help="Create as draft without rendering")
    args = parser.parse_args()

    template_id = args.template_id
    if not template_id:
        templates = list_visual_templates()
        items = templates if isinstance(templates, list) else templates.get("items", [])
        if not items:
            print("No visual templates found. Check your Blotato account.")
            return
        template_id = items[0].get("id") or items[0].get("templateId")
        print(f"Using template: {template_id}")

    full_prompt = f"{args.prompt}. Style: {args.brand_instructions}"

    result = create_visual(
        template_id=template_id,
        prompt=full_prompt,
        render=not args.no_render,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
