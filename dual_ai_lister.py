import os
import json
import base64

from dotenv import load_dotenv
from anthropic import Anthropic
from openai import OpenAI

# Load .env with keys
load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not ANTHROPIC_API_KEY:
    raise RuntimeError("Missing ANTHROPIC_API_KEY in .env")
if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY in .env")

anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

CLAUDE_MODEL = "claude-3-5-sonnet-latest"
GPT_MODEL = "gpt-4.1-mini"


# -------------------- UTILITIES --------------------

def encode_image_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def safe_json_load(text: str):
    """
    Try to parse JSON; if it fails, wrap raw text for debugging.
    """
    try:
        return json.loads(text)
    except Exception:
        return {"error": "invalid_json", "raw_text": text}


def pretty_print_listing(listing: dict):
    """
    Print a human-readable listing for quick copy/paste to Mercari.
    """
    print("\n" + "=" * 60)
    print("FINAL LISTING")
    print("=" * 60)

    print(f"\nTitle:\n  {listing.get('title')}")
    print("\nDescription:\n")
    print(listing.get("description", ""))

    print("\nDetails:")
    print(f"  Identified Item : {listing.get('identified_name')}")
    print(f"  Brand           : {listing.get('brand')}")
    print(f"  Model           : {listing.get('model')}")
    print(f"  Category        : {listing.get('category')}")
    print(f"  Condition       : {listing.get('condition')}")

    price_low = listing.get("price_low")
    price_high = listing.get("price_high")
    if price_low or price_high:
        print(f"  Suggested Price : ${price_low or '?'} - ${price_high or '?'}")

    features = listing.get("features") or []
    defects = listing.get("defects") or []
    keywords = listing.get("keywords") or []

    if features:
        print("\nFeatures:")
        for f in features:
            print(f"  - {f}")

    if defects:
        print("\nDefects / Notes:")
        for d in defects:
            print(f"  - {d}")

    if keywords:
        print("\nTags / Keywords:")
        print("  " + ", ".join(keywords))

    print("\n" + "=" * 60 + "\n")


def sanitize_filename(name: str) -> str:
    """
    Make a safe filename from an item name.
    """
    name = name.strip().lower()
    bad_chars = '<>:"/\\|?*'
    for c in bad_chars:
        name = name.replace(c, "_")
    name = "_".join(name.split())
    if not name:
        name = "listing"
    return name[:50]


# -------------------- CLAUDE ANALYSIS --------------------

def analyze_with_claude(image_path: str, user_hint: str = "") -> dict:
    """
    Claude identifies the item from the image and returns structured JSON.
    """
    img_b64 = encode_image_b64(image_path)

    system_prompt = """
You are an expert at identifying items from photos for online marketplaces.

Return JSON ONLY in the exact format below (no extra text):

{
  "identified_name": string,         // what you think the item is (e.g. "HP 15-f004wm laptop")
  "brand": string | null,            // visible brand, or null if unknown
  "model": string | null,            // visible model/series, or null if unknown
  "category": string | null,         // broad category like "Laptop", "Headphones", "Graphics Card"
  "condition_estimate": string | null, // short phrase like "Used - Good", "Used - Fair", "For parts"
  "notable_features": string[],      // visible important features, ports, buttons, labels
  "visible_defects": string[],       // visible damage, scratches, missing parts
  "price_low": number | null,        // rough low-end resale estimate in USD
  "price_high": number | null,       // rough high-end resale estimate in USD
  "description_notes": string        // raw notes you would use to help write a listing
}

If you are unsure about ANY field, set it to null or [] rather than guessing.
Never invent exact model numbers or capacities that are not clearly visible.
"""

    message = anthropic_client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1100,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": img_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            f"User hint (may be empty): {user_hint}\n\n"
                            "Identify this item and respond ONLY with the JSON described."
                        ),
                    },
                ],
            }
        ],
    )

    text = message.content[0].text if message.content else "{}"
    return safe_json_load(text)


# -------------------- GPT SECOND OPINION --------------------

def analyze_with_gpt(claude_json: dict, user_hint: str = "") -> dict:
    """
    GPT looks at Claude's JSON + your hint and:
    - Confirms or denies Claude's identified_name as a sane item
    - Produces a final refined JSON listing structure
    NOTE: This version uses only text (no image) to keep setup simple.
    """

    system_prompt = """
You are an expert marketplace listing assistant.

You will receive:
- A tentative item name and details from Claude (another AI)
- An optional hint from the human seller

Your tasks:
1. Check whether Claude's identified_name looks like a real, plausible product.
2. If it looks wrong or impossible, correct it based on the rest of the data.
3. Build a clean, buyer-friendly listing.

Return JSON ONLY in this exact format:

{
  "verification_question": string,       // e.g. "Is this a HP 15-f004wm laptop?"
  "verification_answer": "Yes" | "No",   // whether you think Claude's identified_name is correct
  "final_identified_name": string,       // your best final name for what the product actually is
  "brand": string | null,
  "model": string | null,
  "category": string | null,
  "condition": string | null,            // short condition label
  "features": string[],                  // bullet points of features/specs
  "defects": string[],                   // bullet points of issues/defects
  "keywords": string[],                  // search keywords/tags
  "price_low": number | null,           // suggested low-end resale price in USD
  "price_high": number | null,          // suggested high-end resale price in USD
  "final_title": string,                // ready-to-post listing title
  "final_description": string           // ready-to-post full description
}

If you are unsure about exact numbers, keep them null or generic, do NOT hallucinate specifics.
"""

    claude_str = json.dumps(claude_json, indent=2, ensure_ascii=False)

    user_content = (
        f"Human hint (may be empty): {user_hint}\n\n"
        f"Claude's JSON:\n{claude_str}\n\n"
        "Now perform your tasks and return ONLY the JSON described."
    )

    resp = openai_client.chat.completions.create(
        model=GPT_MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )

    text = resp.choices[0].message.content
    return safe_json_load(text)


# -------------------- MERGING LOGIC --------------------

def merge_results(claude_json: dict, gpt_json: dict, override_name: str = None) -> dict:
    """
    Merge Claude + GPT into a final listing.
    - GPT decides if Claude's product ID is plausible.
    - You can override the final name manually (override_name).
    - Claude trusted more for raw visual details.
    - GPT trusted more for final wording.
    """

    final = {}

    # Verification info from GPT
    final["verification_question"] = gpt_json.get("verification_question", "")
    final["verification_answer"] = gpt_json.get("verification_answer", "")

    # Decide on the final identified name
    if override_name:
        final["identified_name"] = override_name
    else:
        if gpt_json.get("verification_answer") == "No":
            final["identified_name"] = gpt_json.get("final_identified_name") or claude_json.get("identified_name")
        else:
            # if Yes or unknown, prefer Claude's specific name if it exists
            final["identified_name"] = claude_json.get("identified_name") or gpt_json.get("final_identified_name")

    # Brand / model / category (prefer Claude, fallback GPT)
    for field in ["brand", "model", "category"]:
        final[field] = claude_json.get(field) or gpt_json.get(field)

    # Condition
    final["condition"] = claude_json.get("condition_estimate") or gpt_json.get("condition")

    # Features and defects combined
    final["features"] = (claude_json.get("notable_features") or []) + (gpt_json.get("features") or [])
    final["defects"] = (claude_json.get("visible_defects") or []) + (gpt_json.get("defects") or [])

    # Keywords (GPT)
    final["keywords"] = gpt_json.get("keywords") or []

    # Pricing: GPT first, Claude backup
    final["price_low"] = gpt_json.get("price_low") or claude_json.get("price_low")
    final["price_high"] = gpt_json.get("price_high") or claude_json.get("price_high")

    # Final title & description from GPT
    final["title"] = gpt_json.get("final_title") or final["identified_name"]
    final["description"] = gpt_json.get("final_description") or (claude_json.get("description_notes") or "")

    return final


# -------------------- INTERACTIVE LOOP --------------------

def interactive_loop():
    print("=" * 60)
    print("DUAL-AI LISTING ASSISTANT (Claude + GPT)")
    print("No flags. Just answer questions. Type 'q' to quit at any prompt.")
    print("=" * 60)

    while True:
        image_path = input("\nEnter image path for the item (or 'q' to quit):\n> ").strip().strip('"')
        if image_path.lower() in ("q", "quit", "exit"):
            break

        if not os.path.isfile(image_path):
            print("⚠ File not found. Check the path and try again.")
            continue

        user_hint = input(
            "\nOptional: What do YOU think this is? (brand, model, or a quick description).\n"
            "Press Enter to skip if you're not sure:\n> "
        ).strip()
        if user_hint.lower() in ("q", "quit", "exit"):
            break

        print("\n📸 Sending to Claude to analyze the photo...")
        claude_result = analyze_with_claude(image_path, user_hint)
        print("✅ Claude responded.")

        print("\n🤖 Sending Claude's result to GPT for second opinion and listing generation...")
        gpt_result = analyze_with_gpt(claude_result, user_hint)
        print("✅ GPT responded.")

        # Show quick summary
        claude_name = claude_result.get("identified_name")
        gpt_name = gpt_result.get("final_identified_name")
        vq = gpt_result.get("verification_question")
        va = gpt_result.get("verification_answer")

        print("\n--- AI IDENTIFICATION SUMMARY ---")
        print(f"Claude thinks this is: {claude_name}")
        print(f"GPT thinks this is:    {gpt_name}")
        if vq:
            print(f"GPT verification:      {vq}  -> {va}")
        print("---------------------------------")

        # Let you confirm / correct the product name
        override_name = None
        while True:
            answer = input(
                "\nDoes this match what you're selling?\n"
                "[y]es / [n]o, it's wrong / [e]dit name / [s]how raw AI JSON\n> "
            ).strip().lower()

            if answer in ("q", "quit", "exit"):
                return

            if answer in ("s", "show"):
                print("\n--- Claude RAW JSON ---")
                print(json.dumps(claude_result, indent=2, ensure_ascii=False))
                print("\n--- GPT RAW JSON ---")
                print(json.dumps(gpt_result, indent=2, ensure_ascii=False))
                continue

            if answer in ("y", "yes"):
                # No override, use AI consensus
                break

            if answer in ("n", "no", "e", "edit"):
                override_name = input("Type the correct name for this item:\n> ").strip()
                if override_name.lower() in ("q", "quit", "exit"):
                    return
                break

            print("Please choose y/n/e/s (or 'q' to quit).")

        # Merge everything
        final_listing = merge_results(claude_result, gpt_result, override_name)

        # Show final listing nicely
        pretty_print_listing(final_listing)

        # Optionally save to JSON
        save_choice = input("Save this listing to a JSON file? [y/N]\n> ").strip().lower()
        if save_choice == "y":
            base_name = sanitize_filename(final_listing.get("identified_name") or "listing")
            out_path = os.path.join(os.getcwd(), base_name + ".json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(final_listing, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved to: {out_path}")

        # Ask if you want to do another item
        again = input("\nDo you want to list another item? [Y/n]\n> ").strip().lower()
        if again in ("n", "no"):
            break


if __name__ == "__main__":
    interactive_loop()
